"User display API endpoints."

import http.client

import flask

import datagraphics.user
from datagraphics import utils

blueprint = flask.Blueprint("api_user", __name__)

@blueprint.route("/")
def all():
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    users = [get_user_basic(u) for u in datagraphics.user.get_users()]
    return flask.jsonify(utils.get_json(users=users))

@blueprint.route("/<name:username>")
def display(username):
    user = datagraphics.user.get_user(username=username)
    if not user:
        flask.abort(http.client.NOT_FOUND)
    # XXX Use 'allow' function
    if not datagraphics.user.am_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    user.pop("password", None)
    user.pop("apikey", None)
    user["logs"] = {"href": utils.url_for(".logs", username=user["username"])}
    return flask.jsonify(utils.get_json(**user))

@blueprint.route("/<name:username>/logs")
def logs(username):
    user = datagraphics.user.get_user(username=username)
    if not user:
        flask.abort(http.client.NOT_FOUND)
    # XXX Use 'allow' function
    if not datagraphics.user.am_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    return flask.jsonify(utils.get_json(user=get_user_basic(user),
                                        logs=utils.get_logs(user["_id"])))

def get_user_basic(user):
    "Return the basic JSON data for a user."
    return {"username": user["username"],
            "href": utils.url_for(".display",username=user["username"])}
