from infrastructure.repository import OrderRepository, OutboxRepository, InboxRepository

class UnitOfWork:
    def __init__(self, session):
        self.session = session
        self.orders = OrderRepository(session)
        self.outbox = OutboxRepository(session)
        self.inbox = InboxRepository(session)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()