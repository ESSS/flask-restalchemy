============================
Flask-RESTAlchemy Change Log
============================

.. current developments

v0.14.1
====================

**Fixed:**

* Fix license placement on setup.py

v0.14.0
====================

**Added:**

* Added api decorator 'route' to register a url rule


v0.13.0
====================

**Changed:**

* Removed flask-restful dependency

**Added:**

* Added support for request decorators
* Added new field NestedModelListField
* Added support for free functions rules
* Added a way to specify the http methods available on an endpoint

**Fixed:**

* Fix bug that was removing target objects when undoing a relationship
* Fix bug that was causing the session not be passed to the serializers

v0.12.1
====================



v0.12.0
====================

**Changed:**

Change the way Column Serializers are registered: by using Api class method
`register_column_serializer` (instead of ModelSerializer.DEFAULT_SERIALIZER class attribute).



v0.11.1
====================

**Fixed:**

When adding the same property twice with different url an error occurred due to the endpoint provided to the RESTFul be
the same. Now add_property have an optional parameter 'endpoint_name' to enable specify a different endpoint and
defaults to the provided 'url_rule'

v0.11.0
====================

**Changed:**

* NestedAttributesField parameters must now be typed

**Fixed:**

* Swagger spec generation

v0.10.4
====================

**Added:**

* Support for append an existent item to a relation end point


v0.10.3
====================

v0.10.2
====================

v0.10.1
====================

**Added:**

* Support for pagination and query on property end points

v0.10.0
====================

**Added:**

* add pre/post commit hooks to put

v0.9.2
====================

**Added:**

* Support for serialize Enum columns
* Support for pagination on relationships


**Changed:**

* Now the auto generated end point name of a relationship uses the relationship name instead of the related model name

**Fixed:**

* Fix changelog auto generation


v0.9.0
====================

**Added:**

* Add pagination and filter support for relationships
* Add documentation with sphinx

**Changed:**


v0.8.5
====================

**Changed:**

* Change the way relation is checked on query related object

v0.8.3
====================

**Changed:**

* Make `query_from_request` reusable

v0.8.2
====================

**Added:**

* Enable deletion of an item from a relation that uses secondary table


v0.8.1
====================

**Added:**

* Support Flask Blueprints

v0.8.0
====================

**Added:**

* Added support to a unit definition for the Measure column

v0.7.1
====================

**Added:**

* Support custom hooks before and after commit data to the DB

v0.6.0
====================

**Changed:**

* Do not add Zulu TZ on naive datetimes
* Rename package from flask-rest-orm to flask-restalchemy

v0.5.0
====================

**Added:**

* Support filters and pagination

v0.4.1
====================

**Added:**

* Support custom implementation of DateTime columns

v0.4.2
====================

**Fixed:**

* Support Zulu time zone

v0.4.1
====================

**Added:**

* Added PrimaryKeyField to serialized only the Foreign key of a model

**Fixed:**

* Update classifiers by removing Python 2 support

v0.4.0
====================

**Changed:**

* Replace marshmallow serializers with our own serializer implementation
* More robust serialization of dates and times

v0.3.0
====================

**Added:**

* Added collection name parameter on add_model method
* Compatibility with python 3.5
* Enable custom endpoint

v0.2.0
====================

**Added:**

* Added query filters and limits

v0.1.0
====================

**Added:**

* First release version
