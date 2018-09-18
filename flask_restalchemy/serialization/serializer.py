from abc import ABC, abstractmethod

from sqlalchemy import DateTime


class Serializer(ABC):

    def __init__(self, column):
        self.column = column

    @abstractmethod
    def dump(self, value): pass

    @abstractmethod
    def load(self, serialized): pass


def is_datetime_field(col):
    """
    Check if a column is DateTime (or implements DateTime)

    :param Column col: the column object to be checked

    :rtype: bool
    """
    if hasattr(col.type, "impl"):
        return type(col.type.impl) is DateTime
    else:
        return type(col.type) is DateTime


def is_enum_field(col):
    return hasattr(col.type, 'enum_class') and getattr(col.type, 'enum_class')
