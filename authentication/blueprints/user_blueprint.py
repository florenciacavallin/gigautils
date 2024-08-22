from flask import Blueprint, redirect, request, render_template, flash
from markupsafe import Markup
from gigautils.authentication.authenticate import require_permission
from gigautils.authentication.objects.User import User, UserForm, DeleteUserForm, PROTECTED_USERS
from gigautils.authentication.objects.UserRole import UserRole
from sqlalchemy import select
from database.giga_engine import engine

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, IntegrityError

user_blueprint = Blueprint('user_blueprint', __name__, url_prefix='/user')

sidebar = [('Table Maintenance', [('User', '/table_maintenance/user'),
                                  ('User-Role', '/table_maintenance/user_role'),
                                  ('Role', '/table_maintenance/role'),
                                  ('Role-Permission', '/table_maintenance/role_permission'),
                                  ('Permission', '/table_maintenance/permission')]),
           ('User', [('Index', '/table_maintenance/user'),
                     ('Add', '/table_maintenance/user/create'),
                     ('Edit', '/table_maintenance/user/edit'),
                     ('Delete', '/table_maintenance/user/delete')])]


@user_blueprint.route('/')
@user_blueprint.route('/index')
@require_permission('admin_read_only')
def index():
    """Index returns an overview of all user objects"""
    sqlalchemy_statement = select(User)
    columnname = ['User ID', 'First name', 'Last name', 'E-mail', 'Birthday', 'Valid Until', '']
    data = []
    with Session(engine) as cursor:
        for user in cursor.execute(sqlalchemy_statement).scalars():
            edit_button = Markup(f"<a class='w3-button w3-small w3-theme-d3 w3-round w3-theme-d5 (w3-theme-dark)' "
                                 f"href='/table_maintenance/user/edit/{user.id}'>Edit</a>")
            data.append([user.id, user.first_name, user.last_name, user.email, user.birthday,
                         user.valid_until, edit_button])
    return render_template('simple_table.html', sidebar=sidebar, title='Users',
                           columnname=columnname, data=data)


@user_blueprint.route('/create', methods=['GET', 'POST'])
@require_permission('admin')
def create():
    """Create returns a form to create a user object"""
    user_form = UserForm(request.form)

    if user_form.validate_on_submit() and request.method == 'POST':
        with Session(engine) as cursor:
            new_user = user_form.create_user()

            try:
                cursor.add(new_user)
                # Flush to retrieve user id
                cursor.flush()
                new_user_role = UserRole(user_id=new_user.id, role_id=1)
                # Add default role to new created user
                cursor.add(new_user_role)
                cursor.commit()
                msg = f"Successfully created user {new_user.first_name} with ID {new_user.id}"
            except IntegrityError as e:
                print(f'Failed to add a User, with error: {str(e)}')
                msg = f"User not created: It is likely it already exists, otherwise check the logs"

            flash(msg)
            return redirect("/table_maintenance/user/index", code=302)

    return render_template('simple_form.html', form=user_form, submit_url='/table_maintenance/user/create',
                           title='Add New User', sidebar=sidebar, errors=user_form.errors)


@user_blueprint.route('/edit/', methods=['GET', 'POST'])
@user_blueprint.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@require_permission('admin')
def edit(user_id=None):
    """Edit returns a form to edit a user object, will redirect to create form if no user is specified"""
    if user_id is None:
        flash('Please select a user to edit by adding their ID: /user/edit/"user_id"')
        return redirect("/table_maintenance/user/create", code=302)
    user_form = UserForm(request.form)
    sqlalchemy_statement = select(User).where(User.id == user_id)

    with Session(engine) as cursor:
        try:
            user_to_edit = cursor.execute(sqlalchemy_statement).scalar_one()
        except NoResultFound:
            flash(f'The user with ID {user_id} does not exist')
            return redirect("/table_maintenance/user/create", code=302)

        if user_form.validate_on_submit() and request.method == 'POST':
            new_user = user_form.create_user()

            user_to_edit.edit_user(new_user)

            cursor.add(user_to_edit)
            cursor.commit()

            msg = f"Successfully updated user {user_to_edit.first_name} with ID {user_to_edit.id}"
            flash(msg)
            return redirect("/table_maintenance/user/index", code=302)

        user_form.populate_form(user_to_edit)

    return render_template('simple_form.html', form=user_form, sidebar=sidebar, title='Edit User',
                           errors=user_form.errors, submit_url=f'/table_maintenance/user/edit/{user_id}')


@user_blueprint.route('/delete', methods=['GET', 'POST'])
@require_permission('admin')
def delete():
    """Delete will open a form to allow deletion of the specified User object"""
    delete_user_form = DeleteUserForm(request.form)

    with Session(engine) as cursor:
        # Select all Users to fill the form
        sql_stmt = select(User).where(User.id.not_in(PROTECTED_USERS)).order_by(User.email)
        users = cursor.execute(sql_stmt).scalars()
        delete_user_form.user_id.choices = [(u.id, u.email) for u in users]

        if delete_user_form.validate_on_submit() and request.method == 'POST':
            return delete_user_form.delete(cursor)

    return render_template(
        'simple_form.html', form=delete_user_form,
        submit_url=f'/table_maintenance/user/delete',
        title='Delete User', sidebar=sidebar
    )

