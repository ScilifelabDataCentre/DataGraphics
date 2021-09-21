"Test the API About resource."

import http.client
import unittest

import requests

import utils


class About(utils.ApiMixin, unittest.TestCase):
    "Test the API About resources."

    def test_software(self):
        "Get software information."
        url = f"{self.settings['BASE_URL']}api//about/software"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)


if __name__ == "__main__":
    unittest.main()
