from abc import ABC, abstractmethod

from datetime import datetime

import re


class Serializer(ABC):


    @abstractmethod
    def dump(self, value): pass

    @abstractmethod
    def load(self, serialized): pass


class DateTimeSerializer(Serializer):
    """
    Serializer for DateTime objects
    """

    ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    def __init__(self, str_format: str = ISO_FORMAT):
        self._str_format = str_format

    def dump(self, value):
        if not value:
            return
        return value.strftime(self._str_format)

    def load(self, serialized):
        if re.search("\+\d{4}$", serialized):
            serialized_format = self._str_format
        else:
            serialized_format = self._str_format.rstrip("%z")
        return datetime.strptime(serialized, serialized_format)
