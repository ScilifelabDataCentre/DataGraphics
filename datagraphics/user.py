"User display, register, login/logout, etc endpoints."

import http.client
import json
import re

import flask
import flask_mail
import werkzeug.security

from datagraphics import constants
from datagraphics import utils
from datagraphics.saver import BaseSaver

def init(app):
    """Initialize; update CouchDB design document.
    Create the admin user specified in the settings file, if any.
    """
    db = utils.get_db(app=app)
    logger = utils.get_logger(app)
    if db.put_design("users", DESIGN_DOC):
        logger.info("Updated users design document.")
    if app.config["ADMIN_USER"]:
        with app.app_context():
            flask.g.db = db
            user = get_user(username=app.config["ADMIN_USER"]["username"])
            if user is None:
                try:
                    with UserSaver() as saver:
                        saver.set_username(app.config["ADMIN_USER"]["username"])
                        saver.set_email(app.config["ADMIN_USER"]["email"])
                        saver.set_role(constants.ADMIN)
                        saver.set_status(constants.ENABLED)
                        saver.set_password(app.config["ADMIN_USER"]["password"])
                    logger.info("Created admin user " +
                                app.config["ADMIN_USER"]["username"])
                except ValueError as error:
                    logger.error("Could not create admin user; misconfiguration.")
            else:
                logger.info(f"Admin user {app.config['ADMIN_USER']['username']}"
                            " already exists.")

DESIGN_DOC = {
    "views": {
        "username": {"map": "function(doc) {if (doc.doctype !== 'user') return; emit(doc.username, null);}"},
        "email": {"map": "function(doc) {if (doc.doctype !== 'user') return;  emit(doc.email, null);}"},
        "apikey": {"map": "function(doc) {if (doc.doctype !== 'user') return;  emit(doc.apikey, null);}"},
        "role": {"map": "function(doc) {if (doc.doctype !== 'user') return;  emit(doc.role, null);}"},
    },
}

blueprint = flask.Blueprint("user", __name__)

@blueprint.route("/login", methods=["GET", "POST"])
def login():
    "Login to a user account."
    if utils.http_GET():
        return flask.render_template("user/login.html",
                                     next=flask.request.args.get("next"))
    if utils.http_POST():
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        try:
            if username and password:
                do_login(username, password)
            else:
                raise ValueError
            try:
                next = flask.request.form["next"]
            except KeyError:
                return flask.redirect(flask.url_for("home"))
            else:
                return flask.redirect(next)
        except ValueError:
            utils.flash_error("Invalid user or password, or account disabled.")
            return flask.redirect(flask.url_for(".login"))

@blueprint.route("/logout", methods=["POST"])
def logout():
    "Logout from the user account."
    username = flask.session.pop("username", None)
    if username:
        utils.get_logger().info(f"logged out {username}")
    return flask.redirect(flask.url_for("home"))

@blueprint.route("/register", methods=["GET", "POST"])
def register():
    "Register a new user account."
    if utils.http_GET():
        return flask.render_template("user/register.html")

    elif utils.http_POST():
        try:
            with UserSaver() as saver:
                saver.set_username(flask.request.form.get("username"))
                saver.set_email(flask.request.form.get("email"))
                saver.set_role(constants.USER)
                if flask.g.am_admin:
                    saver.set_password(flask.request.form.get("password") or None)
                    saver.set_status(constants.ENABLED)
                else:
                    saver.set_password()
            user = saver.doc
        except ValueError as error:
            utils.flash_error(error)
            return flask.redirect(flask.url_for(".register"))
        utils.get_logger().info(f"registered user {user['username']}")
        if user["status"] == constants.ENABLED:
            # Directly enabled; send code to the user.
            if user["password"][:5] == "code:":
                send_password_code(user, "registration")
                utils.get_logger().info(f"enabled user {user['username']}")
                utils.flash_message("User account created; check your email.")
            # Directly enabled and password set. No email to anyone.
            else:
                utils.get_logger().info(f"enabled user {user['username']}"
                                        " and set password")
                utils.flash_message("User account created and password set.")
        # Was set to 'pending'; send email to admins.
        else:
            admins = get_users(constants.ADMIN, status=constants.ENABLED)
            emails = [u["email"] for u in admins]
            site = flask.current_app.config["SITE_NAME"]
            message = flask_mail.Message(f"{site} user account pending",
                                         recipients=emails)
            url = flask.url_for(".display", username=user["username"],
                                _external=True)
            message.body = f"To enable the user account, go to {url}"
            utils.mail.send(message)
            utils.get_logger().info(f"pending user {user['username']}")
            utils.flash_message("User account created; an email will be sent"
                                " when it has been enabled by the admin.")
        return flask.redirect(flask.url_for("home"))

@blueprint.route("/reset", methods=["GET", "POST"])
def reset():
    "Reset the password for a user account and send email."
    if utils.http_GET():
        email = flask.request.args.get("email") or ""
        email = email.lower()
        return flask.render_template("user/reset.html", email=email)

    elif utils.http_POST():
        try:
            user = get_user(email=flask.request.form["email"])
            if user is None: raise KeyError
            if user["status"] != constants.ENABLED: raise KeyError
        except KeyError:
            pass
        else:
            with UserSaver(user) as saver:
                saver.set_password()
            send_password_code(user, "password reset")
        utils.get_logger().info(f"reset user {user['username']}")
        utils.flash_message("An email has been sent if the user account exists.")
        return flask.redirect(flask.url_for("home"))

@blueprint.route("/password", methods=["GET", "POST"])
def password():
    "Set the password for a user account, and login user."
    if utils.http_GET():
        return flask.render_template(
            "user/password.html",
            username=flask.request.args.get("username"),
            code=flask.request.args.get("code"))

    elif utils.http_POST():
        try:
            username = flask.request.form.get("username") or ""
            code = flask.request.form.get("code") or ""
            if not username:
                raise ValueError("No such user or wrong code.")
            user = get_user(username=username)
            if user is None:
                raise ValueError("No such user or wrong code.")
            if user["password"] != f"code:{code}":
                raise ValueError("No such user or wrong code.")
            password = flask.request.form.get("password") or ""
            if len(password) < flask.current_app.config["MIN_PASSWORD_LENGTH"]:
                raise ValueError("Too short password.")
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(flask.url_for(".password",
                                                username=username,
                                                code=code))
        else:
            with UserSaver(user) as saver:
                saver.set_password(password)
            utils.get_logger().info(f"password user {user['username']}")
            do_login(username, password)
        return flask.redirect(flask.url_for("home"))

@blueprint.route("/display/<name:username>")
@utils.login_required
def display(username):
    "Display the given user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    if not am_admin_or_self(user):
        utils.flash_error("Access not allowed.")
        return flask.redirect(flask.url_for("home"))
    user["count"] = {"datasets": count_user_datasets(user),
                     "graphics": count_user_graphics(user)}
    return flask.render_template("user/display.html", user=user)

@blueprint.route("/display/<name:username>/edit",
                 methods=["GET", "POST", "DELETE"])
@utils.login_required
def edit(username):
    "Edit the user display. Or delete the user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    if not am_admin_or_self(user):
        utils.flash_error("Access not allowed.")
        return flask.redirect(flask.url_for("home"))

    if utils.http_GET():
        return flask.render_template("user/edit.html",
                                     user=user,
                                     deletable=is_empty(user))

    elif utils.http_POST():
        with UserSaver(user) as saver:
            if flask.g.am_admin:
                email = flask.request.form.get("email")
                if email != user["email"]:
                    saver.set_email(email)
            if am_admin_and_not_self(user):
                saver.set_role(flask.request.form.get("role"))
            if flask.request.form.get("apikey"):
                saver.set_apikey()
        return flask.redirect(
            flask.url_for(".display", username=user["username"]))

    elif utils.http_DELETE():
        if not is_empty(user):
            utils.flash_error("Cannot delete non-empty user account.")
            return flask.redirect(flask.url_for(".display", username=username))
        for log in utils.get_logs(user["_id"], cleanup=False):
            flask.g.db.delete(log)
        flask.g.db.delete(user)
        utils.flash_message(f"Deleted user {username}.")
        utils.get_logger().info(f"deleted user {username}")
        if flask.g.am_admin:
            return flask.redirect(flask.url_for(".all"))
        else:
            return flask.redirect(flask.url_for("home"))

@blueprint.route("/display/<name:username>/logs")
@utils.login_required
def logs(username):
    "Display the log records of the given user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    if not am_admin_or_self(user):
        utils.flash_error("Access not allowed.")
        return flask.redirect(flask.url_for("home"))
    return flask.render_template(
        "logs.html",
        title=f"User {user['username']}",
        cancel_url=flask.url_for(".display", username=user["username"]),
        api_logs_url=flask.url_for("api_user.logs", username=user["username"]),
        logs=utils.get_logs(user["_id"]))

@blueprint.route("/all")
@utils.admin_required
def all():
    "Display list of all users."
    return flask.render_template("user/all.html", users=get_users())

@blueprint.route("/enable/<name:username>", methods=["POST"])
@utils.admin_required
def enable(username):
    "Enable the given user account."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    with UserSaver(user) as saver:
        saver.set_status(constants.ENABLED)
        saver.set_password()
    send_password_code(user, "enabled")
    utils.get_logger().info(f"enabled user {username}")
    return flask.redirect(flask.url_for(".display", username=username))

@blueprint.route("/disable/<name:username>", methods=["POST"])
@utils.admin_required
def disable(username):
    "Disable the given user account."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    with UserSaver(user) as saver:
        saver.set_status(constants.DISABLED)
    utils.get_logger().info(f"disabled user {username}")
    return flask.redirect(flask.url_for(".display", username=username))


class UserSaver(BaseSaver):
    "User document saver context."

    DOCTYPE = constants.DOCTYPE_USER
    HIDDEN_FIELDS = ["password"]

    def initialize(self):
        "Set the status for a new user."
        if flask.current_app.config["USER_ENABLE_IMMEDIATELY"]:
            self.doc["status"] = constants.ENABLED
        else:
            self.doc["status"] = constants.PENDING

    def finalize(self):
        "Check that required fields have been set."
        for key in ["username", "email", "role", "status"]:
            if not self.doc.get(key):
                raise ValueError("invalid user: %s not set" % key)

    def set_username(self, username):
        if "username" in self.doc:
            raise ValueError("username cannot be changed")
        if not constants.NAME_RX.match(username):
            raise ValueError("invalid username; must be a name")
        if get_user(username=username):
            raise ValueError("username already in use")
        self.doc["username"] = username

    def set_email(self, email):
        email = email.lower()
        if not constants.EMAIL_RX.match(email):
            raise ValueError("invalid email")
        if get_user(email=email):
            raise ValueError("email already in use")
        self.doc["email"] = email
        if self.doc.get("status") == constants.PENDING:
            for rx in flask.current_app.config["USER_ENABLE_EMAIL_WHITELIST"]:
                if re.match(rx, email):
                    self.set_status(constants.ENABLED)
                    break

    def set_status(self, status):
        if status not in constants.USER_STATUSES:
            raise ValueError("invalid status")
        self.doc["status"] = status

    def set_role(self, role):
        if role not in constants.USER_ROLES:
            raise ValueError("invalid role")
        self.doc["role"] = role

    def set_password(self, password=None):
        "Set the password; a one-time code if no password provided."
        config = flask.current_app.config
        if password is None:
            self.doc["password"] = "code:%s" % utils.get_iuid()
        else:
            if len(password) < config["MIN_PASSWORD_LENGTH"]:
                raise ValueError("password too short")
            self.doc["password"] = werkzeug.security.generate_password_hash(
                password, salt_length=config["SALT_LENGTH"])

    def set_apikey(self):
        "Set a new API key."
        self.doc["apikey"] = utils.get_iuid()


# Utility functions

def get_user(username=None, email=None, apikey=None):
    """Return the user for the given username, email or apikey.
    Return None if no such user.
    """
    if username:
        rows = flask.g.db.view("users", "username", 
                               key=username, include_docs=True)
    elif email:
        rows = flask.g.db.view("users", "email",
                               key=email.lower(), include_docs=True)
    elif apikey:
        rows = flask.g.db.view("users", "apikey", 
                               key=apikey, include_docs=True)
    else:
        return None
    if len(rows) == 1:
        return rows[0].doc
    else:
        return None

def get_users(role=None, status=None):
    "Get the users optionally specified by role and status."
    assert role is None or role in constants.USER_ROLES
    assert status is None or status in constants.USER_STATUSES
    if role is None:
        result = [r.doc for r in 
                  flask.g.db.view("users", "role", include_docs=True)]
    else:
        result = [r.doc for r in 
                  flask.g.db.view("users", "role", key=role, include_docs=True)]
    if status is not None:
        result = [d for d in result if d["status"] == status]
    for user in result:
        user["count"] = {"datasets": count_user_datasets(user),
                         "graphics": count_user_graphics(user)}
        user["storage"] = get_storage(user["username"])
    return result

def get_current_user():
    """Return the user for the current session.
    Return None if no such user, or disabled.
    """
    user = get_user(username=flask.session.get("username"),
                    apikey=flask.request.headers.get("x-apikey"))
    if user is None or user["status"] != constants.ENABLED:
        flask.session.pop("username", None)
        return None
    return user

def do_login(username, password):
    """Set the session cookie if successful login.
    Raise ValueError if some problem.
    """
    user = get_user(username=username)
    if user is None: raise ValueError
    if not werkzeug.security.check_password_hash(user["password"], password):
        raise ValueError
    if user["status"] != constants.ENABLED:
        raise ValueError
    flask.session["username"] = user["username"]
    flask.session.permanent = True
    utils.get_logger().info(f"logged in {user['username']}")

def send_password_code(user, action):
    "Send an email with the one-time code to the user's email address."
    site = flask.current_app.config["SITE_NAME"]
    message = flask_mail.Message(f"{site} user account {action}",
                                 recipients=[user["email"]])
    url = flask.url_for(".password",
                        username=user["username"],
                        code=user["password"][len("code:"):],
                        _external=True)
    message.body = f"To set your password, go to {url}"
    utils.mail.send(message)

def is_empty(user):
    "Is the given user account empty? No data associated with it."
    return not get_user_datasets(user) and not get_user_graphics(user)

def am_admin_or_self(user=None, username=None):
    "Is the current user admin, or the same as the given user?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if user is not None:
        username = user["username"]
    return flask.g.current_user["username"] == username

def am_admin_and_not_self(user):
    "Is the current user admin, but not the same as the given user?"
    if flask.g.am_admin:
        return flask.g.current_user["username"] != user["username"]
    return False

def get_user_datasets(user):
    "Get the datasets owned by the user."
    result = []
    for row in flask.g.db.view("datasets", "owner_modified",
                               startkey=[user["username"]],
                               endkey=[user["username"], "ZZZZZZ"],
                               include_docs=True):
        flask.g.cache[row.doc["_id"]] = row.doc
        result.append(row.doc)
    return result

def count_user_datasets(user):
    "Return the number of datasets owned by the user."
    rows = list(flask.g.db.view("datasets", "owner_modified",
                                startkey=[user["username"]],
                                endkey=[user["username"], "ZZZZZZ"],
                                reduce=True))
    if rows:
        return rows[0].value
    else:
        return 0
    
def get_user_graphics(user):
    "Get the graphics owned by the user."
    result = []
    for row in flask.g.db.view("graphics", "owner_modified",
                               startkey=[user["username"]],
                               endkey=[user["username"], "ZZZZZZ"],
                               include_docs=True):
        flask.g.cache[row.doc["_id"]] = row.doc
        result.append(row.doc)
    return result
    
def count_user_graphics(user):
    "Return the number of datasets owned by the user."
    rows = list(flask.g.db.view("graphics", "owner_modified",
                                startkey=[user["username"]],
                                endkey=[user["username"], "ZZZZZZ"],
                                reduce=True))
    if rows:
        return rows[0].value
    else:
        return 0
    
def get_storage(username):
    "Return the sum of attachments file sizes for the given user."
    rows = list(flask.g.db.view("datasets", "file_size",
                                key=username,
                                reduce=True,
                                group_level=1))
    if rows:
        return rows[0].value
    else:
        return 0
