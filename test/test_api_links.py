"Walk all links in JSON from root."

import http.client
import os.path

import api_base


class Links(api_base.Base):
    "Walk all links in JSON from root."

    def test_links(self):
        self.visited = set()
        self.visit(api_base.SETTINGS['ROOT_URL'])

    def visit(self, url):
        if url in self.visited: return
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.visited.add(url)
        # URLs with explicit extensions are data; do not parse.
        if os.path.splitext(url)[1]: return
        hrefs = Hrefs()
        hrefs.traverse(self.check_schema(response))
        for url in hrefs:
            self.visit(url)


class Hrefs:
    "Traverse the JSON data structure to find all 'href' values."

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
           value.startswith(api_base.SETTINGS['ROOT_URL']):
            self.urls.append(value)

    def __iter__(self):
        yield from self.urls


if __name__ == '__main__':
    api_base.run()
