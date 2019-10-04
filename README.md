# Flask-RESTAlchemy #

[![travis-ci](https://api.travis-ci.org/ESSS/flask-restalchemy.svg?branch=master)](https://travis-ci.org/ESSS/flask-restalchemy)
[![codecov](https://codecov.io/gh/ESSS/flask-restalchemy/branch/master/graph/badge.svg)](https://codecov.io/gh/ESSS/flask-restalchemy)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


A Flask extension to build REST APIs. It dismiss the need of building *Schema* classes,
since usually all the information needed to serialize an SQLAlchemy instance is in the model
itself.

By adding a model to the API, all its properties will be exposed:

```python
class User(Base):

    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)
    password = Column(String)


api = Api(flask_app)
api.add_model(User, "/user")
```

To change the way properties are serialized, declare only the one that needs a non-default
behaviour:

```python
from flask_rest_orm import ModelSerializer, Field


class UserSerializer(ModelSerializer):

    password = Field(load_only=True)


api = Api(flask_app)
api.add_model(User, "/user", serializer_class=UserSerializer)
```

### Release
A reminder for the maintainers on how to make a new release.

Note that the VERSION should folow the semantic versioning as X.Y.Z
Ex.: v1.0.5

1. Create a ``release-VERSION`` branch from ``upstream/master``.
2. Update ``CHANGELOG.rst``.
3. Push a branch with the changes.
4. Once all builds pass, push a ``VERSION`` tag to ``upstream``.
5. Merge the PR.

[Changelog]: https://regro.github.io/rever-docs/devguide.html#changelog
