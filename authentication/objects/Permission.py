import json
import os

from flask import redirect, flash
from flask_wtf import FlaskForm
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql import select
from wtforms import SelectField
from wtforms import StringField, SubmitField

from database.model import Base
# Although this import is unused it allows sqlalchemy to find the foreignkey reference
from gigautils.authentication.objects.RolePermission import RolePermission

PROTECTED_PERMISSIONS = json.loads(os.environ.get('PROTECTED_PERMISSIONS', '[]'))


class Permission(Base):
    """
    A Permission stores information about resources and actions that can be performed on resources.
    """
    __tablename__ = 'permission'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    roles = relationship(
        "RolePermission",
        backref="permission",
        cascade="all, delete",
        passive_deletes=False,
    )

    def __str__(self) -> str:
        """String representation of the Permission object"""
        return f'Permission {self.id}: {self.name}'

    def edit_permission(self, new_permission):
        """
        Edit the attributes of the self Permission object with the new_permission
        :param new_permission: Permission object that should overwrite the self object
        """
        self.name = new_permission.name


class PermissionForm(FlaskForm):
    """
    PermissionForm to create and edit Permission objects
    """
    id = StringField('ID', render_kw={'readonly': True})
    name = StringField('Name')
    submit = SubmitField('Submit')

    def create_permission(self) -> Permission:
        """Create Permission object of data in the Form"""
        name = self.name.data
        new_permission = Permission(name=name)
        return new_permission

    def populate_form(self, permission):
        """
        Use the offered permission object to fill the form.
        :param permission: Permission object whose information should be in the form
        """
        self.id.data = permission.id
        self.name.data = permission.name


class DeletePermissionForm(FlaskForm):
    """
    DeletePermissionForm to delete a Permission object
    """
    permission_id = SelectField('Permission', coerce=int)
    submit = SubmitField('Delete')

    def delete(self, cursor_staas: Session) -> redirect:
        """
        Delete Permission from SQL based on flask form input

        :param cursor_staas: Session connection to the MySQL database
        :return: redirects to /table_maintenance/permission/index
        """
        if self.permission_id.data in PROTECTED_PERMISSIONS:
            flash(f'Permission with ID {self.permission_id.data} is protected.')
            return redirect("/table_maintenance/permission/index", code=302)

        sql_statement = select(Permission).where(Permission.id == self.permission_id.data)
        try:
            permission_to_delete = cursor_staas.execute(sql_statement).scalar_one()
        except NoResultFound:
            flash(f'The permission with ID {self.permission_id.data} does not exist')
            return redirect("/table_maintenance/permission/index", code=302)

        cursor_staas.delete(permission_to_delete)
        msg = f'Successfully deleted permission {permission_to_delete.name} with ID {permission_to_delete.id}'

        try:
            cursor_staas.commit()
        except OperationalError:
            msg = f'MySQL error when deleting, please retry'

        flash(msg)
        return redirect("/table_maintenance/permission/index", code=302)
