"Test the API User resource."

import http.client

import api_base

class User(api_base.Base):
    "Test the API User resource."

    def test_user_data(self):
        "Get user information."
        url = f"{self.SETTINGS['ROOT_URL']}/user/{self.SETTINGS['USERNAME']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        user = self.check_schema(response)

    def test_users_data(self):
        "Get information for all users."
        url = f"{self.SETTINGS['ROOT_URL']}/users/all"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        users = self.check_schema(response)
        self.assertGreater(len(users), 1)
