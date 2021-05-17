"Walk all links in JSON from root."

import http.client
import os.path
import unittest

import requests

import utils


class Links(utils.ApiMixin, unittest.TestCase):
    "Walk all links in JSON from root."

    def test_links(self):
        self.visited = set()
        url = f"{self.settings['BASE_URL']}api"
        self.visit(url)

    def visit(self, url):
        if url in self.visited: return
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.visited.add(url)
        # URLs with explicit extensions are data; do not parse.
        if os.path.splitext(url)[1]: return
        hrefs = Hrefs(base_url=f"{self.settings['BASE_URL']}api")
        hrefs.traverse(self.check_schema(response))
        for url in hrefs:
            self.visit(url)


class Hrefs:
    "Traverse the JSON data structure to find all 'href' values."

    def __init__(self, base_url):
        self.base_url = base_url

    def traverse(self, data):
        self.path = []
        self.urls = []
        self._traverse(data)

    def _traverse(self, fragment):
        if isinstance(fragment, dict):
            self.path.append(None)
            for key, value in fragment.items():
                self.path[-1] = key
                self._traverse(value)
            self.path.pop()
        elif isinstance(fragment, list):
            self.path.append(None)
            for pos, value in enumerate(fragment):
                self.path[-1] = pos
                self._traverse(value)
            self.path.pop()
        else:
            self.handle(fragment)

    def handle(self, value):
        "Handle the current path/value."
        if self.path[-1] == "href" and \
           value.startswith(self.base_url):
            self.urls.append(value)

    def __iter__(self):
        yield from self.urls
