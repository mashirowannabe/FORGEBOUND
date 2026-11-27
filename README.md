# FORGEBOUND

Metal Production & Custom Order Management System.

Python CLI prototype for custom metalwork orders.

## Actors
- Admin: one seeded administrator account; manages orders and production stages.
- Customer: registers, logs in, creates custom orders, views orders and notifications.

## Design Patterns
- Factory Method: creates Golok, Cangkul, and Pagar Tempa objects.
- Builder: assembles custom orders.
- Decorator: adds finishing, ornament, and delivery services.
- Facade: coordinates order creation and pricing.
- State: controls production stages and cancellation rules.
- Observer: notifies customers about order changes.

## Run
Python 3.10+; no third-party packages required.

```bash
python main.py
```

SQLite database is created at `data/forgebound.db`.

Initial admin: username `admin`, password `ForgeAdmin123!`. Change it after first login.