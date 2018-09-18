from .enumserializer import EnumSerializer
from .datetimeserializer import DateTimeSerializer
from .fields import Field
from .serializer import Serializer, is_datetime_field, is_enum_field


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

    def get_model_name(self) -> str:
        return self._mapper_class.__name__

    @property
    def model_columns(self) -> dict:
        return self._mapper_class.__mapper__.c

    def dump(self, model):
        serial = {}
        for attr, field in self._fields.items():
            if field.load_only:
                continue
            value = getattr(model, attr) if hasattr(model, attr) else None
            if value and field and field.serializer:
                serialized = field.serializer.dump(value)
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
            # If deserialization must update an existing model, check if primary key is the same
            pk_name = self._get_pk_name(existing_model)
            assert getattr(existing_model, pk_name) == serialized[pk_name], \
                "Primary key value of serialized nested object is inconsistent"
        else:
            model = self._mapper_class()
        for field_name, value in serialized.items():
            field = self._fields[field_name]
            if field.dump_only:
                continue
            if value is None:
                deserial_value = value
            elif field.serializer:
                if isinstance(field.serializer, ModelSerializer):
                    if existing_model:
                        existing_nested = getattr(existing_model, field_name)
                    else:
                        existing_nested = self._find_existing_model(field, value)
                    deserial_value = field.serializer.load(value, existing_nested)
                else:
                    deserial_value = field.serializer.load(value)
            else:
                deserial_value = value
            setattr(model, field_name, deserial_value)
        return model

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

    def _find_existing_model(self, field, value):
        class_mapper = field.serializer._mapper_class
        pk_name = self._get_pk_name(class_mapper)
        pk = value.get(pk_name)
        if pk:
            return class_mapper.query.get(pk)
        else:
            return None

    def _get_pk_name(self, existing_model):
        primary_keys = existing_model.__mapper__.primary_key
        assert len(primary_keys) == 1, "Nested object must have exactly one primary key"
        pk_name = primary_keys[0].key
        return pk_name
