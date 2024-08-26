import json
import os

from flask import redirect, flash
from flask_wtf import FlaskForm
from sqlalchemy import Column, Integer, DateTime, ForeignKey, select
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from wtforms import SelectField, SubmitField

from database.model import Base

PROTECTED_ROLE_PERMISSIONS = json.loads(os.environ.get('PROTECTED_ROLE_PERMISSIONS', '[]'))


class RolePermission(Base):
    """
    A RolePermission stores association between roles and permissions. That is which role has which permissions.
    """
    __tablename__ = 'role_permission'

    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RolePermissionForm(FlaskForm):
    """
    RolePermissionForm to create RolePermission objects
    """
    role_id = SelectField('Role')
    permission_id = SelectField('Permission')
    submit = SubmitField('Submit')

    def create_role_permission(self) -> RolePermission:
        """Create RolePermission object of data in the Form"""
        role_id = self.role_id.data
        permission_id = self.permission_id.data
        new_role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        return new_role_permission


class DeleteRolePermissionForm(FlaskForm):
    """
    DeleteRolePermissionForm to delete a RolePermission object
    """
    role_id = SelectField('Role', coerce=int)
    permission_id = SelectField('Permission', coerce=int)
    submit = SubmitField('Delete')

    def delete(self, cursor: Session) -> redirect:
        """
        Delete RolePermission from SQL based on flask form input

        :param cursor: Session connection to the MySQL database
        :return: redirects to /table_maintenance/role_permission/index
        """
        role_permission_to_be_deleted = [self.role_id.data, self.permission_id.data]
        if role_permission_to_be_deleted in PROTECTED_ROLE_PERMISSIONS:
            flash(f'RolePermission {role_permission_to_be_deleted} is protected.')
            return redirect("/table_maintenance/role_permission/index", code=302)

        sql_statement = select(RolePermission).where(
            (RolePermission.role_id == self.role_id.data) &
            (RolePermission.permission_id == self.permission_id.data)
        )
        try:
            role_permission_to_delete = cursor.execute(sql_statement).scalar_one()
        except NoResultFound:
            flash(f'The RolePermission with role ID {self.role_id.data} and '
                  f'permission ID {self.permission_id.data} does not exist')
            return redirect("/table_maintenance/role_permission/index", code=302)

        cursor.delete(role_permission_to_delete)
        msg = f'Successfully deleted role permission with role ID {self.role_id.data} and ' \
              f'permission ID {self.permission_id.data}'

        try:
            cursor.commit()
        except OperationalError:
            msg = f'MySQL error when deleting, please retry'

        flash(msg)
        return redirect("/table_maintenance/role_permission/index", code=302)
