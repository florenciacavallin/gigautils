import os
from typing import Optional
import warnings

import sqlalchemy
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv

# Take environment variables from .env if available
load_dotenv()


def is_this_test_environment() -> bool:
    """
    Checks if the current environment is the test environment.
    :return: a boolean which is True if the current environment is the test environment, False otherwise.
    """
    result = None

    devshell = os.environ.get('DEVSHELL_PROJECT_ID')
    gcp = os.environ.get('GOOGLE_CLOUD_PROJECT')
    # TODO only use the giga_bool_test_env here
    giga_bool_test_env = os.environ.get('GIGA_BOOL_TEST_ENV', 'True') == 'True'

    if devshell is None and gcp == 'giga-energy-trade' and not giga_bool_test_env:
        result = False
    elif not giga_bool_test_env:
        warnings.warn('GIGA_BOOL_TEST_ENV wants to connect to the PRD environment. '
                      'I can see that we are not in PRD, overwriting bool_test_env to True (connect to TEST).')
        result = True
    else:
        result = True
    return result


def get_db_config(pool_size: int = 20, max_overflow: int = 5, time_out: int = 30, pool_recycle: int = 1800) -> dict:
    """
    Creates a configuration object (dictionary) that is used for configuring sqlalchemy connection engines.
    :param pool_size: Pool size is the maximum number of permanent connections to keep.
    :param max_overflow: The total number of concurrent connections for your
     application will be a total of pool_size and max_overflow.
    :param time_out: time in seconds until the connection to the Sql database times out and an exception is thrown.
    :param pool_recycle: time in seconds until the connection will be refreshed.
    :return:
    """
    db_config = {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": time_out,
        "pool_recycle": pool_recycle,
        # Verify all actions taken on the engine are compatible with SqlAlchemy 2.0
        "future": False
    }

    return db_config


def get_auth_params(bool_test_env: bool):
    """
    Gets the right authentication parameters to establish a sql database connection to either the test environment or
     the prd environment
    :param bool_test_env: retrieved fields will give access to the test database if this param is true
                        or the production database if this field is false
    :return:
    """
    if bool_test_env:
        db_user = os.getenv('TEST_GIGA_MYSQL_USERNAME')
        db_pass = os.getenv('TEST_GIGA_MYSQL_PASSWORD')
        instance_connection_name = "giga-energy-trade:europe-west4:giga-energy-trade-test-mysql"
    else:
        db_user = os.getenv('GIGA_MYSQL_USERNAME')
        db_pass = os.getenv('GIGA_MYSQL_PASSWORD')
        instance_connection_name = "giga-energy-trade:europe-west4:giga-energy-trade-mysql"

    return db_user, db_pass, instance_connection_name


def init_remote_connection_engine(bool_test_env: bool, db_name: str = 'giga_energy_trade') -> sqlalchemy.engine:
    """
    Initializes a remote database connection with the SQL database
    :param bool_test_env: connect to prd (False) or test (True) environment
    :param db_name: name of database to connect to

    :return: engine responsible for sql database connections
    """
    # initialize Connector object
    connector = Connector()
    db_user, db_pass, instance_connection_name = get_auth_params(bool_test_env)

    def create_connection():
        """This method will create a new connection to the database"""
        new_connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name
        )
        return new_connection

    # create connection pool
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=create_connection,
    )
    return pool


def init_connection_engine(bool_test_env: Optional[bool] = None) -> sqlalchemy.engine:
    """
    Function that returns the correct connection engine for the current development environment.
    It checks if we are on cloudshell prd/test and returns the right connection engine if we are,
    and returns a remote connection engine if we are not in prd, enabling the usage of the same function
    for remote testing and prd.
    :param bool_test_env: test (True) or prd (False) environment, only used for remote connections
    """
    if bool_test_env is None:
        bool_test_env = is_this_test_environment()

    make_remote_connection_bool = (os.environ.get('MAKE_REMOTE_CONNECTION', 'False') == 'True')
    if bool_test_env and make_remote_connection_bool:
        return init_remote_connection_engine(bool_test_env=bool_test_env)

    return init_unix_connection_engine(bool_test_env=bool_test_env)


def init_unix_connection_engine(db_name: str = 'giga_energy_trade', db_config: dict = None, bool_test_env=True):
    """
    initializes a connection running locally in the cloud
    :param bool_test_env: connect with test (True) or prd (False)
    :param db_name: name of database to connect to
    :param db_config: configuration settings generated through get_db_config()
    :return:
    """
    if db_config is None:
        db_config = get_db_config()

    db_user, db_pass, instance_connection_name = get_auth_params(bool_test_env)
    db_socket_dir = "cloudsql"

    engine = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={
                "unix_socket": "/{}/{}".format(
                    db_socket_dir,
                    instance_connection_name)
            }
        ),
        **db_config
    )

    if os.environ.get('DEVSHELL_PROJECT_ID') is None and bool_test_env:
        # DEVSHELL_PROJECT_ID is None usually points to production environment
        # this code will trigger if it seems to be bool_test_env
        warnings.warn("DEVSHELL_PROJECT_ID is None and you connecting to the test database. "
                      "Are you sure you don't want MAKE_REMOTE_CONNECTION=True?")
    # [END cloud_sql_mysql_sqlalchemy_create_socket]
    return engine
