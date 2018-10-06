class Printable:
    """A base class which implements printing functionality of objects."""
    def __repr__(self):
        return str(self.__dict__)
