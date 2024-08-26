from flask import Blueprint, redirect, request, render_template, flash

from gigautils.authentication.authenticate import require_permission
from gigautils.authentication.objects.Role import Role, RoleForm, DeleteRoleForm, PROTECTED_ROLES
from markupsafe import Markup
from sqlalchemy import select

from gigautils.authentication.objects.RolePermission import RolePermission
from gigautils.database.giga_engine import engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, IntegrityError

role_blueprint = Blueprint('role_blueprint', __name__, url_prefix='/role')

sidebar = [('Table Maintenance', [('User', '/table_maintenance/user'),
                                  ('User-Role', '/table_maintenance/user_role'),
                                  ('Role', '/table_maintenance/role'),
                                  ('Role-Permission', '/table_maintenance/role_permission'),
                                  ('Permission', '/table_maintenance/permission')]),
           ('Role', [('Index', '/table_maintenance/role'),
                     ('Add', '/table_maintenance/role/create'),
                     ('Edit', '/table_maintenance/role/edit'),
                     ('Delete', '/table_maintenance/role/delete')])]


@role_blueprint.route('/')
@role_blueprint.route('/index')
@require_permission('admin_read_only')
def index():
    """Index returns an overview of all role objects"""
    sqlalchemy_statement = select(Role)
    columnname = ['ID', 'Name', '']
    data = []
    with Session(engine) as cursor:
        for role in cursor.execute(sqlalchemy_statement).scalars():
            edit_button = Markup(f"<a class='w3-button w3-small w3-theme-d3 w3-theme-d5 (w3-theme-dark)' "
                                 f"href='/table_maintenance/role/edit/{role.id}'>Edit</a>")
            data.append([role.id, role.name, edit_button])
    return render_template('simple_table.html', sidebar=sidebar, title='Roles',
                           columnname=columnname, data=data)


@role_blueprint.route('/create', methods=['GET', 'POST'])
@require_permission('admin')
def create():
    """Create returns a form to create a role object"""
    role_form = RoleForm(request.form)

    if role_form.validate_on_submit() and request.method == 'POST':
        with Session(engine) as cursor:
            new_role = role_form.create_role()

            try:
                cursor.add(new_role)
                # Flush to retrieve role id
                cursor.flush()
                new_role_permission = RolePermission(role_id=new_role.id, permission_id=1)
                # Add default permission to new created role
                cursor.add(new_role_permission)
                cursor.commit()
                msg = f"Successfully created role {new_role.name} with ID {new_role.id}"
            except IntegrityError as e:
                print(f'Failed to add a Role, with error: {str(e)}')
                msg = f"Role not created: It is likely it already exists, otherwise check the logs"

            flash(msg)
            return redirect("/table_maintenance/role/index", code=302)

    return render_template('simple_form.html', form=role_form, submit_url='/table_maintenance/role/create',
                           title='Add New Role', sidebar=sidebar, errors=role_form.errors)


@role_blueprint.route('/edit/', methods=['GET', 'POST'])
@role_blueprint.route('/edit/<int:role_id>', methods=['GET', 'POST'])
@require_permission('admin')
def edit(role_id=None):
    """Edit returns a form to edit a role object, will redirect to create form if no role is specified"""
    if role_id is None:
        flash('Please select a role to edit by adding their ID: /role/edit/"role_id"')
        return redirect("/table_maintenance/role/create", code=302)
    role_form = RoleForm(request.form)
    sqlalchemy_statement = select(Role).where(Role.id == role_id)

    with Session(engine) as cursor:
        try:
            role_to_edit = cursor.execute(sqlalchemy_statement).scalar_one()
        except NoResultFound:
            flash(f'The role with ID {role_id} does not exist')
            return redirect("/table_maintenance/role/create", code=302)

        if role_form.validate_on_submit() and request.method == 'POST':
            new_role = role_form.create_role()

            role_to_edit.edit_role(new_role)

            cursor.add(role_to_edit)
            cursor.commit()

            msg = f"Successfully updated role {role_to_edit.name} with ID {role_to_edit.id}"
            flash(msg)
            return redirect("/table_maintenance/role/index", code=302)

        role_form.populate_form(role_to_edit)

    return render_template('simple_form.html', form=role_form, sidebar=sidebar, title='Edit Role',
                           errors=role_form.errors, submit_url=f'/table_maintenance/role/edit/{role_id}')


@role_blueprint.route('/delete', methods=['GET', 'POST'])
@require_permission('admin')
def delete():
    """Delete will open a form to allow deletion of a Role object"""
    delete_role_form = DeleteRoleForm(request.form)

    with Session(engine) as cursor:
        # Select all Roles to fill the form
        sql_stmt = select(Role).where(Role.id.not_in(PROTECTED_ROLES)).order_by(Role.name)
        roles = cursor.execute(sql_stmt).scalars()
        delete_role_form.role_id.choices = [(r.id, r.name) for r in roles]

        if delete_role_form.validate_on_submit() and request.method == 'POST':
            return delete_role_form.delete(cursor)

    return render_template(
        'simple_form.html', form=delete_role_form,
        submit_url=f'/table_maintenance/role/delete',
        title='Delete Role', sidebar=sidebar
    )
