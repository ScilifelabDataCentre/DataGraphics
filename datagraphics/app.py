"Serve data and graphics on the web using Vega-Lite graphics."

import flask

import datagraphics.about
import datagraphics.config
import datagraphics.user
import datagraphics.site
import datagraphics.dataset
import datagraphics.graphic

import datagraphics.api.about
import datagraphics.api.root
import datagraphics.api.schema
import datagraphics.api.user

from datagraphics import constants
from datagraphics import utils

app = flask.Flask(__name__)

# Get the configuration and initialize modules (database).
datagraphics.config.init(app)
utils.init(app)
datagraphics.dataset.init(app)
datagraphics.graphic.init(app)
datagraphics.user.init(app)
utils.mail.init_app(app)


@app.errorhandler(utils.JsonException)
def handle_json_exception(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token)

@app.before_request
def prepare():
    "Open the database connection; get the current user."
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
        return flask.render_template("home.html")

# Set up the URL map.
app.register_blueprint(datagraphics.about.blueprint, url_prefix="/about")
app.register_blueprint(datagraphics.user.blueprint, url_prefix="/user")
app.register_blueprint(datagraphics.site.blueprint, url_prefix="/site")
app.register_blueprint(datagraphics.dataset.blueprint, url_prefix="/dataset")
app.register_blueprint(datagraphics.graphic.blueprint, url_prefix="/graphic")

app.register_blueprint(datagraphics.api.root.blueprint, url_prefix="/api")
app.register_blueprint(datagraphics.api.about.blueprint, 
                       url_prefix="/api/about")
app.register_blueprint(datagraphics.api.schema.blueprint,
                       url_prefix="/api/schema")
app.register_blueprint(datagraphics.api.user.blueprint, url_prefix="/api/user")
# app.register_blueprint(datagraphics.api.dataset.blueprint,
#                        url_prefix="/api/dataset")
# app.register_blueprint(datagraphics.api.graphics.blueprint,
#                        url_prefix="/api/graphics")


# This code is used only during development.
if __name__ == "__main__":
    app.run()
