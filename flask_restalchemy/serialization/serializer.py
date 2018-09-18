from abc import ABC, abstractmethod


class Serializer(ABC):

    @abstractmethod
    def dump(self, value): pass

    @abstractmethod
    def load(self, serialized): pass
