"DataGraphics: Serve data and graphics on the web using Vega-Lite graphics."

import re
import os.path
import string

__version__ = "0.13.1"


class Constants:
    VERSION = __version__
    URL = "https://github.com/pekrau/DataGraphics"
    ROOT = os.path.dirname(os.path.abspath(__file__))

    BOOTSTRAP_VERSION = "4.6.1"
    BOOTSTRAP_URL = "https://getbootstrap.com/"
    BOOTSTRAP_CSS_URL = (
        "https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/css/bootstrap.min.css"
    )
    BOOTSTRAP_CSS_INTEGRITY = (
        "sha384-zCbKRCUGaJDkqS1kPbPd7TveP5iyJE0EjAuZQTgFLD2ylzuqKfdKlfG/eSrtxUkn"
    )
    BOOTSTRAP_JS_URL = (
        "https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/js/bootstrap.bundle.min.js"
    )
    BOOTSTRAP_JS_INTEGRITY = (
        "sha384-fQybjgWLrvvRgtW6bFlB7jaZrFsaBXjsOMm/tB9LTS58ONXgqbR9W8oWht/amnpF"
    )

    JQUERY_VERSION = "3.5.1"
    JQUERY_URL = "https://jquery.com/"
    JQUERY_JS_URL = "https://code.jquery.com/jquery-3.5.1.slim.min.js"
    JQUERY_JS_INTEGRITY = (
        "sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj"
    )

    JQUERY_LOCALTIME_URL = "https://plugins.jquery.com/jquery.localtime/"
    JQUERY_LOCALTIME_VERSION = "0.9.1"
    JQUERY_LOCALTIME_FILENAME = "jquery.localtime-0.9.1.min.js"

    DATATABLES_VERSION = "1.10.24"
    DATATABLES_URL = "https://datatables.net/"
    DATATABLES_CSS_URL = (
        "https://cdn.datatables.net/1.10.24/css/dataTables.bootstrap4.min.css"
    )
    DATATABLES_JQUERY_JS_URL = (
        "https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js"
    )
    DATATABLES_BOOTSTRAP_JS_URL = (
        "https://cdn.datatables.net/1.10.24/js/dataTables.bootstrap4.min.js"
    )

    VEGA_URL = "https://vega.github.io/vega/"
    VEGA_VERSION = "5.19.1"

    VEGA_LITE_URL = "https://vega.github.io/vega-lite/"
    VEGA_LITE_VERSION = "5.0.0"  # Must match schema file in 'static'.
    VEGA_LITE_SCHEMA_URL = "https://vega.github.io/schema/vega-lite/v5.json"
    VEGA_EMBED_VERSION = "6.15.1"
    VEGA_EMBED_URL = "https://github.com/vega/vega-embed"
    VEGA_LITE_TYPES = ("quantitative", "temporal", "ordinal", "nominal", "geojson")

    # Patterns
    IUID_RX = re.compile(r"^[a-f0-9]{32,32}$")
    NAME_RX = re.compile(r"^[a-z][a-z0-9_-]*$", re.I)
    EMAIL_RX = re.compile(r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$")
    YEAR_RX = re.compile(r"^[1-9]\d\d\d$", re.ASCII)
    DATE_RX = re.compile(r"^[1-9]\d\d\d-\d\d-\d\d$", re.ASCII)
    DATETIME_RX = re.compile(r"^[1-9]\d\d\d-\d\d-\d\d \d\d:\d\d(:\d\d)?$", re.ASCII)
    TIME_RX = re.compile(r"^\d\d:\d\d(:\d\d)?$", re.ASCII)

    NA_STRINGS = {"na", "n/a"}
    SLUG_CHARS = frozenset(string.ascii_letters + string.digits + "-")

    # CouchDB document types
    DOCTYPE_DATASET = "dataset"
    DOCTYPE_GRAPHIC = "graphic"
    DOCTYPE_USER = "user"
    DOCTYPE_LOG = "log"

    # User roles
    ADMIN = "admin"
    USER = "user"
    USER_ROLES = (ADMIN, USER)

    # User statuses
    PENDING = "pending"
    ENABLED = "enabled"
    DISABLED = "disabled"
    USER_STATUSES = (PENDING, ENABLED, DISABLED)

    # Content types
    HTML_MIMETYPE = "text/html"
    JSON_MIMETYPE = "application/json"
    CSV_MIMETYPE = "text/csv"
    JS_MIMETYPE = "text/javascript"
    EXCEL_MIMETYPE = "application/vnd.ms-excel"
    XML_MIMETYPE = "text/xml"

    # JSON Schema; Draft 7 validator is currently hardwired.
    JSON_SCHEMA_URL = "http://json-schema.org/draft-07/schema#"

    # Miscellaneous.
    FRONT_MATTER_RX = re.compile(r"^---(.*)---", re.DOTALL | re.MULTILINE)


    def __setattr__(self, key, value):
        raise ValueError("cannot set constant")


constants = Constants()
