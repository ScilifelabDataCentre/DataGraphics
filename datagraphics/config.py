"Configuration."

import json
import os
import os.path

import flask

from datagraphics import constants
from datagraphics import utils

# Default configurable values; modified by reading a JSON file in 'init'.
DEFAULT_SETTINGS = dict(
    SERVER_NAME = "127.0.0.1:5005",   # For URL generation.
    SERVER_HOST = "127.0.0.1",        # For app.run()
    SERVER_PORT = "5005",             # For app.run()
    SITE_STATIC_DIRPATH = None,
    DEBUG = False,
    LOG_DEBUG = False,
    LOG_NAME = "datagraphics",
    LOG_FILEPATH = None,
    LOG_ROTATING = 0,           # Number of backup rotated log files, if any.
    LOG_FORMAT = "%(levelname)-10s %(asctime)s %(message)s",
    HOST_LOGO = None,           # Filename, must be in 'SITE_STATIC_DIRPATH'.
    HOST_NAME = None,
    HOST_URL = None,
    CONTACT_EMAIL = None,
    SECRET_KEY = None,          # Must be set in 'settings.json'.
    SALT_LENGTH = 12,
    COUCHDB_URL = "http://127.0.0.1:5984/",
    COUCHDB_USERNAME = None,
    COUCHDB_PASSWORD = None,
    COUCHDB_DBNAME = "datagraphics",
    JSON_AS_ASCII = False,
    JSON_SORT_KEYS = False,
    JSONIFY_PRETTYPRINT_REGULAR = False,
    MAX_RECORDS_INSPECT = 2000,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # in seconds: 1 week
    MAX_HOME_LIST_ITEMS = 10,
    MAIL_SERVER = None,         # e.g. "localhost", if set up.
    MAIL_PORT = 25,
    MAIL_USE_TLS = False,
    MAIL_USERNAME = None,
    MAIL_PASSWORD = None,
    MAIL_DEFAULT_SENDER = None,
    USER_REGISTER = True,
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # List of regexp's
    ADMIN_USER = {},                  # Keys: username, email, password
)

def init(app):
    """Perform the configuration of the Flask app.
    Set the defaults, and then read JSON settings file.
    Check the environment for a specific set of variables and use if defined.
    """
    # Set the defaults specified above.
    app.config.from_mapping(DEFAULT_SETTINGS)
    # Modify the configuration from a JSON settings file.
    try:
        filepaths = [os.environ["SETTINGS_FILEPATH"]]
    except KeyError:
        filepaths = []
    for filepath in ["settings.json", "../site/settings.json"]:
        filepaths.append(os.path.normpath(os.path.join(constants.ROOT_DIRPATH,
                                                       filepath)))
    for filepath in filepaths:
        try:
            app.config.from_file(filepath, load=json.load)
        except FileNotFoundError:
            pass
        else:
            app.config["SETTINGS_FILE"] = filepath
            break

    # Modify the configuration from environment variables.
    for key, convert in [("DEBUG", utils.to_bool),
                         ("SECRET_KEY", str),
                         ("COUCHDB_URL", str),
                         ("COUCHDB_USERNAME", str),
                         ("COUCHDB_PASSWORD", str),
                         ("MAIL_SERVER", str),
                         ("MAIL_USE_TLS", utils.to_bool),
                         ("MAIL_USERNAME", str),
                         ("MAIL_PASSWORD", str),
                         ("MAIL_DEFAULT_SENDER", str)]:
        try:
            app.config[key] = convert(os.environ[key])
        except (KeyError, TypeError, ValueError):
            pass

    # Sanity check; should not execute if this fails.
    assert app.config["SECRET_KEY"]
    assert app.config["SALT_LENGTH"] > 6
    assert app.config["MIN_PASSWORD_LENGTH"] > 4

    # Read in JSON Schema for Vega-Lite from file in 'static'.
    filepath = os.path.join(constants.ROOT_DIRPATH,
                            f"static/v{constants.VEGA_LITE_VERSION}.json")
    with open(filepath) as infile:
        app.config["VEGA_LITE_SCHEMA"] = json.load(infile)

    # Read in stencil JSON specifications from files in 'stencils'.
    app.config["STENCILS"] = {}
    for rootpath in ["stencils", "../site/stencils"]:
        rootpath = os.path.normpath(os.path.join(constants.ROOT_DIRPATH,
                                                 rootpath))
        if not os.path.exists(rootpath) or not os.path.isdir(rootpath): continue
        for filename in os.listdir(rootpath):
            name, ext = os.path.splitext(filename)
            if ext != ".json": continue
            with open(os.path.join(rootpath, filename)) as infile:
                stencil = json.load(infile)
                stencil["header"]["name"] = name
                for variable in stencil["header"]["variables"]:
                    variable["name"] = "/".join(variable["path"])
                app.config["STENCILS"][name] = stencil
