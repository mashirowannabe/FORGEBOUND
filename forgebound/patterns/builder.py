from dataclasses import dataclass, field


@dataclass
class CustomOrder:
    customer_id: int
    product_code: str
    product_name: str
    length_cm: float
    material: str
    motif: str
    handle_type: str
    base_price: int
    services: list[str] = field(default_factory=list)


class OrderBuilder:
    def __init__(self):
        self.reset()

    def reset(self):
        self._data = {}

    def customer(self, customer_id):
        self._data["customer_id"] = customer_id
        return self

    def product(self, product):
        self._data.update(
            product_code=product.code,
            product_name=product.name,
            base_price=product.base_price,
        )
        return self

    def specifications(self, length_cm, material, motif, handle_type):
        self._data.update(
            length_cm=length_cm,
            material=material,
            motif=motif,
            handle_type=handle_type,
        )
        return self

    def services(self, services):
        self._data["services"] = list(services)
        return self

    def build(self):
        required = {
            "customer_id", "product_code", "product_name", "base_price",
            "length_cm", "material", "motif", "handle_type",
        }
        missing = required.difference(self._data)
        if missing:
            raise ValueError("Data pesanan belum lengkap: " + ", ".join(sorted(missing)))
        order = CustomOrder(**self._data)
        self.reset()
        return order
