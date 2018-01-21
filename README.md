# Flask-REST-ORM #

![travis-ci](https://api.travis-ci.org/ESSS/flask-rest-orm.svg?branch=master)

A Flask extension to build REST APIs based on SQLAlchemy models. It uses [marshmallow-sqlalchemy]
to serialize models and avoid the need of building *Schema* classes, since *Schemas* are 
typically a repetition of your model.

By adding a model to the API, all its properties will be exposed:

```python
class User(Base):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)
    password = Column(String)
    

api = Api(flask_app)
api.add_model(User, '/user')
```

To change the way properties are serialized, declare only the one that needs a non-default 
behaviour:

```python
from marshmallow import fields
from marshmallow_sqlalchemy import ModelSchema

class UserSerializer(ModelSchema):
    class Meta:
        include_fk = True
        model = User
        
    password = fields.Str(load_only=True)


api = Api(flask_app)
api.add_model(User, '/user', serializer=UserSerializer())
```

[marshmallow-sqlalchemy]: https://marshmallow-sqlalchemy.readthedocs.io