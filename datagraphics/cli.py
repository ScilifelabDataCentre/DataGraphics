"Command-line tool."

import argparse
import getpass
import io
import json
import os
import sys
import tarfile
import time

import flask

import datagraphics.app
import datagraphics.user

from datagraphics import constants
from datagraphics import utils


def get_parser():
    "Get the parser for the command line tool."
    p = argparse.ArgumentParser(prog="cli.py",
                                usage="python %(prog)s [options]",
                                description="DataGraphics command line interface")
    p.add_argument("-d", "--debug", action="store_true",
                    help="Debug logging output.")
    x0 = p.add_mutually_exclusive_group()
    x0.add_argument("-A", "--create_admin", action="store_true",
                    help="Create an admin user.")
    x0.add_argument("-U", "--create_user", action="store_true",
                    help="Create a user.")
    x0.add_argument("-D", "--dump", action="store", metavar="FILENAME",
                    nargs="?", const=True,
                    help="Dump all data into a tar.gz file.")
    x0.add_argument("-L", "--load", action="store", metavar="FILENAME",
                    help="Load (undump) data from a tar.gz file. The database should be empty.")
    return p

def execute(pargs):
    "Execute the command."
    if pargs.debug:
        flask.current_app.config["DEBUG"] = True
        flask.current_app.config["LOGFORMAT"] = "%(levelname)-10s %(message)s"
    if pargs.create_admin:
        with datagraphics.user.UserSaver() as saver:
            saver.set_username(input("username > "))
            saver.set_email(input("email > "))
            saver.set_password(getpass.getpass("password > "))
            saver.set_role(constants.ADMIN)
            saver.set_status(constants.ENABLED)
    elif pargs.create_user:
        with datagraphics.user.UserSaver() as saver:
            saver.set_username(input("username > "))
            saver.set_email(input("email > "))
            saver.set_password(getpass.getpass("password > "))
            saver.set_role(constants.USER)
            saver.set_status(constants.ENABLED)
    elif pargs.dump:
        if pargs.dump == True:
            filepath = "dump_{}.tar.gz".format(time.strftime("%Y-%m-%d"))
        else:
            filepath = pargs.dump
        dump(flask.g.db, filepath)
    elif pargs.load:
        load(flask.g.db, pargs.load)

def dump(db, filepath):
    if filepath.endswith(".gz"):
        mode = "w:gz"
    else:
        mode = "w"
    outfile = tarfile.open(filepath, mode=mode)
    count_items = 0
    count_files = 0
    for doc in db:
        # Only documents that explicitly belong to the application
        if doc.get("doctype") is None: continue
        info = tarfile.TarInfo(doc["_id"])
        rev = doc.pop("_rev")
        data = json.dumps(doc).encode("utf-8")
        doc["_rev"] = rev
        info.size = len(data)
        outfile.addfile(info, io.BytesIO(data))
        count_items += 1
        for attname in doc.get("_attachments", dict()):
            info = tarfile.TarInfo("{0}_att/{1}".format(doc["_id"], attname))
            attfile = db.get_attachment(doc, attname)
            if attfile is None: continue
            data = attfile.read()
            attfile.close()
            info.size = len(data)
            outfile.addfile(info, io.BytesIO(data))
            count_files += 1
    outfile.close()
    print(f"dumped {count_items} items and {count_files} files to {filepath}")

def load(db, filepath):
    "Load (undump) data from a tar.gz file. The database should be empty."
    count_items = 0
    count_files = 0
    attachments = dict()
    infile = tarfile.open(filepath, mode="r")
    for item in infile:
        itemfile = infile.extractfile(item)
        itemdata = itemfile.read()
        itemfile.close()
        print(item.name)
        if item.name in attachments:
            # This relies on an attachment being after its item in the tarfile.
            db.put_attachment(doc, itemdata, **attachments.pop(item.name))
            count_files += 1
        else:
            doc = json.loads(itemdata)
            # If the account already exists, do not load document.
            if doc["doctype"] == constants.DOCTYPE_USER:
                rows = db.view("users", "username", key=doc["username"])
                if len(list(rows)) != 0: continue
            atts = doc.pop("_attachments", dict())
            db.put(doc)
            count_items += 1
            for attname, attinfo in atts.items():
                key = "{0}_att/{1}".format(doc["_id"], attname)
                attachments[key] = dict(filename=attname,
                                        content_type=attinfo["content_type"])
    infile.close()
    print(f"loaded {count_items} items and {count_files} files from {filepath}")

def main():
    "Entry point for command line interface."
    parser = get_parser()
    pargs = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_usage()
    with datagraphics.app.app.app_context():
        flask.g.db = utils.get_db()
        execute(pargs)

if __name__ == "__main__":
    main()
