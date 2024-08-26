from flask import Blueprint, render_template

from authentication.authenticate import require_permission
from authentication.blueprints.user_blueprint import user_blueprint, sidebar as user_sidebar
from authentication.blueprints.role_blueprint import role_blueprint, sidebar as role_sidebar
from authentication.blueprints.permission_blueprint import permission_blueprint, sidebar as permission_sidebar
from authentication.blueprints.user_role_blueprint import user_role_blueprint, sidebar as user_role_sidebar
from authentication.blueprints.role_permission_blueprint import role_permission_blueprint, \
                                                                        sidebar as role_permission_sidebar


table_maintenance_blueprint = Blueprint('table_maintenance_blueprint', __name__, url_prefix='/table_maintenance')

table_maintenance_blueprint.register_blueprint(user_blueprint)
table_maintenance_blueprint.register_blueprint(user_role_blueprint)
table_maintenance_blueprint.register_blueprint(role_blueprint)
table_maintenance_blueprint.register_blueprint(role_permission_blueprint)
table_maintenance_blueprint.register_blueprint(permission_blueprint)

sidebar = [user_sidebar[1], user_role_sidebar[1], role_sidebar[1], role_permission_sidebar[1], permission_sidebar[1]]


@table_maintenance_blueprint.route('/')
@require_permission('admin')
def home():
    topic_home_menu_items = [('User', '/table_maintenance/user', 'fa-user'),
                             ('User-Role', '/table_maintenance/user_role', 'fa-users'),
                             ('Role', '/table_maintenance/role', 'fa-id-badge'),
                             ('Role-Permission', '/table_maintenance/role_permission', 'fa-tags'),
                             ('Permission', '/table_maintenance/permission', 'fa-shield')]

    return render_template('topic_home.html', title='Table Maintenance', sidebar=sidebar,
                           topic_home_menu_items=topic_home_menu_items)
