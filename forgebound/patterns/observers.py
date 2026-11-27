class CustomerObserver:
    def __init__(self, user_id, order_id, notifier):
        self.user_id = user_id
        self.order_id = order_id
        self.notifier = notifier

    def update(self, message):
        self.notifier(self.user_id, self.order_id, message)


class OrderSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, message):
        for observer in list(self._observers):
            observer.update(message)
