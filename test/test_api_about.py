"Test the API About resource."

import http.client

import api_base


class About(api_base.Base):
    "Test the API About resources."

    def test_software(self):
        "Get software information."
        url = f"{self.SETTINGS['ROOT_URL']}/about/software"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)
