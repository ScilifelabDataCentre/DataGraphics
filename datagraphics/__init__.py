"Serve data and graphics on the web using Vega-Lite graphics."

import json
import os.path
import re
import string

__version__ = "0.2.10"

class Constants:
    VERSION     = __version__

    BOOTSTRAP_VERSION  = "4.3.1"
    JQUERY_VERSION     = "3.3.1"
    DATATABLES_VERSION = "1.10.18"

    NAME_RX  = re.compile(r"^[a-z][a-z0-9_-]*$", re.I)
    IUID_RX  = re.compile(r"^[a-f0-9]{32,32}$", re.I)
    EMAIL_RX = re.compile(r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$")

    SLUG_CHARS = frozenset(string.ascii_letters + string.digits + "-")

    # CouchDB document types
    DOCTYPE_DATASET = "dataset"
    DOCTYPE_GRAPHIC = "graphic"
    DOCTYPE_USER    = "user"
    DOCTYPE_LOG     = "log"

    # User roles
    ADMIN = "admin"
    USER  = "user"
    USER_ROLES = (ADMIN, USER)

    # User statuses
    PENDING  = "pending"
    ENABLED  = "enabled"
    DISABLED = "disabled"
    USER_STATUSES = [PENDING, ENABLED, DISABLED]

    # Content types
    HTML_MIMETYPE = "text/html"
    JSON_MIMETYPE = "application/json"
    CSV_MIMETYPE  = "text/csv"
    JS_MIMETYPE   = "text/javascript"

    # JSON Schema; Draft 7 validator is used on the source code.
    JSON_SCHEMA_URL = "http://json-schema.org/draft-07/schema#",

    def __setattr__(self, key, value):
        raise ValueError("cannot set constant")


constants = Constants()
