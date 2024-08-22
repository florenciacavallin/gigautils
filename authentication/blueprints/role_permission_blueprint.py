from flask import Blueprint, redirect, request, render_template, flash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gigautils.authentication.authenticate import require_permission
from gigautils.authentication.objects.Permission import Permission
from gigautils.authentication.objects.Role import Role
from gigautils.authentication.objects.RolePermission import RolePermission, RolePermissionForm, DeleteRolePermissionForm
from database.giga_engine import engine

role_permission_blueprint = Blueprint('role_permission_blueprint', __name__, url_prefix='/role_permission')


sidebar = [('Table Maintenance', [('User', '/table_maintenance/user'),
                                  ('User-Role', '/table_maintenance/user_role'),
                                  ('Role', '/table_maintenance/role'),
                                  ('Role-Permission', '/table_maintenance/role_permission'),
                                  ('Permission', '/table_maintenance/permission')]),
           ('Role-Permission', [('Index', '/table_maintenance/role_permission'),
                                ('Add', '/table_maintenance/role_permission/create'),
                                ('Delete', '/table_maintenance/role_permission/delete')])]


@role_permission_blueprint.route('/')
@role_permission_blueprint.route('/index')
@require_permission('admin_read_only')
def index():
    """Index returns an overview of all role-permission objects"""
    sqlalchemy_statement = select(RolePermission)
    columnname = ['Role ID', 'Role', 'Permission', 'Permission ID']
    data = []
    with Session(engine_staas) as cursor_staas:
        for role_permission in cursor_staas.execute(sqlalchemy_statement).scalars():
            row = [role_permission.role_id, role_permission.role.name,
                   role_permission.permission.name, role_permission.permission_id]
            data.append(row)

    return render_template('simple_table.html', sidebar=sidebar, title='RolePermissions',
                           columnname=columnname, data=data)


@role_permission_blueprint.route('/create', methods=['GET', 'POST'])
@require_permission('admin')
def create():
    """Create returns a form to create a role-permission object"""
    role_permission_form = RolePermissionForm(request.form)

    with Session(engine_staas) as cursor_staas:
        roles = cursor_staas.execute(select(Role).order_by(Role.name)).scalars()
        role_permission_form.role_id.choices = [(r.id, r.name) for r in roles]

        permissions = cursor_staas.execute(select(Permission).order_by(Permission.name)).scalars()
        role_permission_form.permission_id.choices = [(p.id, p.name) for p in permissions]

        if role_permission_form.validate_on_submit() and request.method == 'POST':
            new_role_permission = role_permission_form.create_role_permission()

            try:
                cursor_staas.add(new_role_permission)
                cursor_staas.commit()
                msg = f"Succesfully add permission {new_role_permission.role.name} " \
                      f"to role {new_role_permission.permission.name}"
            except IntegrityError as e:
                print(f'Failed to add a RolePermission, with error: {str(e)}')
                msg = f"RolePermission not created: It is likely it already exists, otherwise check the logs"

            flash(msg)
            return redirect("/table_maintenance/role_permission/index", code=302)

    return render_template('simple_form.html', form=role_permission_form,
                           submit_url='/table_maintenance/role_permission/create',
                           title='Add New RolePermission', sidebar=sidebar, errors=role_permission_form.errors)


@role_permission_blueprint.route('/delete', methods=['GET', 'POST'])
@require_permission('admin')
def delete_role_permission():
    """Delete will open a form to allow deletion of a RolePermission object"""
    delete_role_permission_form = DeleteRolePermissionForm(request.form)

    with Session(engine_staas) as cursor_staas:
        # Select all Roles to fill the form
        roles = cursor_staas.execute(select(Role).order_by(Role.name)).scalars()
        delete_role_permission_form.role_id.choices = [(r.id, r.name) for r in roles]

        # Select all Permissions to fill the form
        permissions = cursor_staas.execute(select(Permission).order_by(Permission.name)).scalars()
        delete_role_permission_form.permission_id.choices = [(p.id, p.name) for p in permissions]

        if delete_role_permission_form.validate_on_submit() and request.method == 'POST':
            return delete_role_permission_form.delete(cursor_staas)

    return render_template(
        'simple_form.html', form=delete_role_permission_form,
        submit_url=f'/table_maintenance/role_permission/delete',
        title='Delete RolePermission', sidebar=sidebar
    )
