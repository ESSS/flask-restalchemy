from .serializer import Serializer


class EnumSerializer(Serializer):

    def dump(self, value):
        if not value:
            return None
        return value.value

    def load(self, serialized):
        enum = getattr(self.column.type, 'enum_class')
        return enum(serialized)