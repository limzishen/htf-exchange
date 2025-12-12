class Matcher:
    """Base class for all matchers."""
    def match(self, order_book, incoming_order):
        raise NotImplementedError
