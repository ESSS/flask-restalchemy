# Flask-RESTAlchemy #

![travis-ci](https://api.travis-ci.org/ESSS/flask-restalchemy.svg?branch=master)

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

For each PR, you must update the CHANGELOG using the `news` folder. See [Changelog] section of
Rever Developer's Guide on how to add a CHANGELOG entry.

```
rever setup  # (first time only)

rever <version>  # In the format 0.0.0
```

Some preconditions:

* flask-restalchemy-feedstock must be forked under your github account
* Repository remote must be set using SSH protocol
* PyPI config file `.pypirc` must be on $HOME with the following parameters:
```
[pypi]
username = <username>

[distutils]
index-servers = pypi
```

[Changelog]: https://regro.github.io/rever-docs/devguide.html#changelog
