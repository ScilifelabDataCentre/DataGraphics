"Test the dataset API endpoints."

import http.client

import base


class Dataset(base.Base):
    "Test the dataset API endpoint."

    def test_dataset(self):
        "Get datasets API JSON."
        url = f"{base.SETTINGS['ROOT_URL']}/datasets/public"
        response = self.session.get(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
