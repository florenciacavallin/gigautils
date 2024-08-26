from flask import Blueprint, redirect, request, render_template, flash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from authentication.authenticate import require_permission
from authentication.objects.Role import Role
from authentication.objects.User import User
from authentication.objects.UserRole import UserRole, UserRoleForm, DeleteUserRoleForm
from database.giga_engine import engine

user_role_blueprint = Blueprint('user_role_blueprint', __name__, url_prefix='/user_role')

sidebar = [('Table Maintenance', [('User', '/table_maintenance/user'),
                                  ('User-Role', '/table_maintenance/user_role'),
                                  ('Role', '/table_maintenance/role'),
                                  ('Role-Permission', '/table_maintenance/role_permission'),
                                  ('Permission', '/table_maintenance/permission')]),
           ('User-Role', [('Index', '/table_maintenance/user_role'),
                          ('Add', '/table_maintenance/user_role/create'),
                          ('Delete', '/table_maintenance/user_role/delete')])]


@user_role_blueprint.route('/')
@user_role_blueprint.route('/index')
@require_permission('admin_read_only')
def index():
    """Index returns an overview of all user-role objects"""
    sqlalchemy_statement = select(UserRole)
    columnname = ['User ID', 'User', 'Role', 'Role ID']
    data = []
    with Session(engine) as cursor:
        for user_role in cursor.execute(sqlalchemy_statement).scalars():
            user = user_role.user.first_name + ' ' + user_role.user.last_name
            row = [user_role.user_id, user, user_role.role.name, user_role.role_id]
            data.append(row)
    return render_template('simple_table.html', sidebar=sidebar, title='UserRoles',
                           columnname=columnname, data=data)


@user_role_blueprint.route('/create', methods=['GET', 'POST'])
def create():
    """Create returns a form to create a user-role object"""
    user_role_form = UserRoleForm(request.form)

    with Session(engine) as cursor:
        users = cursor.execute(select(User).order_by(User.email)).scalars()
        user_role_form.user_id.choices = [(u.id, u.email) for u in users]

        roles = cursor.execute(select(Role).order_by(Role.name)).scalars()
        user_role_form.role_id.choices = [(r.id, r.name) for r in roles]

        if user_role_form.validate_on_submit() and request.method == 'POST':
            new_user_role = user_role_form.create_user_role()

            try:
                cursor.add(new_user_role)
                cursor.commit()
                msg = f"Successfully added role {new_user_role.role.name} to user {new_user_role.user.first_name}"
            except IntegrityError as e:
                print(f'Failed to add a UserRole, with error:{str(e)}')
                msg = f"UserRole not created: It is likely it already exists, otherwise check the logs"

            flash(msg)
            return redirect("/table_maintenance/user_role/index", code=302)

    return render_template('simple_form.html', form=user_role_form, submit_url='/table_maintenance/user_role/create',
                           title='Add New UserRole', sidebar=sidebar, errors=user_role_form.errors)


@user_role_blueprint.route('/delete', methods=['GET', 'POST'])
@require_permission('admin')
def delete():
    """Delete will open a form to allow deletion of a UserRole object"""
    delete_user_role_form = DeleteUserRoleForm(request.form)

    with Session(engine) as cursor:
        # Select all Users to fill the form
        users = cursor.execute(select(User).order_by(User.email)).scalars()
        delete_user_role_form.user_id.choices = [(u.id, u.email) for u in users]

        # Select all Roles to fill the form
        roles = cursor.execute(select(Role).order_by(Role.name)).scalars()
        delete_user_role_form.role_id.choices = [(r.id, r.name) for r in roles]

        if delete_user_role_form.validate_on_submit() and request.method == 'POST':
            return delete_user_role_form.delete(cursor)

    return render_template(
        'simple_form.html', form=delete_user_role_form,
        submit_url=f'/table_maintenance/user_role/delete',
        title='Delete UserRole', sidebar=sidebar
    )
