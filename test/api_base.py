"Base class for API tests."

import http.client
import json
import os
import re
import unittest

import jsonschema
import requests

from datagraphics import constants

JSON_MIMETYPE = 'application/json'

DEFAULT_SETTINGS = {
    'ROOT_URL': 'http://127.0.0.1:5005/api',
    'USERNAME': None,           # Needs to be set! Must have admin privileges.
    'APIKEY': None              # Needs to be set! For the above user.
}


class Base(unittest.TestCase):
    "Base class for DataGraphics API test cases."

    @classmethod
    def setUpClass(cls):
        cls.SETTINGS = DEFAULT_SETTINGS.copy()
        try:
            settings_filepath = os.environ["SETTINGS"]
        except KeyError:
            settings_filepath = "settings.json"
        with open(settings_filepath) as infile:
            cls.SETTINGS.update(json.load(infile))
        assert cls.SETTINGS['USERNAME']
        assert cls.SETTINGS['APIKEY']
        cls.schemas = {}

    def setUp(self):
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': self.SETTINGS['APIKEY']})
        self.addCleanup(self.close_session)

    def close_session(self):
        self.session.close()

    @property
    def root(self):
        "Return the API Root resource."
        try:
            return self._root
        except AttributeError:
            response = self.GET(self.SETTINGS['ROOT_URL'])
            self.assertEqual(response.status_code, http.client.OK)
            self._root = self.check_schema(response)
            return self._root

    def GET(self, url):
        return self.session.get(url)

    def POST(self, url, json=None, data=None):
        return self.session.post(url, json=json, data=data)

    def PUT(self, url, json=None, data=None):
        return self.session.put(url, json=json, data=data)

    def DELETE(self, url):
        return self.session.delete(url)

    def check_schema(self, response):
        """ Return the response JSON after checking it against
        the JSON Schema in the response header.
        """
        result = response.json()
        try:
            url = response.links['schema']['url']
        except KeyError:
            raise ValueError(f"No schema schema for {response.url}")
        try:
            schema = self.schemas[url]
        except KeyError:
            if url == constants.JSON_SCHEMA_URL:
                with open("schema.json") as infile:
                    schema = json.load(infile)
            else:
                r = self.GET(url)
                self.assertEqual(r.status_code, http.client.OK)
                schema = r.json()
            self.schemas[url] = schema
        self.validate_schema(result, schema)
        return result

    def validate_schema(self, instance, schema):
        "Validate the JSON instance versus the given JSON schema."
        jsonschema.validate(instance=instance,
                            schema=schema,
                            format_checker=jsonschema.draft7_format_checker)
