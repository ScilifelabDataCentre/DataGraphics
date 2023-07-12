"DataGraphics: Serve data and graphics on the web using Vega-Lite graphics."

import flask
import markupsafe
from werkzeug.middleware.proxy_fix import ProxyFix

import datagraphics.about
import datagraphics.config
import datagraphics.dataset
import datagraphics.datasets
import datagraphics.doc
import datagraphics.graphic
import datagraphics.graphics
import datagraphics.user

import datagraphics.api.about
import datagraphics.api.root
import datagraphics.api.dataset
import datagraphics.api.datasets
import datagraphics.api.graphic
import datagraphics.api.graphics
import datagraphics.api.user
import datagraphics.api.users
import datagraphics.api.schema

from datagraphics import constants
from datagraphics import utils


class JsonException(Exception):
    "JSON API error response."

    status_code = 400

    def __init__(self, message, status_code=None, data=None):
        super().__init__()
        self.message = str(message)
        if status_code is not None:
            self.status_code = status_code
        self.data = data

    def to_dict(self):
        result = dict(self.data or ())
        result["status_code"] = self.status_code
        result["message"] = self.message
        return result


# Get the app.
app = datagraphics.config.create_app(__name__)
datagraphics.doc.init(app)

if app.config["REVERSE_PROXY"]:
    app.wsgi_app = ProxyFix(app.wsgi_app)


@app.errorhandler(JsonException)
def handle_json_exception(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(
        constants=constants,
        csrf_token=utils.csrf_token,
        enumerate=enumerate,
        am_admin_or_self=datagraphics.user.am_admin_or_self,
        url_referrer=utils.url_referrer,
    )


@app.before_request
def prepare():
    "Open the database connection; get the current user."
    flask.g.timer = utils.Timer()
    flask.g.db = utils.get_db()
    flask.g.cache = {}  # key: iuid, value: doc
    flask.g.current_user = datagraphics.user.get_current_user()
    flask.g.am_admin = (
        flask.g.current_user and flask.g.current_user["role"] == constants.ADMIN
    )


app.after_request(utils.log_access)


@app.route("/")
def home():
    "Home page. Redirect to API root if JSON is accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for("api_root"))
    else:
        datasets = datagraphics.datasets.get_datasets_public(
            limit=flask.current_app.config["MAX_HOME_LIST_ITEMS"]
        )
        graphics = datagraphics.graphics.get_graphics_public(
            limit=flask.current_app.config["MAX_HOME_LIST_ITEMS"]
        )
        return flask.render_template("home.html", datasets=datasets, graphics=graphics)


@app.route("/debug")
@utils.admin_required
def debug():
    "Return some debug info for admin."
    result = [f"<h1>Debug  {constants.VERSION}</h2>"]
    result.append("<h2>headers</h2>")
    result.append("<table>")
    for key, value in sorted(flask.request.headers.items()):
        result.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
    result.append("</table>")
    result.append("<h2>environ</h2>")
    result.append("<table>")
    for key, value in sorted(flask.request.environ.items()):
        result.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
    result.append("</table>")
    return markupsafe.Markup("\n".join(result))


@app.route("/status")
def status():
    "Return JSON for the current status and some counts for the database."
    return dict(
        status="ok",
        n_datasets=datagraphics.datasets.count_datasets_public(),
        n_graphics=datagraphics.graphics.count_graphics_public(),
    )


@app.route("/sitemap")
def sitemap():
    "Return an XML sitemap."
    pages = [
        dict(
            url=flask.url_for("home", _external=True), changefreq="daily", priority=1.0
        ),
        dict(url=flask.url_for("about.contact", _external=True), changefreq="yearly"),
        dict(
            url=flask.url_for("about.documentation", _external=True),
            changefreq="monthly",
        ),
        dict(url=flask.url_for("about.software", _external=True), changefreq="yearly"),
        dict(
            url=flask.url_for("datasets.public", _external=True),
            changefreq="daily",
            priority=1.0,
        ),
        dict(
            url=flask.url_for("graphics.public", _external=True),
            changefreq="daily",
            priority=1.0,
        ),
    ]
    for dataset in datagraphics.datasets.get_datasets_public():
        pages.append(
            dict(
                url=flask.url_for("dataset.display", iuid=dataset[0], _external=True),
                changefreq="weekly",
            )
        )
    for graphic in datagraphics.graphics.get_graphics_public():
        pages.append(
            dict(
                url=flask.url_for("graphic.display", iuid=graphic[0], _external=True),
                changefreq="weekly",
            )
        )
    xml = flask.render_template("sitemap.xml", pages=pages)
    response = flask.current_app.make_response(xml)
    response.mimetype = constants.XML_MIMETYPE
    return response


# Set up the URL map.
app.register_blueprint(datagraphics.about.blueprint, url_prefix="/about")
app.register_blueprint(datagraphics.user.blueprint, url_prefix="/user")
app.register_blueprint(datagraphics.dataset.blueprint, url_prefix="/dataset")
app.register_blueprint(datagraphics.datasets.blueprint, url_prefix="/datasets")
app.register_blueprint(datagraphics.graphic.blueprint, url_prefix="/graphic")
app.register_blueprint(datagraphics.graphics.blueprint, url_prefix="/graphics")
app.register_blueprint(datagraphics.doc.blueprint, url_prefix="/documentation")

app.register_blueprint(datagraphics.api.root.blueprint, url_prefix="/api")
app.register_blueprint(datagraphics.api.about.blueprint, url_prefix="/api/about")
app.register_blueprint(datagraphics.api.dataset.blueprint, url_prefix="/api/dataset")
app.register_blueprint(datagraphics.api.datasets.blueprint, url_prefix="/api/datasets")
app.register_blueprint(datagraphics.api.graphic.blueprint, url_prefix="/api/graphic")
app.register_blueprint(datagraphics.api.graphics.blueprint, url_prefix="/api/graphics")
app.register_blueprint(datagraphics.api.user.blueprint, url_prefix="/api/user")
app.register_blueprint(datagraphics.api.users.blueprint, url_prefix="/api/users")
app.register_blueprint(datagraphics.api.schema.blueprint, url_prefix="/api/schema")


# This code is used only during development.
if __name__ == "__main__":
    app.run()
