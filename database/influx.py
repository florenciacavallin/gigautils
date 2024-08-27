from dotenv import load_dotenv
import os
import influxdb_client

# Take environment variables from .env if available
load_dotenv()

test_influx_token = os.environ.get('INFLUX_API_TOKEN_TEST')
prd_influx_token = os.environ.get('INFLUX_API_TOKEN_PRD')


def influx_vars(bool_test_env: bool = True) -> (str, str, str):
    """
    influx_vars will return the influx variables
    :param bool_test_env: boolean specifying the environment
    :return: url, token, org
    """
    if bool_test_env:
        token = test_influx_token
    else:
        token = prd_influx_token

    url = 'https://eu-central-1-1.aws.cloud2.influxdata.com'
    org = 'GIGA Storage'
    return url, token, org


def init_influx_client(bool_test_env: bool = True, timeout: int = 10000) -> influxdb_client.InfluxDBClient:
    """
    init_influx_client initialises the influx client
    :param bool_test_env: boolean specifying the environment
    :return: The influx_client
    """
    url, token, org = influx_vars(bool_test_env)
    influx_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, timeout=timeout,
                                                   auth_basic=False, profilers="query, operator", ssl_verify=False)
    return influx_client


def get_bucket(db_name: str, bool_test_env: bool = True) -> str:
    """
    The get_bucket method will retrieve the right bucket/database for the influx client
    :param bool_test_env: boolean specifying the environment
    :param db_name: the name of the database
    :return: string name of the bucket matching the environment
    """
    if bool_test_env:
        bucket = f"{db_name}-test"
    else:
        bucket = f"{db_name}-prd"
    return bucket