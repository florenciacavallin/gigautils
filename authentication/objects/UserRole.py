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

PROTECTED_USER_ROLES = json.loads(os.environ.get('PROTECTED_USER_ROLES', '[]'))


class UserRole(Base):
    """
    A UserRole stores association between a user and the roles.
    """
    __tablename__ = 'user_role'

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserRoleForm(FlaskForm):
    """
    UserRoleForm to create UserRole objects
    """
    user_id = SelectField('User')
    role_id = SelectField('Role')
    submit = SubmitField('Submit')

    def create_user_role(self) -> UserRole:
        """Create UserRole object of data in the Form"""
        user_id = self.user_id.data
        role_id = self.role_id.data
        new_user_role = UserRole(user_id=user_id, role_id=role_id)
        return new_user_role


class DeleteUserRoleForm(FlaskForm):
    """
    DeleteUserRoleForm to delete a UserRole object
    """
    user_id = SelectField('User', coerce=int)
    role_id = SelectField('Role', coerce=int)
    submit = SubmitField('Delete')

    def delete(self, cursor_staas: Session) -> redirect:
        """
        Delete UserRole from SQL based on flask form input

        :param cursor_staas: Session connection to the MySQL database
        :return: redirects to /table_maintenance/user_role/index
        """
        user_role_to_be_deleted = [self.user_id.data, self.role_id.data]
        if user_role_to_be_deleted in PROTECTED_USER_ROLES:
            flash(f'UserRole {user_role_to_be_deleted} is protected.')
            return redirect("/table_maintenance/user_role/index", code=302)

        sql_statement = select(UserRole).where(
            (UserRole.user_id == self.user_id.data) &
            (UserRole.role_id == self.role_id.data)
        )
        try:
            user_role_to_delete = cursor_staas.execute(sql_statement).scalar_one()
        except NoResultFound:
            flash(f'The UserRole with user ID {self.user_id.data} and '
                  f'role ID {self.role_id.data} does not exist')
            return redirect("/table_maintenance/user_role/index", code=302)

        cursor_staas.delete(user_role_to_delete)
        msg = f'Successfully deleted UserRole with user ID {self.user_id.data} and ' \
              f'role ID {self.role_id.data}'

        try:
            cursor_staas.commit()
        except OperationalError:
            msg = f'MySQL error when deleting, please retry'

        flash(msg)
        return redirect("/table_maintenance/user_role/index", code=302)
