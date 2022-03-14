"About info HTMl endpoints."

import sys

import certifi
import chardet
import couchdb2
import flask
import jinja2
import jsonschema
import marko
import requests

from datagraphics import constants
from datagraphics import utils


blueprint = flask.Blueprint("about", __name__)


@blueprint.route("/software")
def software():
    "Software version information."
    return flask.render_template("about/software.html", software=get_software())


def get_software():
    v = sys.version_info
    return [
        ("DataGraphics", constants.VERSION, constants.URL),
        ("Python", f"{v.major}.{v.minor}.{v.micro}", "https://www.python.org/"),
        ("Flask", flask.__version__, "http://flask.pocoo.org/"),
        ("certifi", certifi.__version__, "https://pypi.org/project/certifi/"),
        ("chardet", chardet.__version__, "https://pypi.org/project/chardet/"),
        ("CouchDB server", flask.g.db.server.version, "https://couchdb.apache.org/"),
        (
            "CouchDB2 interface",
            couchdb2.__version__,
            "https://pypi.org/project/couchdb2",
        ),
        ("Jinja2", jinja2.__version__, "https://pypi.org/project/Jinja2/"),
        ("jsonschema", jsonschema.__version__, "https://pypi.org/project/jsonschema"),
        ("Marko", marko.__version__, "https://pypi.org/project/marko/"),
        ("requests", requests.__version__, "https://docs.python-requests.org/"),
        ("Bootstrap", constants.BOOTSTRAP_VERSION, constants.BOOTSTRAP_URL),
        ("jQuery", constants.JQUERY_VERSION, constants.JQUERY_URL),
        (
            "jQuery.localtime",
            constants.JQUERY_LOCALTIME_VERSION,
            constants.JQUERY_LOCALTIME_URL,
        ),
        ("DataTables", constants.DATATABLES_VERSION, constants.DATATABLES_URL),
        ("Vega", constants.VEGA_VERSION, constants.VEGA_URL),
        ("Vega-Lite", constants.VEGA_LITE_VERSION, constants.VEGA_LITE_URL),
        ("Vega-Embed", constants.VEGA_EMBED_VERSION, constants.VEGA_EMBED_URL),
    ]


@blueprint.route("/contact")
def contact():
    "Show contact information."
    return flask.render_template("about/contact.html")


@blueprint.route("/settings")
@utils.admin_required
def settings():
    "Show settings, except for sensitive or too complex values."
    config = flask.current_app.config.copy()
    for key in [
        "SECRET_KEY",
        "MAIL_PASSWORD",
        "ADMIN_USER",
        "COUCHDB_PASSWORD",
        "STENCILS",
    ]:
        if config.get(key):
            config[key] = "<hidden>"
    config.pop("VEGA_LITE_SCHEMA", None)
    return flask.render_template("about/settings.html", items=sorted(config.items()))
