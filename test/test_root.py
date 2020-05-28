"Test the root API endpoint."

import http.client

import base


class Root(base.Base):
    "Test the root API endpoint."

    def test_root_data(self):
        "Get root information."
        url = f"{base.SETTINGS['ROOT_URL']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
