"Test the API Root resource."

import http.client
import unittest

import api_base


class Root(api_base.Base):
    "Test the API Root resource."

    def test_root_data(self):
        "Get root information."
        url = self.SETTINGS['ROOT_URL']
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)


if __name__ == "__main__":
    unittest.main()
