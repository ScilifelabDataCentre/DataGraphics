"Test the user API endpoints."

import http.client

import base

class User(base.Base):
    "Test the user API endpoints."

    def test_user_data(self):
        "Get user information."
        url = f"{base.SETTINGS['ROOT_URL']}/user/{base.SETTINGS['USERNAME']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        user = self.check_schema(response)

    def test_users_data(self):
        "Get information for all users."
        url = f"{base.SETTINGS['ROOT_URL']}/user"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        users = self.check_schema(response)
        self.assertGreater(len(users), 1)


if __name__ == '__main__':
    base.run()
