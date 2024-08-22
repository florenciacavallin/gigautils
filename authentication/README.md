# Authentication
Overview of directory:
* **authenticate.py** - Direct access to all authentication related methods
* **table_maintenance_blueprint.py** - The table maintenance route that currently only creates, visualises and edits the objects used in authentication
* **blueprints** - Directory containing the blueprints for creating, visualising and editing authenticatio objects
* **objects** - Directory containing the Python objects that define authenticated Users, Roles and Permissions.

## General authentication overview
There are 5 defined python objects that are utilised by authentication.
3 actual objects, User, Role and Permission.
2 relationship tables, UserRole and Role Permission.
These relationships define the One to Many relationship between their respective objects.

A textual approach to these objects can be found below:
* User table that stores information related to individuals accessing your application.
* UserRole table that stores association between a user and the roles.
* Role table that stores information of roles a user can have.
* RolePermission table that stores association between roles and permissions. That is which role has which permissions.
* Permission table that stores information about resources and actions that can be performed on resources.

This design was taken from [this blog post](https://www.nikhilajain.com/post/user-role-permission-model).
A visual overview is offered at the bottom of this document.

## Default Permissions
The `AuthenticateRequestHandler` uses 'automatically' generated permissions to verify actions taken.
When creating an instance of the handler, a `request_type` (str) and `staas_asset_id` (int) are offered.
The name of the permission will be formatted as follows: `permission_name = f'{staas_asset_id}_{request_type}'`.
If authentication is checked without the permission being part of the SQL table a warning will be raised.

## Visual overview of User, Role and permission design
<p align="center">
  <img width="1000" height="523" src="https://github.com/GigaStorage/storage-as-a-service/blob/main/images/role-based-access-control.jpg?raw=True">
</p>
