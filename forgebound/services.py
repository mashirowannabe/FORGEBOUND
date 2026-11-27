import json
from datetime import datetime, timezone

from .database import get_client
from .patterns.builder import OrderBuilder
from .patterns.observers import CustomerObserver, OrderSubject
from .patterns.pricing import calculate_price
from .patterns.products import get_product_factory
from .patterns.states import ProductionOrder


def store_notification(user_id, order_id, message):
    get_client().table("notifications").insert({
        "user_id": user_id,
        "order_id": order_id,
        "title": "Pembaruan pesanan",
        "message": message,
    }).execute()


def notify_customer(customer_id, order_id, message):
    subject = OrderSubject()
    subject.attach(CustomerObserver(customer_id, order_id, store_notification))
    subject.notify(message)


class OrderFacade:
    """Coordinates Factory Method, Builder, Decorator, and Observer."""

    def create_order(self, customer_id, product_code, length_cm, material, motif, handle_type, services):
        product = get_product_factory(product_code).create_product()
        order = (
            OrderBuilder().customer(customer_id).product(product)
            .specifications(length_cm, material, motif, handle_type)
            .services(services).build()
        )
        priced = calculate_price(order.base_price, order.services)
        client = get_client()
        product_row = (
            client.table("products").select("id, name, base_price")
            .eq("name", order.product_name).eq("is_active", True).single().execute().data
        )
        order_code = "FB-" + datetime.now(timezone.utc).strftime("%y%m%d%H%M%S%f")
        order_row = client.table("orders").insert({
            "customer_id": customer_id,
            "order_code": order_code,
            "status": "Diterima",
            "notes": f"Panjang: {length_cm} cm | Motif: {motif} | Gagang: {handle_type}",
            "subtotal": order.base_price,
            "customization_fee": priced.total() - order.base_price,
            "total_amount": priced.total(),
        }).execute().data[0]
        client.table("order_items").insert({
            "order_id": order_row["id"],
            "product_id": product_row["id"],
            "product_name": order.product_name,
            "material": material,
            "specifications": {
                "length_cm": length_cm, "motif": motif,
                "handle_type": handle_type, "services": order.services,
            },
            "quantity": 1,
            "unit_price": order.base_price,
            "line_total": priced.total(),
        }).execute()
        notify_customer(customer_id, order_row["id"],
            f"Pesanan {order_code} berhasil dibuat. Status: Diterima.")
        return order_code, priced.total()


def _get_order(order_id):
    return (
        get_client().table("orders").select("*")
        .eq("id", order_id).single().execute().data
    )


def advance_order(order_id):
    try:
        client = get_client()
        row = _get_order(order_id)
        production = ProductionOrder(row["status"])
        production.next_stage()
        client.table("orders").update({"status": production.status}).eq("id", order_id).execute()
        client.table("production_history").insert({
            "order_id": order_id, "previous_status": row["status"],
            "new_status": production.status, "note": "Tahap produksi diperbarui.",
        }).execute()
        notify_customer(row["customer_id"], order_id,
            f"Pesanan {row['order_code']} sekarang berada pada tahap {production.status}.")
        return True, "Status pesanan diperbarui menjadi " + production.status + "."
    except Exception as exc:
        return False, str(exc)


def cancel_order(order_id):
    try:
        client = get_client()
        row = _get_order(order_id)
        production = ProductionOrder(row["status"])
        production.cancel()
        client.table("orders").update({"status": production.status}).eq("id", order_id).execute()
        client.table("production_history").insert({
            "order_id": order_id, "previous_status": row["status"],
            "new_status": production.status, "note": "Pesanan dibatalkan.",
        }).execute()
        notify_customer(row["customer_id"], order_id,
            f"Pesanan {row['order_code']} telah dibatalkan.")
        return True, "Pesanan berhasil dibatalkan."
    except Exception as exc:
        return False, str(exc)


def get_customer_orders(customer_id):
    rows = (
        get_client().table("orders").select("*, order_items(*)")
        .eq("customer_id", customer_id).order("created_at", desc=True).execute().data
    )
    return [_format_order(row) for row in rows]


def get_all_orders():
    rows = (
        get_client().table("orders")
        .select("*, profiles!orders_customer_id_fkey(full_name), order_items(*)")
        .order("created_at", desc=True).execute().data
    )
    result = []
    for row in rows:
        profile = row.get("profiles") or {}
        row["customer_name"] = profile.get("full_name", "Pelanggan")
        result.append(_format_order(row))
    return result


def _format_order(row):
    item = (row.get("order_items") or [{}])[0]
    specs = item.get("specifications") or {}
    row["product_name"] = item.get("product_name", "Produk")
    row["total_price"] = row.get("total_amount", 0)
    row["id"] = row["id"]
    return row


def get_notifications(user_id):
    rows = (
        get_client().table("notifications")
        .select("*, orders(order_code)")
        .eq("user_id", user_id).order("created_at", desc=True).execute().data
    )
    for row in rows:
        row["order_code"] = (row.get("orders") or {}).get("order_code", "-")
    unread = [row["id"] for row in rows if not row["is_read"]]
    if unread:
        get_client().table("notifications").update({"is_read": True}).in_("id", unread).execute()
    return rows


def get_products():
    rows = (
        get_client().table("products").select("*")
        .eq("is_active", True).order("name").execute().data
    )
    code_by_name = {"Golok": "GLK-001", "Cangkul": "CGL-001", "Pagar Tempa": "PGT-001"}
    for row in rows:
        row["code"] = code_by_name.get(row["name"], row["id"][:8].upper())
        row["base_price"] = float(row["base_price"])
        row["description"] = row.get("description") or ""
    return rows
