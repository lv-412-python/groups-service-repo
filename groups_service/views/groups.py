"""Group view implementation."""
from marshmallow import ValidationError, fields
from flask_api import status
from sqlalchemy.exc import IntegrityError
from flask import request, Response
from flask_restful import Resource, HTTPException
from webargs.flaskparser import parser

from groups_service import APP
from groups_service.db import DB
from groups_service.serializers import (
    GROUP_SCHEMA,
    GROUPS_SCHEMA,
    WORKER_SCHEMA
)
from groups_service.models.group import Groups, Forms


def check_authority(view):
    """Decorator for resources"""
    def func_wrapper(*args, **kwargs):
        """wrapper"""
        if request.cookies['admin'] == 'False' and request.method != 'GET':
            return {"error": "Forbidden."}, status.HTTP_403_FORBIDDEN
        return view(*args, **kwargs)
    return func_wrapper


class GroupResource(Resource):
    """Class GroupView implementation."""
    @check_authority
    def post(self):#pylint: disable=no-self-use
        """
        Post method for creating a new group.
        :return: Response object or error message with status code.
        """
        try:
            req = GROUP_SCHEMA.load(request.json).data
        except ValidationError as err:
            APP.logger.error(err.args)
            return err.messages, status.HTTP_400_BAD_REQUEST
        forms_id = req.pop('assigned_to_forms', None)
        list_forms = [Forms(form_id.get('form_id')) for form_id in forms_id] if forms_id else None
        if list_forms:
            req.update({'assigned_to_forms' : list_forms})
        else:
            req.update({'assigned_to_forms' : []})

        new_group = Groups(**req)
        DB.session.add(new_group)
        try:
            DB.session.commit()
        except IntegrityError as err:
            APP.logger.error(err.args)
            DB.session.rollback()
            return {'error': 'Already exist'}, status.HTTP_400_BAD_REQUEST
        return Response(status=status.HTTP_201_CREATED)

    @check_authority
    def get(self, group_id=None):# pylint: disable=no-self-use
        """
        Get method for Group Service.
        :return: requested groups with status code or error message with status code.
        """
        if group_id:
            group = Groups.query.get(group_id)
            result = GROUP_SCHEMA.dump(group).data
        else:
            url_args = {
                'group_id': fields.List(fields.Integer(validate=lambda val: val > 0)),
                'owner': fields.List(fields.Integer(validate=lambda val: val > 0)),
                'user_id': fields.Integer(validate=lambda val: val > 0)
            }
            try:
                args = parser.parse(url_args, request)
            except HTTPException as err:
                APP.logger.error(err.args)
                return {'error': 'Invalid URL.'}, status.HTTP_400_BAD_REQUEST
            if args.get('group_id'):
                title_groups = Groups.query.filter(
                    Groups.id.in_(args['group_id'])
                    )
                result = WORKER_SCHEMA.dump(title_groups).data
            elif args.get('owner'):
                owner_groups = Groups.query.filter(Groups.owner_id.in_(args['owner']))
                result = GROUPS_SCHEMA.dump(owner_groups).data
            elif args.get('user_id'):
                search = "%{}%".format(args['user_id'])
                forms_to_user = Groups.query.filter(Groups.members.match(search)).first()
                result = GROUP_SCHEMA.dump(forms_to_user).data
            else:
                return {'error': 'Invalid URL.'}, status.HTTP_400_BAD_REQUEST

        return (result, status.HTTP_200_OK) if result else \
               ({'error': 'Does not exist.'}, status.HTTP_404_NOT_FOUND)

    @check_authority
    def put(self, group_id):#pylint: disable=no-self-use
        """
        Put method for the group.
        :return: Response object or error message with status code.
        """
        try:
            updated_data = GROUP_SCHEMA.load(request.json).data
        except ValidationError as err:
            APP.logger.error(err.args)
            return err.messages, status.HTTP_400_BAD_REQUEST

        updated_group = Groups.query.get(group_id)
        if updated_group is None:
            return {'error': 'Does not exist.'}, status.HTTP_404_NOT_FOUND

        forms_id = updated_data.pop('assigned_to_forms', None)
        list_forms = [Forms(form_id.get('form_id')) for form_id in forms_id] if forms_id else None
        if list_forms:
            updated_data.update({'assigned_to_forms' : list_forms})
        else:
            updated_data.update({'assigned_to_forms' : []})

        for key, value in updated_data.items():
            setattr(updated_group, key, value)
        DB.session.commit()

        return Response(status=status.HTTP_200_OK)
