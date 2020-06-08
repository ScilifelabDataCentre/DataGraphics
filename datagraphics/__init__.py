"Serve data and graphics on the web using Vega-Lite graphics."

import json
import os.path
import re
import string

__version__ = "0.3.28"

class Constants:
    VERSION = __version__
    URL     = "https://github.com/pekrau/DataGraphics"

    # Currently, these are hardwired; configurability is not meaningful.
    BOOTSTRAP_VERSION    = "4.3.1"
    BOOTSTRAP_URL        = "https://getbootstrap.com/"
    JQUERY_VERSION       = "3.3.1"
    JQUERY_URL           = "https://jquery.com/"
    DATATABLES_VERSION   = "1.10.18"
    DATATABLES_URL       = "https://datatables.net/"
    VEGA_VERSION         = "5.12.1"
    VEGA_URL             = "https://vega.github.io/vega/"
    VEGA_LITE_VERSION    = "4.12.2"  # Must match file in 'static'!
    VEGA_LITE_URL        = "https://vega.github.io/vega-lite/"
    VEGA_LITE_SCHEMA_URL = "https://vega.github.io/schema/vega-lite/v4.json"
    VEGA_EMBED_VERSION   = "6.8.0"
    VEGA_EMBED_URL       = "https://github.com/vega/vega-embed"

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

    # JSON Schema; Draft 7 validator is currently hardwired.
    JSON_SCHEMA_URL = "http://json-schema.org/draft-07/schema#",

    def __setattr__(self, key, value):
        raise ValueError("cannot set constant")


constants = Constants()
