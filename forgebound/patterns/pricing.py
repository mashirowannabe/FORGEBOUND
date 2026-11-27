from abc import ABC, abstractmethod


class PriceComponent(ABC):
    @abstractmethod
    def total(self):
        raise NotImplementedError

    @abstractmethod
    def description(self):
        raise NotImplementedError


class BasePrice(PriceComponent):
    def __init__(self, amount):
        self.amount = amount

    def total(self):
        return self.amount

    def description(self):
        return "Harga dasar produk"


class PriceDecorator(PriceComponent):
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def total(self):
        return self._wrapped.total()

    def description(self):
        return self._wrapped.description()


class FinishingDecorator(PriceDecorator):
    COST = 30000

    def total(self):
        return self._wrapped.total() + self.COST

    def description(self):
        return self._wrapped.description() + " + Finishing premium"


class OrnamentDecorator(PriceDecorator):
    COST = 20000

    def total(self):
        return self._wrapped.total() + self.COST

    def description(self):
        return self._wrapped.description() + " + Ukiran ornamen"


class DeliveryDecorator(PriceDecorator):
    COST = 15000

    def total(self):
        return self._wrapped.total() + self.COST

    def description(self):
        return self._wrapped.description() + " + Pengiriman"


SERVICE_DECORATORS = {
    "finishing": FinishingDecorator,
    "ornamen": OrnamentDecorator,
    "pengiriman": DeliveryDecorator,
}


def calculate_price(base_amount, services):
    component = BasePrice(base_amount)
    for service in services:
        decorator = SERVICE_DECORATORS.get(service)
        if decorator is None:
            raise ValueError("Layanan tidak dikenal: " + service)
        component = decorator(component)
    return component
