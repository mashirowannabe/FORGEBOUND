from abc import ABC, abstractmethod


class OrderState(ABC):
    name = "Tidak diketahui"

    @abstractmethod
    def next_stage(self, order):
        raise NotImplementedError

    def cancel(self, order):
        raise ValueError("Pesanan tidak dapat dibatalkan pada tahap " + self.name + ".")

    def change_design(self, order, **changes):
        raise ValueError("Desain tidak dapat diubah pada tahap " + self.name + ".")


class DiterimaState(OrderState):
    name = "Diterima"

    def next_stage(self, order):
        order.state = PenempaanState()


class PenempaanState(OrderState):
    name = "Penempaan"

    def next_stage(self, order):
        order.state = PembentukanState()


class PembentukanState(OrderState):
    name = "Pembentukan"

    def next_stage(self, order):
        order.state = FinishingState()


class FinishingState(OrderState):
    name = "Finishing"

    def next_stage(self, order):
        order.state = SelesaiState()


class SelesaiState(OrderState):
    name = "Selesai"

    def next_stage(self, order):
        raise ValueError("Pesanan sudah selesai.")


class DibatalkanState(OrderState):
    name = "Dibatalkan"

    def next_stage(self, order):
        raise ValueError("Pesanan sudah dibatalkan.")


class ProductionOrder:
    def __init__(self, status="Diterima"):
        states = {
            "Diterima": DiterimaState,
            "Penempaan": PenempaanState,
            "Pembentukan": PembentukanState,
            "Finishing": FinishingState,
            "Selesai": SelesaiState,
            "Dibatalkan": DibatalkanState,
        }
        if status not in states:
            raise ValueError("Status tidak valid: " + status)
        self.state = states[status]()

    @property
    def status(self):
        return self.state.name

    def next_stage(self):
        self.state.next_stage(self)

    def cancel(self):
        # Cancellation is allowed only before forging begins.
        if isinstance(self.state, DiterimaState):
            self.state = DibatalkanState()
            return
        self.state.cancel(self)

    def change_design(self, **changes):
        if isinstance(self.state, DiterimaState):
            return changes
        return self.state.change_design(self, **changes)
