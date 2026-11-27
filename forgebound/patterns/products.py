from abc import ABC, abstractmethod


class MetalProduct(ABC):
    def __init__(self, code, name, base_price):
        self.code = code
        self.name = name
        self.base_price = base_price

    @abstractmethod
    def specifications(self):
        raise NotImplementedError


class Golok(MetalProduct):
    def specifications(self):
        return "Perkakas potong"


class Cangkul(MetalProduct):
    def specifications(self):
        return "Peralatan pertanian"


class PagarTempa(MetalProduct):
    def specifications(self):
        return "Produk konstruksi dekoratif"


class ProductFactory(ABC):
    @abstractmethod
    def create_product(self):
        raise NotImplementedError


class GolokFactory(ProductFactory):
    def create_product(self):
        return Golok("GLK-001", "Golok", 150000)


class CangkulFactory(ProductFactory):
    def create_product(self):
        return Cangkul("CGL-001", "Cangkul", 125000)


class PagarTempaFactory(ProductFactory):
    def create_product(self):
        return PagarTempa("PGT-001", "Pagar Tempa", 500000)


def get_product_factory(product_code):
    factories = {
        "GLK-001": GolokFactory,
        "CGL-001": CangkulFactory,
        "PGT-001": PagarTempaFactory,
    }
    try:
        return factories[product_code]()
    except KeyError as exc:
        raise ValueError("Produk tidak dikenal.") from exc
