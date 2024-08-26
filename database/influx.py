import os

import influxdb_client


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


def init_influx_client(bool_test_env: bool = True) -> influxdb_client.InfluxDBClient:
    """
    init_influx_client intialises the influx client
    :param bool_test_env: boolean specifying the environment
    :return: The influx_client
    """
    url, token, org = influx_vars(bool_test_env)
    influx_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, timeout=10000,
                                                   auth_basic=False, profilers="query, operator", ssl_verify=False)
    return influx_client


def get_bucket(bool_test_env: bool = True) -> str:
    """
    The get_bucket method will retrieve the right bucket/database for the influx client
    :param bool_test_env: boolean specifying the environment
    :return: string name of the bucket matching the environment
    """
    if bool_test_env:
        bucket = "energy-trade-test"
    else:
        bucket = "energy-trade-prd"
    return bucket
