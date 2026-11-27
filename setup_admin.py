import getpass
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def main():
    url = os.getenv("SUPABASE_URL")
    secret = os.getenv("SUPABASE_SECRET_KEY")
    if not url or not secret:
        raise SystemExit("Isi SUPABASE_URL dan SUPABASE_SECRET_KEY di .env terlebih dahulu.")

    email = input("Admin email: ").strip().lower()
    full_name = input("Nama admin: ").strip() or "FORGEBOUND Administrator"
    password = getpass.getpass("Password admin (min. 12 karakter): ")
    if len(password) < 12:
        raise SystemExit("Password admin harus minimal 12 karakter.")

    admin_client = create_client(url, secret)
    created = admin_client.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"full_name": full_name},
        "app_metadata": {"role": "admin"},
    })
    user = created.user
    if not user:
        raise SystemExit("Supabase tidak mengembalikan data user.")

    admin_client.table("profiles").upsert({
        "id": user.id, "full_name": full_name, "role": "admin"
    }).execute()
    print(f"Admin berhasil dibuat: {email}")
    print("Login menggunakan email dan password tersebut.")

if __name__ == "__main__":
    main()
