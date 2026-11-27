import getpass

from .database import authenticate, change_password, create_customer, sign_out
from .services import (
    OrderFacade, advance_order, cancel_order, get_all_orders,
    get_customer_orders, get_notifications, get_products,
)


def money(amount):
    return "Rp" + f"{amount:,.0f}".replace(",", ".")


def banner():
    print("\n" + "=" * 62)
    print("                         FORGEBOUND")
    print("             METAL PRODUCTION & CUSTOM ORDER SYSTEM")
    print("                         Version 0.1")
    print("=" * 62)
def pause():
    input("\nTekan ENTER untuk melanjutkan...")


def required_input(label):
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Input tidak boleh kosong.")


def read_secret(label):
    try:
        return getpass.getpass(label)
    except (EOFError, KeyboardInterrupt):
        return ""


def register():
    print("\n=== CUSTOMER REGISTRATION ===")
    name = required_input("Nama lengkap : ")
    email = required_input("Email        : ")
    password = read_secret("Password     : ")
    if len(password) < 8:
        print("Password minimal 8 karakter.")
        return
    confirmation = read_secret("Ulangi       : ")
    if password != confirmation:
        print("Konfirmasi password tidak cocok.")
        return
    ok, message = create_customer(name, "", email, password)
    print(("[SUCCESS] " if ok else "[ERROR] ") + message)


def login():
    print("\n=== LOGIN ===")
    username = required_input("Email    : ")
    password = read_secret("Password : ")
    user = authenticate(username, password)
    if not user:
        print("[ERROR] Email atau password salah.")
        return
    print("\nSelamat datang, " + user["full_name"] + "!")
    if user["role"] == "admin":
        admin_menu(user)
    else:
        customer_menu(user)
    sign_out()


def show_products():
    print("\n=== PRODUCT CATALOG ===")
    for item in get_products():
        print(
            f"{item['code']:<10} {item['name']:<16} "
            f"{money(item['base_price']):>14} | {item['description']}"
        )


def create_order(user):
    show_products()
    product_codes = {item["code"] for item in get_products()}
    product_code = required_input("\nKode produk: ").upper()
    if product_code not in product_codes:
        print("[ERROR] Produk tidak ditemukan.")
        return

    try:
        length = float(required_input("Panjang (cm): "))
        if not 1 <= length <= 1000:
            raise ValueError
    except ValueError:
        print("[ERROR] Panjang harus berupa angka antara 1 dan 1000 cm.")
        return

    material = required_input("Material (besi/baja): ").lower()
    if material not in {"besi", "baja"}:
        print("[ERROR] Material harus besi atau baja.")
        return

    motif = required_input("Motif/desain: ")
    handle = required_input("Jenis gagang: ")
    print("\nLayanan tambahan:")
    print("1. Finishing premium  (+Rp30.000)")
    print("2. Ukiran ornamen     (+Rp20.000)")
    print("3. Pengiriman         (+Rp15.000)")
    choice_text = input("Pilihan dipisahkan koma, kosong jika tidak ada: ").strip()
    mapping = {"1": "finishing", "2": "ornamen", "3": "pengiriman"}
    services = []
    if choice_text:
        for code in choice_text.split(","):
            code = code.strip()
            if code not in mapping:
                print("[ERROR] Pilihan layanan tidak valid.")
                return
            if mapping[code] not in services:
                services.append(mapping[code])

    try:
        order_code, total = OrderFacade().create_order(
            user["id"], product_code, length, material, motif, handle, services
        )
        print("\n" + "=" * 48)
        print("PESANAN BERHASIL DIBUAT")
        print("Kode pesanan : " + order_code)
        print("Total biaya  : " + money(total))
        print("Status       : Diterima")
        print("=" * 48)
    except (ValueError, RuntimeError) as exc:
        print("[ERROR] " + str(exc))


def show_orders(rows, include_customer=False):
    if not rows:
        print("\nBelum ada pesanan.")
        return
    print(f"\n{'ID':<5} {'KODE':<24} {'PRODUK':<15} {'STATUS':<15} {'TOTAL':>14}")
    print("-" * 82)
    for row in rows:
        print(
            f"{row['id']:<5} {row['order_code']:<24} {row['product_name']:<15} "
            f"{row['status']:<15} {money(row['total_price']):>14}"
        )
        if include_customer:
            print("      Customer: " + row["customer_name"])


def change_user_password(user):
    current = read_secret("Password saat ini: ")
    new = read_secret("Password baru (min. 8 karakter): ")
    if len(new) < 8:
        print("[ERROR] Password minimal 8 karakter.")
        return
    confirmation = read_secret("Ulangi password baru: ")
    if new != confirmation:
        print("[ERROR] Konfirmasi password tidak cocok.")
        return
    ok, message = change_password(user["id"], current, new)
    print(("[SUCCESS] " if ok else "[ERROR] ") + message)


def customer_menu(user):
    while True:
        print("\n" + "=" * 62)
        print(" CUSTOMER PANEL | " + user["full_name"])
        print("=" * 62)
        print("1. Lihat katalog produk")
        print("2. Buat pesanan custom")
        print("3. Pesanan saya")
        print("4. Notifikasi")
        print("5. Ganti password")
        print("0. Logout")
        choice = input("\nforgebound/customer> ").strip()

        if choice == "1":
            show_products()
        elif choice == "2":
            create_order(user)
        elif choice == "3":
            show_orders(get_customer_orders(user["id"]))
        elif choice == "4":
            items = get_notifications(user["id"])
            print("\n=== NOTIFIKASI ===")
            if not items:
                print("Belum ada notifikasi.")
            for item in items:
                print(f"[{item['created_at']}] {item['order_code']}: {item['message']}")
        elif choice == "5":
            change_user_password(user)
        elif choice == "0":
            return
        else:
            print("[ERROR] Pilihan tidak valid.")
        pause()


def admin_menu(user):
    while True:
        print("\n" + "=" * 62)
        print(" ADMIN PANEL | " + user["full_name"])
        print("=" * 62)
        print("1. Lihat katalog produk")
        print("2. Lihat semua pesanan")
        print("3. Lanjutkan tahap produksi")
        print("4. Batalkan pesanan")
        print("5. Ganti password admin")
        print("0. Logout")
        choice = input("\nforgebound/admin> ").strip()

        if choice == "1":
            show_products()
        elif choice == "2":
            show_orders(get_all_orders(), include_customer=True)
        elif choice in {"3", "4"}:
            show_orders(get_all_orders(), include_customer=True)
            order_id = required_input("\nID pesanan (UUID): ")
            ok, message = advance_order(order_id) if choice == "3" else cancel_order(order_id)
            print(("[SUCCESS] " if ok else "[ERROR] ") + message)
        elif choice == "5":
            change_user_password(user)
        elif choice == "0":
            return
        else:
            print("[ERROR] Pilihan tidak valid.")
        pause()


def main():
    while True:
        print("\n\033[2J\033[H", end="")
        banner()
        print("\n [1] Login")
        print(" [2] Register as Customer")
        print(" [0] Exit")
        choice = input("\nforgebound> ").strip()
        if choice == "1":
            login()
            pause()
        elif choice == "2":
            register()
            pause()
        elif choice == "0":
            print("\nTerima kasih telah menggunakan FORGEBOUND.")
            break
        else:
            print("[ERROR] Pilihan tidak valid.")
            pause()
