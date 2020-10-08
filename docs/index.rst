.. Flask-RESTAlchemy documentation master file, created by
   sphinx-quickstart on Fri Mar 23 18:56:26 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Flask-RESTAlchemy's!
====================

A Flask extension to build REST APIs based on `SQLAlchemy`_ models. Exported models expose all their properties by
default, making the definition of *Schema* classes optional.

Installation
------------

Install Flask-RESTAlchemy with `pip`:

.. code-block:: shell

    pip install flask-restalchemy

or `conda` (package available on `conda-forge`_):

.. code-block:: shell

    conda install flask-restalchemy -c conda-forge


Minimal App
-----------

Let's define a very simple *SQLAlchemy* model using `flask-sqlalchemy`_:

.. code-block:: python

    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import Column, String, Integer

    db = SQLAlchemy()


    class Hero(db.Model):
        id = Column(Integer, primary_key=True)
        name = Column(String)
        secret_name = Column(String)

Expose SQLAlchemy models in a very simple way is one of the aims of Flask-RESTAlchemy. Just instantiate an `Api` object
and use `Api.add_model` to expose a model through an endpoint:

.. code-block:: python

    from flask import Flask
    from flask_restalchemy import Api

    app = Flask("tour-of-heroes")


    @app.route("/create_db", methods=["POST"])
    def create_db():
        db.create_all()
        return "DB created"


    # Set an SQLite in-memory database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)  # Must be called before Api object creation

    api = Api(app)
    api.add_model(Hero, "/heroes")

    if __name__ == "__main__":
        app.run()

`Api.add_model` creates methods GET and POST for the `Heroes` collection at  ``/heroes`` and methods GET, PUT and DELETE
for ``/heroes/:id`` Let's see it in action:

.. code-block:: shell

    $ python app.py
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

    $ curl -X POST http://localhost:5000/create_db
    DB Created

    $ curl -H "Content-Type:application/json" -d "{\"name\":\"Mr. Nice\"}" http://localhost:5000/heroes
    $ curl -X GET http://localhost:5000/heroes/1
    {
        "id": 1,
        "name": "Mr. Nice",
        secret_name: "",
    }

Serializers could be used to override the default serialization of models:

.. code-block:: python

    class HeroSerializer(ModelSerializer):

        secret_name = Field(load_only=True)


    api = Api(app)
    api.add_model(Hero, "/heroes", serializer_class=HeroSerializer)

In the above example, `secret_name` property will not be exposed on a GET, but can be updated in a PUT or POST.

.. _conda-forge: https://conda-forge.org
.. _flask-sqlalchemy: http://lask-sqlalchemy.pocoo.org
.. _SQLAlchemy: http://www.sqlalchemy.org

Documentation
=============

.. toctree::
   :maxdepth: 2

   source/api_reference
