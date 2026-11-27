# FORGEBOUND

Metal Production & Custom Order Management System. Python CLI for custom metalwork orders backed by Supabase.

## Actors
- **Admin**: manages orders, production stages, and order status.
- **Customer**: registers, logs in, creates custom orders, views orders and notifications.

## Design Patterns
- Factory Method: creates Golok, Cangkul, and Pagar Tempa objects.
- Builder: assembles custom orders.
- Decorator: adds finishing, ornament, and delivery services.
- Facade: coordinates order creation and pricing.
- State: controls production stages and cancellation rules.
- Observer: notifies customers about order changes.

## Requirements
- Python 3.11+
- Supabase project credentials

## Setup

1. Clone the repository and create a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # macOS/Linux
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and keep the publishable key:
   ```env
   SUPABASE_URL=https://atiabiwldcmnbncauqwa.supabase.co
   SUPABASE_PUBLISHABLE_KEY=your_publishable_key
   ```

4. **Create the first admin account once.** In Supabase Dashboard, open Project Settings → API Keys and copy a server-side **secret key** (or legacy service_role key) into `SUPABASE_SECRET_KEY` in your local `.env`. Then run:
   ```bash
   python setup_admin.py
   ```
   The script asks for admin email, name, and password, creates the Auth user, and sets the protected `app_metadata.role=admin`. Never commit `.env` or share the secret key. Remove `SUPABASE_SECRET_KEY` from `.env` after setup.

5. Start the CLI:
   ```bash
   python main.py
   ```

Customers register from the CLI using their name, email, and password. Login uses email and password. Depending on the project's Auth email-confirmation setting, customers may need to verify their email before logging in.

## Supabase
Project URL: https://atiabiwldcmnbncauqwa.supabase.co

Tables: `profiles`, `products`, `orders`, `order_items`, `production_history`, and `notifications`.

All exposed tables use Row Level Security. The admin role is checked from server-managed Auth app metadata, not user-editable profile metadata.
