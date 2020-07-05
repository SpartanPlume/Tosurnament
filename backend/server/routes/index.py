"""index of /"""

import os
import importlib
import logging
import time
from urllib import parse
from common.databases.token import Token


def do_method(method, handler, parameters, url_parameters, ids_parameters, dir_to_list, module_name):
    module_dir = dir_to_list.replace("/", ".").replace("\\", ".")
    try:
        module = importlib.import_module(module_dir + module_name)
    except ModuleNotFoundError:
        return False
    try:
        method_to_do = getattr(module, method)
    except AttributeError:
        handler.send_error(405, "The HTTP method used is not valid for the location specified")
        return True
    logger = logging.getLogger(dir_to_list.replace("\\", "/")[6:] + module_name.replace(".", "/"))
    logger.info(method.upper())
    for i, parameter in enumerate(ids_parameters):
        logger.debug(method.upper() + ": Parameter " + str(i + 1) + ": " + parameter)
    handler.logger = logger
    method_to_do(handler, parameters, url_parameters, *ids_parameters)
    return True


def find_endpoint(method, handler, parameters, url_parameters, ids_parameters, dir_to_list, endpoint):
    """Find the route from endpoint and call the correct method when found"""
    if not endpoint:
        return do_method(method, handler, parameters, url_parameters, ids_parameters, dir_to_list, ".all")
    if "/" not in endpoint:
        next_dir = endpoint
        endpoint = ""
    else:
        [next_dir, endpoint] = endpoint.split("/", 1)
    entries = os.listdir(dir_to_list)
    if next_dir not in entries:
        if next_dir.isdigit():
            ids_parameters.append(next_dir)
            if not endpoint:
                return do_method(method, handler, parameters, url_parameters, ids_parameters, dir_to_list, ".single")
            else:
                return find_endpoint(method, handler, parameters, url_parameters, ids_parameters, dir_to_list, endpoint)
        else:
            return False
    elif os.path.isdir(os.path.join(dir_to_list, next_dir)):
        return find_endpoint(
            method, handler, parameters, url_parameters, ids_parameters, os.path.join(dir_to_list, next_dir), endpoint
        )
    return False


def do_endpoint(method, handler, endpoint, parameters):
    """Parse url parameters and ready up the search of the endpoint"""
    if method != "get":
        token = handler.session.query(Token).where(Token.session_token == handler.session_token).first()
        if token:
            if token.expiry_date < int(time.time()):
                handler.session.delete(token)
                logging.info("Token expired")
                handler.send_error(403, "Not connected")
                return
            elif token.access_token:
                handler.refresh_token(token)
        elif endpoint != "/api/v1/discord/tokens":
            logging.info("No token")
            handler.send_error(403, "Not connected")
            return
    parsed_url = parse.urlparse(endpoint.strip("/"))
    if not find_endpoint(
        method, handler, parameters, parse.parse_qs(parsed_url.query), [], "server/routes", parsed_url.path
    ):
        handler.send_error(404, "The resource at the location specified doesn't exist")
        print("404 error")


def get(handler, endpoint, parameters):
    """GET method"""
    do_endpoint("get", handler, endpoint, None)


def post(handler, endpoint, parameters):
    """POST method"""
    do_endpoint("post", handler, endpoint, parameters)


def put(handler, endpoint, parameters):
    """PUT method"""
    if not parameters:
        handler.logger.debug("Ignoring")
        handler.send_json("{}")
        return
    do_endpoint("put", handler, endpoint, parameters)


def patch(handler, endpoint, parameters):
    """PATCH method"""
    do_endpoint("put", handler, endpoint, parameters)


def delete(handler, endpoint, parameters):
    """DELETE method"""
    do_endpoint("delete", handler, endpoint, None)
