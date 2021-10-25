"Test the API Graphic resource."

import http.client
import unittest

import requests

import utils


class Graphic(utils.ApiMixin, unittest.TestCase):
    "Test the API Graphic resource."

    def test_public_graphics(self):
        "Get public graphics."
        url = f"{self.settings['BASE_URL']}api/graphics/public"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_user_graphics(self):
        "Get user's graphics."
        url = f"{self.settings['BASE_URL']}api/graphics/user/{self.settings['USERNAME']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_all_graphics(self):
        "Get all graphics."
        url = f"{self.settings['BASE_URL']}api/graphics/all"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_create_graphic(self):
        "Create, update and delete a graphic."

        # First create the dataset.
        url = f"{self.settings['BASE_URL']}api/dataset/"
        response = requests.post(url,
                                 headers=self.headers,
                                 json={"title": "test"})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload JSON data content to the dataset.
        data = [{"col1": 1, "col2": 3.0, "col3": "c1"},
                {"col1": 2, "col2": 4.1, "col3": "c2"},
                {"col1": 3, "col2": 3.3, "col3": "c1"}]
        response = requests.put(dataset["$id"] + ".json",
                                headers=self.headers,
                                json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Get the updated dataset containing the data content URLs.
        response = requests.get(dataset["$id"], headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Create the graphic.
        url = f"{self.settings['BASE_URL']}api/graphic/"
        response = requests.post(url,
                                 headers=self.headers,
                                 json={"title": "test",
                                       "dataset": dataset["iuid"]})
        self.assertEqual(response.status_code, http.client.OK)
        graphic = self.check_schema(response)
        self.assertTrue(bool(graphic["error"]))

        # Update the specification to make it correct.
        response = requests.post(graphic["$id"],
                                 headers=self.headers,
                                 json={"specification":
                                       {"data": 
                                        {"url": dataset["content"]["csv"]["href"]},
                                        "mark": "point",
                                        "encoding": {
                                            "x": {"field": "col1",
                                                  "type": "quantitative"},
                                            "y": {"field": "col2",
                                                  "type": "quantitative"}
                                        }
                                       }
                                 })
        self.assertEqual(response.status_code, http.client.OK)
        graphic = self.check_schema(response)
        self.assertFalse(bool(graphic["error"]))

        # Delete the graphic.
        response = requests.delete(graphic["$id"], headers=self.headers)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Delete the dataset.
        response = requests.delete(dataset["$id"], headers=self.headers)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == "__main__":
    unittest.main()
