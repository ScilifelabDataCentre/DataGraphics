"Base document saver context classes."

import base64
import copy
import hashlib

import flask

from datagraphics import constants
from datagraphics import utils

import datagraphics.user


class BaseSaver:
    "Base document saver context."

    DOCTYPE = None
    HIDDEN_FIELDS = []

    def __init__(self, doc=None):
        if doc is None:
            self.original = {}
            self.doc = {"_id": utils.get_iuid(),
                        "created": utils.get_time()}
            self.initialize()
        else:
            self.original = copy.deepcopy(doc)
            self.doc = doc
        self.prepare()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        self.finish()
        self.doc["doctype"] = self.DOCTYPE
        self.doc["modified"] = utils.get_time()
        flask.g.db.put(self.doc)
        self.wrapup()
        self.add_log()

    def __getitem__(self, key):
        return self.doc[key]

    def __setitem__(self, key, value):
        self.doc[key] = value

    def initialize(self):
        "Initialize the new document."
        pass

    def prepare(self):
        "Preparations before making any changes."
        pass

    def finish(self):
        "Final changes and checks on the document before storing it."
        pass

    def wrapup(self):
        """Wrap up the save operation by performing actions that
        must be done after the document has been stored.
        """
        pass

    def add_log(self):
        """Add a log entry recording the the difference betweens the current and
        the original document, hiding values of specified keys.
        'added': list of keys for items added in the current.
        'updated': dictionary of items updated; original values.
        'removed': dictionary of items removed; original values.
        """
        added = list(set(self.doc).difference(self.original or {}))
        updated = dict([(k, self.original[k])
                        for k in set(self.doc).intersection(self.original or {})
                        if self.doc[k] != self.original[k]])
        removed = dict([(k, self.original[k])
                        for k in set(self.original or {}).difference(self.doc)])
        for key in ["_id", "_rev", "modified"]:
            try:
                added.remove(key)
            except ValueError:
                pass
        updated.pop("_rev", None)
        updated.pop("modified", None)
        for key in self.HIDDEN_FIELDS:
            if key in updated:
                updated[key] = "***"
            if key in removed:
                removed[key] = "***"
        entry = {"_id": utils.get_iuid(),
                 "doctype": constants.DOCTYPE_LOG,
                 "docid": self.doc["_id"],
                 "added": added,
                 "updated": updated,
                 "removed": removed,
                 "timestamp": utils.get_time()}
        entry.update(self.add_log_items())
        if hasattr(flask.g, "current_user") and flask.g.current_user:
            entry["username"] = flask.g.current_user["username"]
        else:
            entry["username"] = None
        if flask.has_request_context():
            entry["remote_addr"] = str(flask.request.remote_addr)
            entry["user_agent"] = str(flask.request.user_agent)
        else:
            entry["remote_addr"] = None
            entry["user_agent"] = None
        flask.g.db.put(entry)

    def add_log_items(self):
        "Return a dictionary of additional items to add to the log entry."
        return {}


class AttachmentsSaver(BaseSaver):
    "Document saver context handling attachments."

    def prepare(self):
        self._delete_attachments = set()
        self._add_attachments = []

    def wrapup(self):
        """Delete any specified attachments.
        Store the input files as attachments.
        Must be done after document is saved.
        """
        for filename in self._delete_attachments:
            rev = flask.g.db.delete_attachment(self.doc, filename)
            self.doc["_rev"] = rev
        for attachment in self._add_attachments:
            flask.g.db.put_attachment(self.doc,
                                      attachment["content"],
                                      filename=attachment["filename"],
                                      content_type=attachment["mimetype"])

    def add_attachment(self, filename, content, mimetype):
        self._add_attachments.append({"filename": filename,
                                      "content": content,
                                      "mimetype": mimetype})

    def delete_attachment(self, filename):
        self._delete_attachments.add(filename)

    def add_log_items(self):
        "Return a dictionary of additional items to add to the log entry."
        result = {}
        if self._delete_attachments:
            result["attachments_deleted"] = self._delete_attachments
        if self._add_attachments:
            for att in self._add_attachments:
                content = att.pop("content")
                att["length"] = len(content)
                md5 = hashlib.md5(content.encode("utf-8"))
                att["digest"] = base64.b64encode(md5.digest()).decode("utf-8")
            result["attachments_added"] = self._add_attachments
        return result


class EntitySaver(AttachmentsSaver):
    "Entity saver context handling one file (attachment) per entity."

    def initialize(self):
        self.doc["owner"] = flask.g.current_user["username"]

    def change_owner(self, owner=None):
        "Change the owner."
        if not owner:
            owner = flask.request.form.get("owner")
        if not owner: return
        if not datagraphics.user.get_user(owner):
            raise ValueError(f"No user account '{owner}' to set as owner.")
        self.doc["owner"] = owner

    def set_editors(self, editors=None):
        if editors is None:
            editors = flask.request.form.get("editors", "").split()
        if editors:
            for editor in editors:
                if not datagraphics.user.get_user(editor):
                    raise ValueError(f"No user account '{editor}'"
                                     " to set as editor.")
            self.doc["editors"] = editors
        else:
            self.doc.pop("editors", None)
            
    def set_title(self, title=None):
        "Set the title."
        if title is None:
            title = flask.request.form.get("title")
        self.doc["title"] = title or "Untitled"

    def set_description(self, description=None):
        "Set the Markdown-formatted description."
        if description is None:
            description = flask.request.form.get("description") or ""
        # Remove carriage-returns from string.
        self.doc["description"] = description.replace('\r', '')

    def set_public(self, public=None):
        if public is None:
            self.doc["public"] = utils.to_bool(flask.request.form.get("public"))
        else:
            self.doc["public"] = bool(public)
