"Dataset to display graphic of."

import csv
import io
import json
import http.client
import statistics

import couchdb2
import flask
import requests
import requests.exceptions

import datagraphics.user
from datagraphics import constants
from datagraphics import utils

from datagraphics.saver import EntitySaver

TYPE_NAME_MAP = {int:   "integer",
                 float: "number",
                 bool:  "boolean",
                 str:   "string"}

TYPE_OBJECT_MAP = dict((n, o) for o, n in TYPE_NAME_MAP.items())

def bool2(v):
    "Convert to boolean from CSV string value."
    if v == "True": return True
    if v == "true": return True
    if v == "False": return False
    if v == "false": return False
    if not v: return None
    raise ValueError(f"invalid bool '{v}'")

TYPE_OBJECT_MAP2 = TYPE_OBJECT_MAP.copy()
TYPE_OBJECT_MAP2["boolean"] = bool2

def init(app):
    "Initialize; update CouchDB design document."
    db = utils.get_db(app=app)
    logger = utils.get_logger(app)
    if db.put_design("datasets", DESIGN_DOC):
        logger.info("Updated datasets design document.")

DESIGN_DOC = {
    "views": {
        "public_modified": {"reduce": "_count",
                            "map": "function(doc) {if (doc.doctype !== 'dataset' || !doc.public) return; emit(doc.modified, doc.title);}"},
        "owner_modified": {"reduce": "_count",
                           "map": "function(doc) {if (doc.doctype !== 'dataset') return; emit([doc.owner, doc.modified], doc.title);}"},
        "editor_modified": {"reduce": "_count",
                            "map": "function(doc) {if (doc.doctype !== 'dataset') return; if (!doc.editors) return; for (var i=0; i<doc.editors.length; i++) { emit([doc.editors[i], doc.modified], doc.title);}}"},
        "file_size": {"reduce": "_sum",
                      "map": "function(doc) {if (doc.doctype !== 'dataset' || !doc._attachments) return; for (var key in doc._attachments) if (doc._attachments.hasOwnProperty(key)) emit(doc.owner, doc._attachments[key].length);}"}
    },
}

blueprint = flask.Blueprint("dataset", __name__)

@blueprint.route("/", methods=["GET", "POST"])
@utils.login_required
def create():
    "Create a new dataset, from file or URL."
    if utils.http_GET():
        return flask.render_template("dataset/create.html")

    elif utils.http_POST():
        try:
            with DatasetSaver() as saver:
                saver.set_title()
                saver.set_description()
                saver.set_public(False)
                if not saver.upload_file():
                    saver.get_url_data()
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(utils.url_referrer())
        return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>")
def display(iuid):
    "Display the dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())
    storage = sum([s['length'] 
                   for s in dataset.get('_attachments', {}).values()])
    return flask.render_template("dataset/display.html",
                                 dataset=dataset,
                                 graphics=get_graphics(dataset),
                                 storage=storage,
                                 am_owner=am_owner(dataset),
                                 allow_edit=allow_edit(dataset),
                                 allow_delete=allow_delete(dataset),
                                 possible_delete=possible_delete(dataset),
                                 commands=get_commands(dataset))

@blueprint.route("/<iuid:iuid>/data")
def data(iuid):
    "Display the data contents of the dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())
    outfile = flask.g.db.get_attachment(dataset, "data.json")
    data = json.load(outfile)
    max_records = flask.current_app.config["MAX_RECORDS_INSPECT"]
    if len(data) > max_records:
        data = data[:max_records]
        utils.flash_message(f"Only the first {max_records} records are displayed.")
    return flask.render_template("dataset/data.html",
                                 dataset=dataset,
                                 data=data)

@blueprint.route("/<iuid:iuid>/edit", methods=["GET", "POST", "DELETE"])
@utils.login_required
def edit(iuid):
    "Edit the dataset, or delete it."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())

    if utils.http_GET():
        if not allow_edit(dataset):
            utils.flash_error("Edit access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        return flask.render_template("dataset/edit.html",
                                     am_owner=am_owner(dataset),
                                     dataset=dataset)

    elif utils.http_POST():
        if not allow_edit(dataset):
            utils.flash_error("Edit access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        try:
            with DatasetSaver(dataset) as saver:
                saver.set_title()
                if flask.g.am_admin:
                    saver.change_owner()
                if am_owner(dataset):
                    saver.set_editors()
                saver.set_description()
                saver.upload_file()
                saver.set_vega_lite_types()
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(flask.url_for(".display", iuid=iuid))

    elif utils.http_DELETE():
        if not possible_delete(dataset):
            utils.flash_error("Dataset cannot be deleted; use by graphics.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        if not allow_delete(dataset):
            utils.flash_error("Delete access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        flask.g.db.delete(dataset)
        for log in utils.get_logs(dataset["_id"], cleanup=False):
            flask.g.db.delete(log)
        utils.flash_message("The dataset was deleted.")
        return flask.redirect(flask.url_for("datasets.display"))

@blueprint.route("/<iuid:iuid>/copy", methods=["POST"])
@utils.login_required
def copy(iuid):
    "Copy the dataset, including its data content."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(flask.url_for(".display", iuid=iuid))
    try:
        with DatasetSaver() as saver:
            saver.copy(dataset)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>/copy_graphics", methods=["POST"])
@utils.login_required
def copy_graphics(iuid):
    """Copy the dataset, including its data content, 
    and also all its graphics viewable by the user."""
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(flask.url_for(".display", iuid=iuid))
    try:
        with DatasetSaver() as saver:
            saver.copy(dataset, graphics=True)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>/public", methods=["POST"])
@utils.login_required
def public(iuid):
    "Set the dataset to public access."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if am_owner(dataset):
        if not dataset["public"]:
            with DatasetSaver(dataset) as saver:
                saver.set_public(True)
    else:
        utils.flash_error("Only owner may make dataset public.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>/private", methods=["POST"])
@utils.login_required
def private(iuid):
    "Set the dataset to private access."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if am_owner(dataset):
        if dataset["public"]:
            with DatasetSaver(dataset) as saver:
                saver.set_public(False)
    else:
        utils.flash_error("Only owner may make dataset private.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>.<ext>")
def download(iuid, ext):
    """Download the content of the dataset as JSON or CSV file.
    This is for use in the HTML pages, not for API calls.
    """
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset is not allowed.")
        return flask.redirect(utils.url_referrer())
    if not dataset.get("_attachments", None):
        utils.flash_error("Dataset does not contain any data.")
        return flask.redirect(utils.url_referrer())
    if ext == "json":
        outfile = flask.g.db.get_attachment(dataset, "data.json")
        response = flask.make_response(outfile.read())
        response.headers.set("Content-Type", constants.JSON_MIMETYPE)
    elif ext == "csv":
        outfile = flask.g.db.get_attachment(dataset, "data.csv")
        response = flask.make_response(outfile.read())
        response.headers.set("Content-Type", constants.CSV_MIMETYPE)
    else:
        utils.flash_error("Invalid file type requested.")
        return flask.redirect(utils.url_referrer())
    slug = utils.slugify(dataset['title'])
    response.headers.set("Content-Disposition", "attachment", 
                         filename=f"{slug}.{ext}")
    return response

@blueprint.route("/<iuid:iuid>/logs")
def logs(iuid):
    "Display the log records of the given dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())
    return flask.render_template(
        "logs.html",
        title=f"Dataset {dataset['title'] or 'No title'}",
        back_url=flask.url_for(".display", iuid=iuid),
        logs=utils.get_logs(iuid))


class DatasetSaver(EntitySaver):
    "Dataset saver context with data content handling."

    DOCTYPE = constants.DOCTYPE_DATASET

    def initialize(self):
        super().initialize()
        self.doc["meta"] = {}

    def upload_file(self):
        """Upload a file from a web form and return True.
        If no file given, return False.
        """
        infile = flask.request.files.get("file")
        if not infile: return False
        self.set_data(infile, infile.mimetype)  # Exclude parameters.
        return True

    def get_url_data(self):
        "Get the data from a URL. Just skip if no URL."
        url = flask.request.form.get("url")
        if not url: return
        try:
            response = requests.get(url, timeout=5.0)
        except requests.exceptions.TimeOut:
            raise ValueError("Could not fetch data from URL; timeout.")
        if response.status_code != 200:
            raise ValueError(f"Could not fetch data from URL: {response.status_code}")
        content_type = response.headers.get('content-type')
        if not content_type:
            raise ValueError("Unknown content type for data.")
        content_type = content_type.split(";")[0]
        self.set_data(io.BytesIO(response.content), content_type)

    def set_data(self, infile, content_type):
        "Set the data for this dataset from the input file (CSV or JSON)."
        if content_type == constants.JSON_MIMETYPE:
            data = self.get_json_data(infile)
        elif content_type == constants.CSV_MIMETYPE:
            data = self.get_csv_data(infile)
        elif content_type == constants.EXCEL_MIMETYPE:
            # Microsoft Windows may lie about Content-Type!
            # May claim Excel, when it is actually CSV. Try to read it as CSV.
            if "windows" in str(flask.request.user_agent).lower():
                try:
                    data = self.get_csv_data(infile)
                except ValueError:  # Fails if it really was an Excel file.
                    raise  # TODO: Try Excel here, when and if implemented.
        else:
            raise ValueError(f"Cannot handle content_type {content_type}")
        self.doc["n_records"] = len(data)
        self.update_meta(data)

        # Data in JSON format.
        json_content = json.dumps(data, ensure_ascii=False).encode("utf-8")

        # Data in CSV format.
        outfile = io.StringIO()
        writer = csv.DictWriter(outfile, fieldnames=list(data[0].keys()))
        writer.writeheader()
        for record in data:
            writer.writerow(record)
        outfile.seek(0)
        csv_content = outfile.read().encode("utf-8")

        if flask.g.current_user.get("quota_storage"):
            username = flask.g.current_user["username"]
            total = len(json_content) + len(csv_content) + \
                    datagraphics.user.get_storage(username)
            if total > flask.g.current_user["quota_storage"]:
                raise ValueError(f"File {infile.filename} not added;"
                                 " quota storage reached.")
        self.add_attachment("data.json", json_content, constants.JSON_MIMETYPE)
        self.add_attachment("data.csv", csv_content, constants.CSV_MIMETYPE)

    def get_json_data(self, infile):
        """Return the data in JSON format from the given JSON infile.
        If the dataset is new, then define the 'meta' entry contents by 
        inspection of the data. Also set the Vega-Lite types.
        If the dataset is being updated, check against the 'meta' entry.
        """
        data = json.load(infile)
        if not data:
            raise ValueError("No data in JSON file.")
        if not isinstance(data, list):
            raise ValueError("JSON data does not contain a list.")
        first = data[0]
        if not first:
            raise ValueError("Empty first record in JSON data.")
        if not isinstance(first, dict):
            raise ValueError(f"JSON data record 0 '{first}' is not an object.")

        meta = self.doc["meta"]
        new = not bool(meta)  # New dataset, or being updated?

        if new:
            # Figure out the types from the items in the first data record.
            for key in first:
                meta[key] = {}
            for key, value in first.items():
                try:
                    meta[key]["type"] = TYPE_NAME_MAP[type(value)]
                except KeyError:
                    raise ValueError(f"JSON data item 0 '{first}'"
                                     " contains illegal type")

        # Check data homogeneity. Checks with respect to 'meta'.
        keys = list(meta.keys())
        for pos, record in enumerate(data):
            if not isinstance(record, dict):
                raise ValueError(f"JSON data record {pos} '{record}'"
                                 " is not an object.")
            for key in keys:
                try:
                    value = record[key]
                except KeyError:
                    record[key] = value = None
                if value is not None and \
                   type(value) != TYPE_OBJECT_MAP[meta[key]["type"]]:
                    raise ValueError(f"JSON data record {pos} '{record}'"
                                     " contains wrong type.")

        # Set Vega-Lite types if new dataset.
        if new:
            self.set_initial_vega_lite_types(data)
        return data

    def get_csv_data(self, infile):
        """Return the data in JSON format from the given CSV infile.
        If the dataset is new, then define the 'meta' entry contents by 
        inspection of the data. Also set the Vega-Lite types.
        If the dataset is being updated, check against the 'meta' entry.
        """
        reader = csv.DictReader(io.StringIO(infile.read().decode("utf-8")))
        data = list(reader)
        if not data:
            raise ValueError("No data in CSV file.")

        meta = self.doc["meta"]
        new = not bool(meta)  # New dataset, else being updated.

        if new:
            # Figure out the types from the items in the first data record.
            first = data[0]
            for key in first:
                meta[key] = {}
            for key, value in first.items():
                try:
                    int(value)
                    meta[key]["type"] = "integer"
                except ValueError:
                    try:
                        float(value)
                        meta[key]["type"] = "number"
                    except ValueError:
                        try:
                            bool2(value)
                            meta[key]["type"] = "boolean"
                        except ValueError:
                            meta[key]["type"] = "string"

        # Convert values; check data homogeneity. Checks with respect to 'meta'.
        keys = set(meta.keys())
        for pos, record in enumerate(data, 1):
            for key, value in record.items():
                # Ignore additional columns in new data.
                if key not in keys: continue
                if value:
                    try:
                        record[key] = TYPE_OBJECT_MAP2[meta[key]["type"]](value)
                    except ValueError:
                        # "Not Applicable" means None.
                        if value.lower() in constants.NA_STRINGS:
                            record[key] = None
                        else:
                            raise ValueError(f"CSV data record {pos} '{record}'"
                                             f" '{key}' contains wrong type.")
                elif meta[key]["type"] != "string":
                    # An empty string is a string when type is 'string'.
                    # Otherwise the value is set as None.
                    record[key] = None

        # Set Vega-Lite types if new dataset.
        if new:
            self.set_initial_vega_lite_types(data)
        return data

    def set_initial_vega_lite_types(self, data):
        """Set the Vega-Lite types for the data fields as a function of
        the JSON type, except for string where regexp patterns are checked.
        """
        for key, meta in self.doc["meta"].items():
            if meta["type"] in ("integer", "number"):
                meta["vega_lite_types"] = ["quantitative"]
            elif meta["type"] == "boolean":
                meta["vega_lite_types"] = ["nominal"]
            elif meta["type"] == "string":
                for rx in (constants.YEAR_RX, constants.DATE_RX,
                           constants.DATETIME_RX, constants.TIME_RX):
                    for record in data:
                        if not rx.match(record[key]): break
                    else:
                        meta["vega_lite_types"] = ["temporal"]
                        break
                else:
                    meta["vega_lite_types"] = ["nominal"]

    def update_meta(self, data):
        "Update the 'meta' entry statistics given the data."
        for key, meta in self.doc["meta"].items():
            meta["n_null"] = len([r[key] for r in data if r[key] is None])
            if meta["type"] in ("string", "integer"):
                distinct = set(r[key] for r in data if r[key] is not None)
                meta["n_distinct"] = len(distinct)
                try:
                    meta["min"] = min(distinct)
                except ValueError:
                    meta["min"] = None
                try:
                    meta["max"] = max(distinct)
                except ValueError:
                    meta["max"] = None
            if meta["type"] in ("integer", "number"):
                values = [r[key] for r in data if r[key] is not None]
                try:
                    meta["min"] = min(values)
                except ValueError:
                    meta["min"] = None
                try:
                    meta["max"] = max(values)
                except ValueError:
                    meta["max"] = None
                try:
                    meta["mean"] = statistics.mean(values)
                except statistics.StatisticsError:
                    meta["mean"] = None
                try:
                    meta["median"] = statistics.median(values)
                except statistics.StatisticsError:
                    meta["median"] = None
                try:
                    meta["stdev"] = statistics.stdev(values)
                except statistics.StatisticsError:
                    meta["stdev"] = None

    def set_vega_lite_types(self, orig_meta=None):
        "Set the Vega-Lite types for the data fields."
        for key, meta in self.doc["meta"].items():
            if orig_meta:
                types = orig_meta[key].get("vega_lite_types") or []
            else:
                types = flask.request.form.getlist(f"vega_lite_types_{key}")
            meta["vega_lite_types"] = [t for t in types
                                       if t in constants.VEGA_LITE_TYPES]

    def copy(self, dataset, graphics=False):
        """Copy everything from the given dataset into this.
        If flag is set, also make copies of the graphics for the dataset."""
        self.set_title(f"Copy of {dataset['title']}")
        self.set_editors(dataset.get("editors") or [])
        self.set_description(dataset["description"])
        self.set_public(False)
        self.set_data(flask.g.db.get_attachment(dataset, "data.json"),
                      constants.JSON_MIMETYPE)
        self.set_vega_lite_types(dataset["meta"])
        if graphics:
            import datagraphics.graphic
            for graphic in get_graphics(dataset):
                with datagraphics.graphic.GraphicSaver() as saver:
                    saver.copy(graphic, dataset=self.doc)


# Utility functions

def get_dataset(iuid):
    "Get the dataset given its IUID."
    if not iuid:
        raise ValueError("No IUID given for dataset.")
    try:
        try:
            doc = flask.g.cache[iuid]
        except KeyError:
            doc = flask.g.db[iuid]
    except couchdb2.NotFoundError:
        raise ValueError("No such dataset.")
    if doc.get("doctype") != constants.DOCTYPE_DATASET:
        raise ValueError(f"Database entry {iuid} is not a dataset.")
    flask.g.cache[iuid] = doc
    return doc

def get_graphics(dataset):
    """Get the graphics entities the dataset is used for.
    Exclude those this user is not allowed to view.
    """
    from datagraphics.graphic import allow_view
    result = []
    for row in flask.g.db.view("graphics", "dataset",
                               key=dataset["_id"],
                               include_docs=True):
        if allow_view(row.doc):
            flask.g.cache[row.doc["_id"]] = row.doc
            result.append(row.doc)
    return sorted(result, key=lambda g: g["title"])

def am_owner(dataset):
    "Is the current user the owner of the dataset? Includes admin."
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if flask.g.current_user["username"] == dataset["owner"]: return True
    return False

def allow_view(dataset):
    "Is the current user allowed to view the dataset?"
    if dataset.get("public"): return True
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if flask.g.current_user["username"] == dataset["owner"]: return True
    if flask.g.current_user["username"] in dataset.get("editors", []):
        return True
    return False

def allow_edit(dataset):
    "Is the current user allowed to edit the dataset?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if flask.g.current_user["username"] == dataset["owner"]: return True
    if flask.g.current_user["username"] in dataset.get("editors", []):
        return True
    return False

def allow_delete(dataset):
    "Is the current user allowed to delete the dataset?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if flask.g.current_user["username"] == dataset["owner"]: return True
    return False

def possible_delete(dataset):
    """Is it possible to delete the dataset? 
    Not if there is a graphic owned by the same user.
    """
    for row in flask.g.db.view("graphics", "dataset",
                               key=dataset["_id"],
                               include_docs=True):
        if row.doc["owner"] == dataset["owner"]: return False
    return True

def get_commands(dataset):
    "Get commands and scripts populated with access key and URLs."
    if not flask.g.current_user: return None
    if not allow_edit(dataset): return None
    apikey = flask.g.current_user.get("apikey")
    if not apikey: return None
    put_url = flask.url_for('api_dataset.content', iuid=dataset["_id"], ext='csv', _external=True)
    delete_url = flask.url_for('api_dataset.serve', iuid=dataset["_id"], _external=True)
    return {
        "curl": {
            "title": "curl commands",
            "text": """<strong>curl</strong> is a command-line utility to
transfer data to/from web servers. It is available for most computer operating
systems. See <a target="_blank" href="https://curl.se/">curl.se</a>.""",
            "content": f'curl {put_url} -H "x-apikey: {apikey}"' \
            ' --upload-file path-to-content-file.csv',
            "delete": f'curl {delete_url} -H "x-apikey: {apikey}" -X DELETE'},
        "python": {
            "title": "Python scripts using 'requests'",
            "text": """<strong>requests</strong> is a Python package for HTTP.
It is the <i>de facto</i> standard for Python. It must be downloaded from
<a target="_blank" href="https://pypi.org/project/requests/">PyPi</a>
since it is not part of the built-in Python packages.
See <a target="_blank" href="https://requests.readthedocs.io/en/master/">
Requests: HTTP for Humans</a>.""",
            "content": f"""import requests

url = "{put_url}"
headers = {{"x-apikey": "{apikey}"}}
with open("path-to-content-file.csv", "rb") as infile:
    data = infile.read()

response = requests.put(url, headers=headers, data=data)
print(response.status_code)    # Outputs 204
""",
                "delete": f"""import requests

url = "{delete_url}"
headers = {{"x-apikey": "{apikey}"}}
response = requests.delete(url, headers=headers)
print(response.status_code)    # Outputs 204
"""
        },
        "r": {
            "title": "R scripts",
            "text": """<strong>R</strong> is an open-source package for
statistics and data analysis available for most computer operating systems.
See <a target="_blank" href="https://www.r-project.org/">The R Project for
Statistical Computing</a>. You need to have the 'httr' package installed
for the code below to work:
<code>install.packages("httr", dependencies=TRUE)</code>.
""",
            "content": f"""library("httr")

file_data <- upload_file("path-to-content-file.csv")
PUT("{put_url}",
    body = file_data,
    add_headers("x-apikey"="{apikey}"))
""",
            "delete": f"""library("httr")

DELETE("{delete_url}",
       add_headers("x-apikey"="{apikey}"))
"""
        }
    }
