from .enumserializer import EnumSerializer
from .datetimeserializer import DateTimeSerializer
from .fields import Field
from .serializer import Serializer
from flask_restalchemy.serialization.enumserializer import is_enum_field
from flask_restalchemy.serialization.datetimeserializer import is_datetime_field


class ModelSerializer(Serializer):
    """
    Serializer for SQLAlchemy Declarative classes
    """

    DEFAULT_SERIALIZERS = [
        (is_datetime_field, DateTimeSerializer),
        (is_enum_field, EnumSerializer)
    ]

    def __init__(self, model_class):
        """
        :param Type[DeclarativeMeta] model_class: the SQLAlchemy mapping class to be serialized
        """
        self._mapper_class = model_class
        self._fields = self._get_declared_fields()
        # Collect columns not declared in the serializer
        for column in self.model_columns.keys():
            field = self._fields.setdefault(column, Field())
            # Set a serializer for fields that can not be serialized by default
            if field.serializer is None:
                serializer = self._get_default_serializer(self.model_columns.get(column))
                if serializer:
                    field._serializer = serializer

    @property
    def model_class(self):
        return self._mapper_class

    @property
    def model_columns(self):
        return self._mapper_class.__mapper__.c

    def dump(self, model):
        serial = {}
        for attr, field in self._fields.items():
            if field.load_only:
                continue
            value = getattr(model, attr) if hasattr(model, attr) else None
            if field:
                serialized = field.dump(value)
            else:
                serialized = value
            serial[attr] = serialized
        return serial

    def load(self, serialized, existing_model=None):
        """
        Instancialize a Declarative model from a serialized dict

        :param dict serialized: the serialized object.

        :param None|DeclarativeMeta existing_model: If given, the model will be updated with the serialized data.

        :rtype: DeclarativeMeta
        """
        if existing_model:
            model = existing_model
        else:
            model = self._mapper_class()
        for field_name, value in serialized.items():
            field = self._fields[field_name]
            if field.dump_only:
                continue
            deserialized = field.load(value)
            setattr(model, field_name, deserialized)
        return model

    def get_model_name(self) -> str:
        return self._mapper_class.__name__

    def before_put_commit(self, model, session):
        pass

    def after_put_commit(self, model, session):
        pass

    def before_post_commit(self, model, session):
        pass

    def after_post_commit(self, model, session):
        pass

    def _get_default_serializer(self, column):
        for check_type, serializer_class in self.DEFAULT_SERIALIZERS:
            if check_type(column):
                return serializer_class(column)

    @classmethod
    def _get_declared_fields(cls) -> dict:
        fields = {}
        # Fields should be only defined ModelSerializer subclasses,
        if cls is ModelSerializer:
            return fields
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            value = getattr(cls, attr_name)
            if isinstance(value, Field):
                fields[attr_name] = value
        return fields
