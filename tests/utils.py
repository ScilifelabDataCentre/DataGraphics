"Some utilities for the tests."

import http.client
import json
import os
import unittest

import jsonschema
import requests
import selenium.webdriver

from datagraphics import constants


class BrowserTestCase(unittest.TestCase):
    "Browser driver setup."

    def setUp(self):
        self.settings = get_settings()
        self.driver = get_browser_driver(self.settings["BROWSER"])

    def tearDown(self):
        self.driver.close()


class ApiMixin:
    "Provides method the check the validity of a result against its schema."

    def setUp(self):
        self.settings = get_settings()
        self.headers = {"x-apikey": self.settings["APIKEY"]}

    def check_schema(self, response):
        """ Return the response JSON after checking it against
        the JSON Schema in the response header.
        """
        result = response.json()
        try:
            url = response.links['schema']['url']
        except KeyError:
            raise ValueError(f"No schema schema for {response.url}")
        if not hasattr(self, 'schemas'):
            self.schemas = {}
        try:
            schema = self.schemas[url]
        except KeyError:
            if url == constants.JSON_SCHEMA_URL:
                with open("schema.json") as infile:
                    schema = json.load(infile)
            else:
                r = requests.get(url)
                self.assertEqual(r.status_code, http.client.OK)
                schema = r.json()
            self.schemas[url] = schema
        jsonschema.validate(instance=result,
                            schema=schema,
                            format_checker=jsonschema.draft7_format_checker)
        return result


def get_settings():
    """Get the settings from
    1) default
    2) settings file
    """
    result = {
        "BROWSER": "Chrome",
        "BASE_URL": "http://127.0.0.1:5005/",
        "USERNAME": None,
        "PASSWORD": None,
        "APIKEY": None
    }

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in result:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    return result

def get_browser_driver(name):
    "Return the Selenium driver for the browser given by name."
    if name == "Chrome":
        return selenium.webdriver.Chrome()
    elif name == "Firefox":
        return selenium.webdriver.Firefox()
    elif name == "Edge":
        return selenium.webdriver.Edge()
    elif name == "Safari":
        return selenium.webdriver.Safari()
    else:
        raise ValueError(f"Unknown browser driver '{name}'.")
