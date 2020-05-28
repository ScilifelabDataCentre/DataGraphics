"Test the about API endpoints."

import http.client

import base


class About(base.Base):
    "Test the about API endpoint."

    def test_software(self):
        "Get software information."
        url = f"{base.SETTINGS['ROOT_URL']}/about/software"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
