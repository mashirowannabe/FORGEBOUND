import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL dan SUPABASE_PUBLISHABLE_KEY belum diatur di .env")
    return create_client(url, key)


def create_customer(full_name, username, email, password):
    try:
        response = get_client().auth.sign_up({
            "email": email.strip().lower(),
            "password": password,
            "options": {"data": {"full_name": full_name.strip()}},
        })
        if not response.user:
            return False, "Registrasi gagal. Periksa konfigurasi Supabase Auth."
        if not response.session:
            return True, "Akun dibuat. Verifikasi email sebelum login jika diminta."
        return True, "Registrasi berhasil. Silakan login."
    except Exception as exc:
        return False, f"Registrasi gagal: {exc}"


def authenticate(email, password):
    try:
        response = get_client().auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password,
        })
        user = response.user
        if not user:
            return None
        profile = (
            get_client().table("profiles").select("id, full_name, role")
            .eq("id", user.id).single().execute().data
        )
        return {
            "id": user.id,
            "email": user.email,
            "full_name": profile["full_name"],
            "role": profile["role"],
        }
    except Exception:
        return None


def change_password(user_id, current_password, new_password):
    try:
        client = get_client()
        email = client.auth.get_user().user.email
        client.auth.sign_in_with_password({"email": email, "password": current_password})
        client.auth.update_user({"password": new_password})
        return True, "Password berhasil diperbarui."
    except Exception as exc:
        return False, f"Gagal memperbarui password: {exc}"


def sign_out():
    try:
        get_client().auth.sign_out()
    except Exception:
        pass
