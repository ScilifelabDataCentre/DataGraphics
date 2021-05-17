"Test the API Root resource."

import http.client
import unittest

import requests

import utils


class Root(utils.ApiMixin, unittest.TestCase):
    "Test the API Root resource."

    def test_root_data(self):
        "Get root information."
        url = f"{self.settings['BASE_URL']}api"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)


if __name__ == "__main__":
    unittest.main()
