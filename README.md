# DataGraphics

Datasets and graphics served on the web using Vega-Lite.

Uses Python3, Flask, Vega-Lite, CouchDB server, CouchDB2 (Python module),
Marko, emoji, jsonschema, Bootstrap, jQuery, DataTables.

[Vega-Lite](https://vega.github.io/vega-lite/)
is a JavaScript library implementing a grammar of interactive graphics,
provided by the
[University of Washington Interactive Data Lab](https://idl.cs.washington.edu/)
(UW IDL).

## API usage

For an example of how to use the API to update dataset contents, see


## Installation

1. Download and unpack the zipped codebase from
   [https://github.com/pekrau/DataGraphics](https://github.com/pekrau/DataGraphics).
   The source code directory is called `{SOURCE}` in the following.

2. Set up your Python3 environment, e.g. using virtualenv, for the
   `{SOURCE}` directory.

3. Install the required Python3 third-party packages (Flask, etc) using
   `pip install -r requirements.txt'` in the `{SOURCE}` directory.
   
4. Create your JSON file `settings.json` in either the directory
   `{SOURCE}/site` or `{SOURCE}/datagraphics` by making a copy of 
   `{SOURCE}/site/example_settings.json`. Edit as appropriate for your site.

   For security, the `settings.json` should be readable only for the Linux
   account that runs the Flask server process.

   The `settings.json` file may contain an entry `ADMIN_USER` which will
   create an admin user if it doesn't exist. See the `example_settings.json`
   file for how it should look. The password for this user ought to be
   changed as soon as it has been created, for security.
   
   If your email server is not the simple `localhost` with no password,
   then you need to set those variables. See the file
   `{SOURCE}/datagraphics/config.py` for all email-related settings
   variables.

5. Set up the CouchDB database that your app will use, and add the name of
   it, any required username and password for it, in your `settings.json`
   file.

6. Include the `{SOURCE}` directory in the Python path. This can be done
   in different ways. The simplest is to set it in the shell
   (e.g. in your .bashrc file):
   ```
   $ cd {SOURCE}
   $ export PYTHONPATH=$PWD:$PYTHONPATH
   ```

7. You mays use the command-line interface to create user accounts.
   (See point 4 above for how to create an admin user in a different way.)
   This will also automatically load the index definitions to
   the CouchDB server, if not already done.
   ```
   $ python cli.py -A
   ```

8. Run the Flask app in development mode as usual. This will automatically
   load the index definitons to the CouchDB server, if not already done.
   If the `ADMIN_USER` entry has been defined properly in the `settings.json`
   file, it will be created.
   ```
   $ python app.py
   ```

9. For running the Flask app in production mode, see the information
   in the Flask manual and/or the Apache, nginx, or whichever
   outward-facing web server you are using.
