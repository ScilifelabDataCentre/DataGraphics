"About info HTMl endpoints."

import sys

import couchdb2
import flask
import jsonschema

from datagraphics import constants
from datagraphics import utils


blueprint = flask.Blueprint("about", __name__)

@blueprint.route("/software")
def software():
    "Show software versions."
    return flask.render_template("about/software.html",
                                 software=get_software())

def get_software():
    v = sys.version_info
    return sorted([
        ("DataGraphics", constants.VERSION, constants.URL),
        ("Python", f"{v.major}.{v.minor}.{v.micro}", "https://www.python.org/"),
        ("Flask", flask.__version__, "http://flask.pocoo.org/"),
        ("CouchDB server", flask.g.dbserver.version, 
         "https://couchdb.apache.org/"),
        ("CouchDB2 interface", couchdb2.__version__, 
         "https://pypi.org/project/couchdb2"),
        ("jsonschema", jsonschema.__version__, 
         "https://pypi.org/project/jsonschema"),
        ("Bootstrap", constants.BOOTSTRAP_VERSION, constants.BOOTSTRAP_URL),
        ("jQuery", constants.JQUERY_VERSION, constants.JQUERY_URL),
        ("DataTables", constants.DATATABLES_VERSION, constants.DATATABLES_URL),
        ("Vega", constants.VEGA_VERSION, constants.VEGA_URL),
        ("Vega-Lite", constants.VEGA_LITE_VERSION, constants.VEGA_LITE_URL),
        ("Vega-Embed", constants.VEGA_EMBED_VERSION, constants.VEGA_EMBED_URL),
    ], key=lambda t: t[0].lower())

@blueprint.route("/documentation")
@blueprint.route("/documentation/<page>")
def documentation(page=None):
    "Documentation pages."
    if page is None:
        return flask.render_template("documentation/index.html")
    else:
        return flask.render_template(f"documentation/{page}.html")

@blueprint.route("/settings")
@utils.admin_required
def settings():
    "Show settings, except for sensitive or too complex values."
    config = flask.current_app.config.copy()
    for key in ["SECRET_KEY", "MAIL_PASSWORD", 
                "ADMIN_USER", "COUCHDB_PASSWORD"]:
        if config.get(key):
            config[key] = "<hidden>"
    config.pop("VEGA_LITE_SCHEMA", None)
    return flask.render_template("about/settings.html",
                                 items=sorted(config.items()))
@blueprint.route('/schema')
def schema():
    "Page with links to all JSON schema for the API."
    schemas = [
        (flask.url_for("api_schema.root", _external=True), "API Root"),
        (flask.url_for("api_schema.schema", _external=True), "API Schema"),
        (flask.url_for("api_schema.dataset", _external=True), "API Dataset"),
        (flask.url_for("api_schema.datasets", _external=True), "API Datasets"),
        (flask.url_for("api_schema.graphic", _external=True), "API Graphic"),
        (flask.url_for("api_schema.user", _external=True), "API User")]
    return flask.render_template('about/schema.html', schemas=schemas)
