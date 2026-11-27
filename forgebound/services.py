import json
from datetime import datetime

from .database import get_connection
from .patterns.builder import OrderBuilder
from .patterns.observers import CustomerObserver, OrderSubject
from .patterns.pricing import calculate_price
from .patterns.products import get_product_factory
from .patterns.states import ProductionOrder


def store_notification(user_id, order_id, message):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO notifications (user_id, order_id, message) VALUES (?, ?, ?)",
            (user_id, order_id, message),
        )


def notify_customer(customer_id, order_id, message):
    subject = OrderSubject()
    subject.attach(CustomerObserver(customer_id, order_id, store_notification))
    subject.notify(message)


class OrderFacade:
    """Coordinates Factory Method, Builder, Decorator, and Observer."""

    def create_order(
        self, customer_id, product_code, length_cm, material,
        motif, handle_type, services,
    ):
        product = get_product_factory(product_code).create_product()
        order = (
            OrderBuilder()
            .customer(customer_id)
            .product(product)
            .specifications(length_cm, material, motif, handle_type)
            .services(services)
            .build()
        )
        final_price = calculate_price(order.base_price, order.services)
        order_code = "FB-" + datetime.now().strftime("%y%m%d%H%M%S%f")

        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO orders (
                    order_code, customer_id, product_code, product_name,
                    length_cm, material, motif, handle_type, base_price,
                    extra_services, total_price, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Diterima')""",
                (
                    order_code, order.customer_id, order.product_code,
                    order.product_name, order.length_cm, order.material,
                    order.motif, order.handle_type, order.base_price,
                    json.dumps(order.services, ensure_ascii=False),
                    final_price.total(),
                ),
            )
            order_id = cursor.lastrowid

        notify_customer(
            customer_id, order_id,
            "Pesanan " + order_code + " berhasil dibuat. Status: Diterima.",
        )
        return order_code, final_price.total()


def advance_order(order_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            return False, "Pesanan tidak ditemukan."
        production = ProductionOrder(row["status"])
        try:
            production.next_stage()
        except ValueError as exc:
            return False, str(exc)
        conn.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (production.status, order_id),
        )
        customer_id = row["customer_id"]
        order_code = row["order_code"]
        status = production.status

    notify_customer(
        customer_id, order_id,
        "Pesanan " + order_code + " sekarang berada pada tahap " + status + ".",
    )
    return True, "Status pesanan diperbarui menjadi " + status + "."


def cancel_order(order_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            return False, "Pesanan tidak ditemukan."
        production = ProductionOrder(row["status"])
        try:
            production.cancel()
        except ValueError as exc:
            return False, str(exc)
        conn.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (production.status, order_id),
        )
        customer_id = row["customer_id"]
        order_code = row["order_code"]

    notify_customer(
        customer_id, order_id,
        "Pesanan " + order_code + " telah dibatalkan.",
    )
    return True, "Pesanan berhasil dibatalkan."


def get_customer_orders(customer_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        ).fetchall()


def get_all_orders():
    with get_connection() as conn:
        return conn.execute(
            """SELECT o.*, u.full_name AS customer_name
               FROM orders o JOIN users u ON u.id = o.customer_id
               ORDER BY o.created_at DESC"""
        ).fetchall()


def get_notifications(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT n.*, o.order_code FROM notifications n
               JOIN orders o ON o.id = n.order_id
               WHERE n.user_id = ? ORDER BY n.created_at DESC""",
            (user_id,),
        ).fetchall()
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,)
        )
        return rows


def get_products():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE active = 1 ORDER BY id"
        ).fetchall()
