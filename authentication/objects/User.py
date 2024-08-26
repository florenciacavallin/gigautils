import datetime as dt
import json
import os

from flask import redirect, flash
from flask_wtf import FlaskForm
from sqlalchemy import Column, Integer, String, Date, DateTime, select
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from wtforms import StringField, DateField, SubmitField, SelectField

from database.model import Base
# Although this import is unused it allows sqlalchemy to find the foreignkey reference
from authentication.objects.UserRole import UserRole

PROTECTED_USERS = json.loads(os.environ.get('PROTECTED_USERS', '[]'))


class User(Base):
    """
    A User stores information related to individuals accessing your application.
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(45), unique=True)
    birthday = Column(Date, default='1900-01-01')
    valid_until = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    roles = relationship(
        "UserRole",
        backref="user",
        cascade="all, delete",
        passive_deletes=False,
    )

    def __str__(self) -> str:
        """String representation of the User object"""
        return f'User {self.id}: {self.first_name} {self.last_name}. E-mail: {self.email}'

    def edit_user(self, new_user):
        """
        Edit the attributes of the self User object with the new_user
        :param new_user: User object that should overwrite the self object
        """
        self.first_name = new_user.first_name
        self.last_name = new_user.last_name
        self.email = new_user.email
        self.birthday = new_user.birthday
        self.valid_until = new_user.valid_until


class UserForm(FlaskForm):
    """
    UserForm to create and edit User objects
    """
    id = StringField('ID', render_kw={'readonly': True})
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = StringField('Email')
    birthday = DateField('Birthday', default=dt.date(1900, 1, 1))
    valid_until = DateField('Valid Until', default=dt.date.today())
    submit = SubmitField('Submit')

    def create_user(self) -> User:
        """Create User object of data in the Form"""
        first_name = self.first_name.data
        last_name = self.last_name.data
        user_email = self.email.data
        user_birthday = self.birthday.data
        valid_until = self.valid_until.data

        new_user = User(first_name=first_name, last_name=last_name, email=user_email,
                        birthday=user_birthday, valid_until=valid_until)

        return new_user

    def populate_form(self, user):
        """
        Use the offered user object to fill the form.
        :param user: User object whose information should be in the form
        """
        self.id.data = user.id
        self.first_name.data = user.first_name
        self.last_name.data = user.last_name
        self.email.data = user.email
        self.birthday.data = user.birthday
        self.valid_until.data = user.valid_until


class DeleteUserForm(FlaskForm):
    """
    DeleteUserForm to delete a User object
    """
    user_id = SelectField('User', coerce=int)
    submit = SubmitField('Delete')

    def delete(self, cursor: Session) -> redirect:
        """
        Delete User from SQL based on flask form input

        :param cursor: Session connection to the MySQL database
        :return: redirects to /table_maintenance/user/index
        """
        if self.user_id.data in PROTECTED_USERS:
            flash(f'User with ID {self.user_id.data} is protected.')
            return redirect("/table_maintenance/user/index", code=302)

        sql_statement = select(User).where(User.id == self.user_id.data)
        try:
            user_to_delete = cursor.execute(sql_statement).scalar_one()
        except NoResultFound:
            flash(f'The user with ID {self.user_id.data} does not exist')
            return redirect("/table_maintenance/user/index", code=302)

        cursor.delete(user_to_delete)
        msg = f'Successfully deleted user {user_to_delete.first_name} with ID {user_to_delete.id}'

        try:
            cursor.commit()
        except OperationalError:
            msg = f'MySQL error when deleting, please retry'

        flash(msg)
        return redirect("/table_maintenance/user/index", code=302)
