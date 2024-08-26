import datetime as dt
import json
import warnings
from typing import Optional

import pytz
import requests
from flask import request, url_for


def make_http_request(url: str, headers: dict, method='post', data=None, timeout_s=2):
    """
    Extension of the requests.post()/patch()/get()/put() functions. Adds default error handling behaviors.
    Copied from gems.GemsRequest in grids
     :param method: post,put, patch or get
     :param url: url to post request
     :param data: json payload
     :param headers: headers
     :param timeout_s: how long the request is allowed to take before it timeouts in seconds
    """
    request_dict = {
        'post': requests.post,
        'get': requests.get,
        'patch': requests.patch,
        'put': requests.put,
        'delete': requests.delete
    }
    request_method = request_dict[method]
    try:
        if data is None:
            response = request_method(url=url, headers=headers, timeout=timeout_s)
        else:
            response = request_method(url=url, data=data, headers=headers, timeout=timeout_s)
        content = response.content
        status_code = response.status_code
    except requests.exceptions.ConnectionError:
        # Network issue at our end
        status_code = 0
        content = "Unable to connect to server"
    except requests.exceptions.ReadTimeout:
        # No data response
        status_code = 408
        content = f"Timeout on request to: {url}"

    try:
        json_data = json.loads(content)
    except json.decoder.JSONDecodeError:
        json_data = content
    if isinstance(json_data, bytes):
        json_data = json_data.decode(encoding='utf-8')
    return json_data, status_code


def redirect_url(default='home_page'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


def parse_date_parameter(url_parameter,
                         default_value: Optional[dt.datetime] = None,
                         error_message: Optional[str] = None,
                         tz_info: pytz.timezone = pytz.timezone('Europe/Amsterdam'),
                         parameter_name: Optional[str] = '',
                         assume_naive_timezones: Optional[bool] = False) -> dt.datetime:
    """
    Pass your request.args.get(<parameter_name> as the url_parameter and watch this method validate and return the
      the correct timezone aware object. Allow default values by passing a default value, allow naive or aware timezones
      with assume_naive_timezones and adjust error messages however you like.

    :param url_parameter: The result of request.args.get(parameter_name)
    :param default_value: Optional default value to return if the parameter is not present
    :param error_message: An optional error message to return if the parameter is not present
    :param tz_info: The timezone to use for the datetime object
    :param parameter_name: The string parameter_name is used to inform the user of which parameter had the error
    :param assume_naive_timezones: A boolean specifying if it is allowed to assume the timezone of the url_parameter
    :return: The parsed datetime parameter of timezone tz_info

    :raises ValueError: If the parameter is present but cannot be parsed to a datetime
    :raises ValueError: If the parameter is NOT present and there is no default
    """
    if url_parameter is None:
        if default_value is None:
            raise ValueError(f'Invalid parameter {parameter_name}. This is a required isoformat datetime parameter.')
        if default_value.tzinfo is not tz_info:
            warnings.warn("The default of parse_date_parameter is in a different timezone then"
                          "when parsing the parameter.", stacklevel=2)
        return default_value  # If there is no parameter, return the default value

    try:
        parameter_value = dt.datetime.fromisoformat(url_parameter)
        if parameter_value.tzinfo is None:  # If the url_parameter is timezone naive
            if assume_naive_timezones:  # We need to use localize, if we assume its timezone
                parameter_value = tz_info.localize(parameter_value)
            else:
                raise ValueError(f"{parameter_name} must be timezone aware")
        parameter_value = parameter_value.astimezone(tz_info)
    except ValueError:
        if error_message is None:
            error_message = f'Invalid parameter {parameter_name}. ' \
                            f'Valid format is: %Y-%m-%dT%H:%M:%S+%z or any other isoformat'
        raise ValueError(error_message)

    return parameter_value
