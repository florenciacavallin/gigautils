import json
from functools import wraps

import requests
from flask import flash, request, redirect
from google.auth.transport import requests as google_auth_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from authentication.objects.Permission import Permission
from authentication.objects.User import User
from database.giga_engine import engine
from utils.request_helpers import redirect_url
# Although this import is unused it allows sqlalchemy to find the foreignkey reference
from authentication.objects.Role import Role

# Copyright 2019 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# [START getting_started_auth_all]

# see also https://cloud.google.com/iap/docs/authentication-howto
#          https://cloud.google.com/docs/authentication/getting-started

AUDIENCE = None


# [START getting_started_auth_metadata]
def get_metadata(item_name):
    """Returns a string with the project metadata value for the item_name.
    See https://cloud.google.com/compute/docs/storing-retrieving-metadata for
    possible item_name values.
    """

    endpoint = 'http://metadata.google.internal'
    path = '/computeMetadata/v1/project/'
    path += item_name
    response = requests.get(
        '{}{}'.format(endpoint, path),
        headers={'Metadata-Flavor': 'Google'}
    )
    metadata = response.text
    return metadata
# [END getting_started_auth_metadata]


# [START getting_started_auth_audience]
def audience():
    """Returns the audience value (the JWT 'aud' property) for the current
    running instance. Since this involves a metadata lookup, the result is
    cached when first requested for faster future responses.
    """
    global AUDIENCE
    if AUDIENCE is None:
        project_number = get_metadata('numeric-project-id')
        project_id = get_metadata('project-id')
        AUDIENCE = '/projects/{}/apps/{}'.format(
            project_number, project_id
        )
    return AUDIENCE
# [END getting_started_auth_audience]


# [START iap_validate_jwt]
def validate_iap_jwt(iap_jwt) -> tuple[str, str]:
    """
    Checks that the JWT assertion is valid (properly signed, for the
     correct audience) and if so, returns strings for the requesting user's
     email and a persistent user ID. If not valid, returns None for each field.

    Source: https://github.com/GoogleCloudPlatform/python-docs-samples/blob/main/iap/validate_jwt.py

    :param iap_jwt: The contents of the X-Goog-IAP-JWT-Assertion header.

    :returns: user_email, user_id
    """
    try:
        decoded_jwt = id_token.verify_token(
            iap_jwt,
            google_auth_requests.Request(),
            audience=audience(),
            certs_url="https://www.gstatic.com/iap/verify/public_key",
        )
        return decoded_jwt["email"], decoded_jwt["sub"]
    except Exception as e:
        return None, None
# [END iap_validate_jwt]


# [START getting_started_auth_front_controller]
def get_user():
    from flask import request

    if check_cron_job():
        # Check if it is a cron job then return the default email id for it
        return 'cron_job'
    assertion = request.headers.get('X-Goog-IAP-JWT-Assertion')
    email, user_id = validate_iap_jwt(assertion)
    return str(email)
# [END getting_started_auth_front_controller]


def forwarded_for():
    """
    Retrieves the forwarded_for header
    """
    from flask import request
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for is None:
        forwarded_for = 'None'
    return forwarded_for


def check_auth(cursor, email=None, permission="default") -> bool:
    """
    The check_auth method will search for the e-mail address associated with the HTTP request
    Returns True if the user has a role that has the requested permission
    Returns False if the user does not have a role that has the requested permission

    :param cursor - database connection
    :param email - The e-mail address of the user that should be checked
    :param permission - The permission the user should be authenticated for

    :returns authorized - A boolean specifying if the user is authorized for that permission or not

    :raises RuntimeError When referenced outside of request context without filling the email parameter
    """
    if email is None:
        email = get_user().lower()
    else:
        email = email.lower()

    try:
        verify_authentication_call(cursor, email, permission)
    except AttributeError as e:
        print(f'Verify Authentication Call failed with reason {str(e)}')
        flash(str(e))
        return False

    get_user_sql = select(User).where(User.email == email)
    user = cursor.execute(get_user_sql).scalar()
    for user_role in user.roles:
        for role_permission in user_role.role.permissions:
            if role_permission.permission.name == permission:
                return True

    return False


def verify_authentication_call(cursor, email: str, permission: str):
    """
    This method will verify the authentication call and check the following points.
        1. The existence of the permission
        2. The existence of a role
        3. The existence of permissions for that role
        4. The existence of the user
    If any of those points fail, the method will raise an AttributeError
    :return None:

    :raises AttributeError: If any of the above conditions fail
    """
    contact = 'Please contact an administrator.'
    # 1. Verify existence of the permission
    try:
        get_permission_sql = select(Permission).where(Permission.name == permission)
        cursor.execute(get_permission_sql).one()
    except NoResultFound:
        raise AttributeError(f"The permission '{permission}' does not exist. {contact}")

    # 4. Verify existence of the User
    try:
        get_user_sql = select(User).where(User.email == email)
        user_row = cursor.execute(get_user_sql).one()
        # 2. Verify existence of Role for User
        user = user_row[0]
        if len(user.roles) == 0:
            raise AttributeError(f'User {email} has no Role. {contact}')
        for user_role in user.roles:
            # 3. Verify existence of Permission for Role
            if len(user_role.role.permissions) != 0:
                return
        raise AttributeError(f'User {email} has no Roles with Permissions. {contact}')
    except NoResultFound:
        raise AttributeError(f'User {email} was added to IAP but not to the database. {contact}')


def require_permission(permission: str,
                       allowed_task_queues: tuple[str] = (),
                       allow_cron_job: bool = False, redirect_if_unauthorized: bool = True):
    """
    The require_permission method is a decorator usable for flask routes to check authentication
        per route. It will show the route if check_auth(permission) is True or send the user
        to a 401 page otherwise.

    :param permission: A string representing the permission the user must have to access the route
    :param allow_cron_job: A boolean that specifies if a cron job is allowed to access the route
    :param allowed_task_queues: a list of names of app-engine task-queue that are allowed to access the route
    :param redirect_if_unauthorized: A boolean for if the user should be redirected (302) or 401 if authentication fails
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if allow_cron_job and request.headers.get('X-Appengine-Cron', False) == 'true':
                return func(*args, **kwargs)
            if request.headers.get('X-Appengine-Queuename', ()) in allowed_task_queues:
                return func(*args, **kwargs)
            # Check the authentication of the user
            with Session(engine) as cursor:
                authorized = check_auth(cursor, permission=permission)

            if authorized:
                # User is authenticated, allow the request to proceed
                return func(*args, **kwargs)
            # User is not authenticated
            if redirect_if_unauthorized:
                flash(f'You were not authorized to go there; Permission: "{permission}" is needed.')
                flash(f'Please contact an admin (IT Team) if you want to access to "{func.__name__}".')
                flash('For now I have brought you to your previous page.')
                return redirect(redirect_url())
            else:
                return json.dumps({'error': 'Authentication failed.'}), 401

        return wrapper

    return decorator


def check_cron_job():
    """
    Checks based on the headers, if a request is made by a cron job
    """
    from flask import request

    return request.headers.get('X-Appengine-Cron', False) == 'true'
