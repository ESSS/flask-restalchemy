from io import BytesIO

from flask import request, send_file
from flask_restful import Resource

from ..declarative_base import db
from ..models.image import Image
from ..services.api import api
from ..services.authservice import auth_token_required


class ImageResourceCollection(Resource):
    @auth_token_required
    def post(self):
        # check if the post request has the file part
        file = request.files.get('file')
        if not file or not file.filename:
            return {'msg': 'No file identified'}, 400

        img = Image(image=file.read(), mimetype=file.mimetype)
        db.session.add(img)
        db.session.commit()
        return {'id': img.id}, 201


class ImageResourceItem(Resource):
    def get(self, id):
        img = Image.query.filter_by(id=id).first()
        if img:
            return send_file(BytesIO(img.image), mimetype=img.mimetype)
        return '', 404

    @auth_token_required
    def delete(self, id):
        data = Image.query.filter_by(id=id).first()
        if data:
            db.session.delete(data)
            db.session.commit()
            return '', 204
        return '', 404


# TODO: add swagger docs
class ImageChildResourceCollection(Resource):
    def __init__(self, **kwargs):
        self._parent_resource = kwargs.get('parent_resource')

    # @auth_token_required
    def get(self, parent_id):
        # check if the parent exists
        parent = self._parent_resource.query.filter_by(id=parent_id).first()
        if not parent:
            return {'msg': 'Parent resource does not exist!'}, 400

        images = parent.images.all()
        return images, 200

    @auth_token_required
    def post(self, parent_id):
        # check if the parent exists
        parent = self._parent_resource.query.filter_by(id=parent_id).first()
        if not parent:
            return {'msg': 'Parent resource does not exist!'}, 400

        # check if the post request has the file part
        file = request.files.get('file')
        if not file or not file.filename:
            return {'msg': 'No file identified'}, 400

        img = Image(image=file.read(), mimetype=file.mimetype)
        parent.images.append(img)
        db.session.commit()
        return {'id': img.id}, 201


def create_image_child_resource_api(parent_resource, url, tags):
    api.add_resource(ImageChildResourceCollection, url+'/<parent_id>/image',
                     resource_class_kwargs={'parent_resource': parent_resource})