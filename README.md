# Flask-REST-ORM #

![travis-ci](https://api.travis-ci.org/ESSS/flask-rest-orm.svg?branch=master)

A Flask extension to build REST APIs. It dismiss the need of building *Schema* classes, 
since usually all the information needed to serialize an SQLAlchemy instance is in the model
itself.

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
from flask_rest_orm import ModelSerializer, Field

class UserSerializer(ModelSerializer):
        
    password = Field(load_only=True)


api = Api(flask_app)
api.add_model(User, '/user', serializer_class=UserSerializer)
```
### Creating a new release

We are using [rever](https://github.com/regro/rever) to release new versions of the package. Rever
automatically create project tags on GitHub, build and upload the PyPI package and change the recipe
on conda-forge. Just type:

```
rever setup  # (first time only)

rever <version>  # In the format 0.0.0
```

Some preconditions:

* Repository remote must be set using SSH protocol
* PyPI config file `.pypirc` must be on $HOME with the parameter `username` defined
