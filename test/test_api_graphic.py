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

        # Upload JSON data content to the dataset.
        data = [{"col1": 1, "col2": 3.0, "col3": "c1"},
                {"col1": 2, "col2": 4.1, "col3": "c2"},
                {"col1": 3, "col2": 3.3, "col3": "c1"}]
        response = self.PUT(dataset["$id"] + ".json", json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Get the updated dataset containing the data content URLs.
        response = self.GET(dataset["$id"])
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Create the graphic.
        url = f"{api_base.SETTINGS['ROOT_URL']}/graphic/"
        response = self.POST(url, json={"title": "test",
                                        "dataset": dataset["iuid"]})
        self.assertEqual(response.status_code, http.client.OK)
        graphic = self.check_schema(response)
        self.assertTrue(bool(graphic["error"]))

        # Update the specification to make it correct.
        response = self.POST(graphic["$id"],
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
        response = self.DELETE(graphic["$id"])
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Delete the dataset.
        response = self.DELETE(dataset["$id"])
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    api_base.run()
