============================
Flask-RESTAlchemy Change Log
============================

.. current developments

v0.8.3
====================



v0.8.2
====================



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

