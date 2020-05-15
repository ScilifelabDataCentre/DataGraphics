# webapp-flask-couchdb-template

A template for a web app based on Flask and CouchDB with user account handling.

Uses Python3, Flask, CouchDB server, CouchDB2 (Python module), jsonschema,
Bootstrap, jQuery, DataTables.

## Usage

This is a GitHub template: You need to create your own repo out of
this one, and then start developing your app.

In order to add new functionality, you should add modules for your own
entities, defining their URL's and logic. Look at the `webapp.user` module
to see how this can be done.

This template provides the basic framweork including user account
handling, but you need to code your own entities and the display and
edit logic for those.

The code in this repo can run as an app without changes, even though
it is a template, but it won't do anything useful.

## Installation

1. Create your own GitHub repo out of this repo.

2. Clone your repo to your own work computer, as usual.

4. Set up your Python3 environment, e.g. using virtualenv.

5. Install the required Python3 third-party packages (Flask, etc) using
   `pip install -r requirements.txt'.
   
6. Create your JSON file `settings.json` in either the directory
   `{your-repo-dir}/site` or `{your-repo-dir}/webapp` by
   making a copy of `{your-repo-dir}/site/example_settings.json`
   Edit it to fit your site.
   If your email server is not the simple `localhost` with no password,
   then you need to set those variables. See the file
   `{your-repo-dir}/webapp/__init__.py` for all email-related settings
   variables.

7. Set up the CouchDB database that your app will use, and add the name of
   it, any required username and password for it, in your `settings.json`
   file.

8. Include the directory `{your-repo-dir}` in the Python path. This
   can be done in different ways. The simplest is to set it in the shell
   (e.g. in your .bashrc file):
   ```
   $ cd {your-repo-dir}
   $ export PYTHONPATH=$PWD:$PYTHONPATH
   ```

9. Run the Flask app in development mode as usual `python app.py`.

10. If you wish to run the Flask app in production mode, see the Flask
   manual or the Apache, nginx, or whichever outward-facing web server you
   are using for information.
