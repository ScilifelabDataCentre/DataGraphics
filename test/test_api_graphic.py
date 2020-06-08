"Test the graphic API endpoints."

import http.client

import api_base

class Graphic(api_base.Base):
    "Test the graphic API endpoints."

    def test_public_graphics(self):
        "Get public graphics."
        url = f"{api_base.SETTINGS['ROOT_URL']}/graphics/public"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_user_graphics(self):
        "Get user's graphics."
        url = f"{api_base.SETTINGS['ROOT_URL']}/graphics/user/{api_base.SETTINGS['USERNAME']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_all_graphics(self):
        "Get all graphics."
        url = f"{api_base.SETTINGS['ROOT_URL']}/graphics/all"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

if __name__ == '__main__':
    api_base.run()
