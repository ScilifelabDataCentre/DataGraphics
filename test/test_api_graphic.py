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

    def test_create_graphic(self):
        "Create, update and delete a graphic."

        # First create the dataset.
        url = f"{api_base.SETTINGS['ROOT_URL']}/dataset/"
        response = self.POST(url, json={"title": "test"})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload JSON data content.
        data = [{"col1": 1, "col2": 3.0, "col3": "c1"},
                {"col1": 2, "col2": 4.1, "col3": "c2"},
                {"col1": 3, "col2": 3.3, "col3": "c1"}]
        url = f"{api_base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.json"
        response = self.PUT(url, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Delete the dataset.
        url = f"{api_base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.DELETE(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    api_base.run()
