
class Matcher:

    """Base class for all matchers."""

    def match(self, order_book, order):
        raise NotImplementedError
