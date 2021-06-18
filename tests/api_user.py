"Test the API User resource."

import http.client
import unittest

import requests

import utils


class User(utils.ApiMixin, unittest.TestCase):
    "Test the API User resource."

    def test_user_data(self):
        "Get user information."
        url = f"{self.settings['BASE_URL']}api/user/{self.settings['USERNAME']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        user = self.check_schema(response)

    def test_users_data(self):
        "Get information for all users."
        url = f"{self.settings['BASE_URL']}api//users/all"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        users = self.check_schema(response)
        self.assertGreater(len(users), 1)
