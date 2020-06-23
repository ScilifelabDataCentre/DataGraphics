"Serve data and graphics on the web using Vega-Lite graphics."

import flask
import jinja2.utils

import datagraphics.about
import datagraphics.config
import datagraphics.user
import datagraphics.site
import datagraphics.dataset
import datagraphics.datasets
import datagraphics.graphic
import datagraphics.graphics

import datagraphics.api.about
import datagraphics.api.root
import datagraphics.api.dataset
import datagraphics.api.datasets
import datagraphics.api.graphic
import datagraphics.api.graphics
import datagraphics.api.user

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


app = flask.Flask(__name__)

# Get the configuration and initialize modules (database).
datagraphics.config.init(app)
utils.init(app)
datagraphics.dataset.init(app)
datagraphics.graphic.init(app)
datagraphics.user.init(app)
utils.mail.init_app(app)

@app.errorhandler(JsonException)
def handle_json_exception(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                am_admin_or_self=datagraphics.user.am_admin_or_self,
                url_referrer=utils.url_referrer)

@app.before_request
def prepare():
    "Open the database connection; get the current user."
    flask.g.timer = utils.Timer()
    flask.g.dbserver = utils.get_dbserver()
    flask.g.db = utils.get_db(dbserver=flask.g.dbserver)
    flask.g.cache = {}          # key: iuid, value: doc
    flask.g.current_user = datagraphics.user.get_current_user()
    flask.g.am_admin = flask.g.current_user and \
                       flask.g.current_user["role"] == constants.ADMIN

app.after_request(utils.log_access)

@app.route("/")
def home():
    "Home page. Redirect to API root if JSON is accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for("api_root"))
    else:
        datasets = datagraphics.datasets.get_datasets_public(
            limit=flask.current_app.config["MAX_HOME_LIST_ITEMS"])
        graphics = datagraphics.graphics.get_graphics_public(
            limit=flask.current_app.config["MAX_HOME_LIST_ITEMS"])
        return flask.render_template("home.html",
                                     datasets=datasets,
                                     graphics=graphics)

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
    return jinja2.utils.Markup("\n".join(result))


# Set up the URL map.
app.register_blueprint(datagraphics.about.blueprint, url_prefix="/about")
app.register_blueprint(datagraphics.user.blueprint, url_prefix="/user")
app.register_blueprint(datagraphics.site.blueprint, url_prefix="/site")
app.register_blueprint(datagraphics.dataset.blueprint, url_prefix="/dataset")
app.register_blueprint(datagraphics.datasets.blueprint, url_prefix="/datasets")
app.register_blueprint(datagraphics.graphic.blueprint, url_prefix="/graphic")
app.register_blueprint(datagraphics.graphics.blueprint, url_prefix="/graphics")

app.register_blueprint(datagraphics.api.root.blueprint,
                       url_prefix="/api")
app.register_blueprint(datagraphics.api.about.blueprint, 
                       url_prefix="/api/about")
app.register_blueprint(datagraphics.api.dataset.blueprint,
                       url_prefix="/api/dataset")
app.register_blueprint(datagraphics.api.datasets.blueprint,
                       url_prefix="/api/datasets")
app.register_blueprint(datagraphics.api.graphic.blueprint,
                       url_prefix="/api/graphic")
app.register_blueprint(datagraphics.api.graphics.blueprint,
                       url_prefix="/api/graphics")
app.register_blueprint(datagraphics.api.user.blueprint,
                       url_prefix="/api/user")


# This code is used only during development.
if __name__ == "__main__":
    app.run(host=app.config["SERVER_HOST"],
            port=app.config["SERVER_PORT"])
