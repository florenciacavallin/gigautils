from flask import Blueprint, redirect, request, render_template, flash
from markupsafe import Markup
from sqlalchemy.exc import NoResultFound, IntegrityError, ResourceClosedError
from sqlalchemy.orm import Session
from authentication.authenticate import require_permission
from authentication.objects.Permission import Permission, PermissionForm, DeletePermissionForm, \
    PROTECTED_PERMISSIONS
from sqlalchemy import select
from database.giga_engine import engine

permission_blueprint = Blueprint('permission_blueprint', __name__, url_prefix='/permission')

sidebar = [('Table Maintenance', [('User', '/table_maintenance/user'),
                                  ('User-Role', '/table_maintenance/user_role'),
                                  ('Role', '/table_maintenance/role'),
                                  ('Role-Permission', '/table_maintenance/role_permission'),
                                  ('Permission', '/table_maintenance/permission')]),
           ('Permission', [('Index', '/table_maintenance/permission'),
                           ('Add', '/table_maintenance/permission/create'),
                           ('Edit', '/table_maintenance/permission/edit'),
                           ('Delete', '/table_maintenance/permission/delete')])]


@permission_blueprint.route('/')
@permission_blueprint.route('/index')
@require_permission('admin_read_only')
def index():
    """Index returns an overview of all permission objects"""
    sqlalchemy_statement = select(Permission)
    columnname = ['ID', 'Name', '']
    data = []
    with Session(engine) as cursor:
        for permission in cursor.execute(sqlalchemy_statement).scalars():
            edit_button = Markup(f"<a class='w3-button w3-small w3-theme-d3 w3-round w3-theme-d5 (w3-theme-dark)' "
                                 f"href='/table_maintenance/permission/edit/{permission.id}'>Edit</a>")
            data.append([permission.id, permission.name, edit_button])
    return render_template('simple_table.html', sidebar=sidebar, title='Permissions',
                           columnname=columnname, data=data)


@permission_blueprint.route('/create', methods=['GET', 'POST'])
@require_permission('admin')
def create():
    """Create returns a form to create a permission object"""
    permission_form = PermissionForm(request.form)

    if permission_form.validate_on_submit() and request.method == 'POST':
        with Session(engine) as cursor:
            new_permission = permission_form.create_permission()

            try:
                cursor.add(new_permission)
                cursor.commit()
                msg = f"Successfully created permission {new_permission.name} with ID {new_permission.id}"
            except IntegrityError as e:
                print(f'Failed to add a Permission, with error: {str(e)}')
                msg = f"Permission not created: It is likely it already exists, otherwise check the logs"

            flash(msg)
            return redirect("/table_maintenance/permission/index", code=302)

    return render_template('simple_form.html', form=permission_form, submit_url='/table_maintenance/permission/create',
                           title='Add New Permission', sidebar=sidebar, errors=permission_form.errors)


@permission_blueprint.route('/edit/', methods=['GET', 'POST'])
@permission_blueprint.route('/edit/<int:permission_id>', methods=['GET', 'POST'])
@require_permission('admin')
def edit(permission_id=None):
    """Edit returns a form to edit a permission object, will redirect to create form if no permission is specified"""
    if permission_id is None:
        flash('Please select a permission to edit by adding their ID: /permission/edit/"permission_id"')
        return redirect("/table_maintenance/permission/index", code=302)
    permission_form = PermissionForm(request.form)
    sqlalchemy_statement = select(Permission).where(Permission.id == permission_id)

    with Session(engine) as cursor:
        try:
            permission_to_edit = cursor.execute(sqlalchemy_statement).scalar_one()
        except NoResultFound:
            flash(f'The permission with ID {permission_id} does not exist')
            return redirect("/table_maintenance/permission/index", code=302)

        if permission_form.validate_on_submit() and request.method == 'POST':
            new_permission = permission_form.create_permission()

            permission_to_edit.edit_permission(new_permission)

            cursor.add(permission_to_edit)
            try:
                cursor.commit()
            except ResourceClosedError:
                flash(f'The permission with ID {permission_id} can\'t be updated.')
                return redirect("/table_maintenance/permission/index", code=302)

            msg = f"Successfully updated permission {permission_to_edit.name} with ID {permission_to_edit.id}"
            flash(msg)
            return redirect("/table_maintenance/permission/index", code=302)

        permission_form.populate_form(permission_to_edit)

    return render_template('simple_form.html', form=permission_form, sidebar=sidebar,
                           errors=permission_form.errors, title='Edit Permission',
                           submit_url=f'/table_maintenance/permission/edit/{permission_id}')


@permission_blueprint.route('/delete', methods=['GET', 'POST'])
@require_permission('admin')
def delete_permission():
    """Delete will open a form to allow deletion of a Permission object"""
    delete_permission_form = DeletePermissionForm(request.form)

    with Session(engine) as cursor:
        # Select all Permissions to fill the form
        sql_stmt = select(Permission).where(Permission.id.not_in(PROTECTED_PERMISSIONS)).order_by(Permission.name)
        permissions = cursor.execute(sql_stmt).scalars()
        delete_permission_form.permission_id.choices = [(p.id, p.name) for p in permissions]

        if delete_permission_form.validate_on_submit() and request.method == 'POST':
            return delete_permission_form.delete(cursor)

    return render_template(
        'simple_form.html', form=delete_permission_form,
        submit_url=f'/table_maintenance/permission/delete',
        title='Delete Permission', sidebar=sidebar
    )