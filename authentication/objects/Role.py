import json
import os

from flask import flash
from flask import redirect
from flask_wtf import FlaskForm
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from wtforms import StringField, SubmitField, SelectField

from gigautils.database.model import Base
# Although this import is unused it allows sqlalchemy to find the foreignkey reference
from gigautils.authentication.objects.UserRole import UserRole
from gigautils.authentication.objects.RolePermission import RolePermission


PROTECTED_ROLES = json.loads(os.environ.get('PROTECTED_ROLES', '[]'))


class Role(Base):
    """
    A Role stores information of roles a user can have.
    """
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    users = relationship(
        "UserRole",
        backref="role",
        cascade="all, delete",
        passive_deletes=False,
    )
    permissions = relationship(
        "RolePermission",
        backref="role",
        cascade="all, delete",
        passive_deletes=False,
    )

    def __str__(self) -> str:
        """String representation of the Role object"""
        return f'Role {self.id}: {self.name}'

    def edit_role(self, new_role):
        """
        Edit the attributes of the self Role object with the new_role
        :param new_role: Role object that should overwrite the self object
        """
        self.name = new_role.name


class RoleForm(FlaskForm):
    """
    RoleForm to create and edit Role objects
    """
    id = StringField('ID', render_kw={'readonly': True})
    name = StringField('Name')
    submit = SubmitField('Submit')

    def create_role(self) -> Role:
        """Create Role object of data in the Form"""
        name = self.name.data
        new_role = Role(name=name)
        return new_role

    def populate_form(self, role):
        """
        Use the offered role object to fill the form.
        :param role: Role object whose information should be in the form
        """
        self.id.data = role.id
        self.name.data = role.name


class DeleteRoleForm(FlaskForm):
    """
    DeleteRoleForm to delete a Role object
    """
    role_id = SelectField('Role', coerce=int)
    submit = SubmitField('Delete')

    def delete(self, cursor: Session) -> redirect:
        """
        Delete Role from SQL based on flask form input

        :param cursor: Session connection to the MySQL database
        :return: redirects to /table_maintenance/role/index
        """
        if self.role_id.data in PROTECTED_ROLES:
            flash(f'Role with ID {self.role_id.data} is protected.')
            return redirect("/table_maintenance/role/index", code=302)

        sql_statement = select(Role).where(Role.id == self.role_id.data)
        try:
            role_to_delete = cursor.execute(sql_statement).scalar_one()
        except NoResultFound:
            flash(f'The role with ID {self.role_id.data} does not exist')
            return redirect("/table_maintenance/role/index", code=302)

        cursor.delete(role_to_delete)
        msg = f'Successfully deleted role {role_to_delete.name} with ID {role_to_delete.id}'

        try:
            cursor.commit()
        except OperationalError:
            msg = f'MySQL error when deleting, please retry'

        flash(msg)
        return redirect("/table_maintenance/role/index", code=302)
