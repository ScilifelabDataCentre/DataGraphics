"Test the dataset API endpoints."

import collections
import csv
import http.client
import io

import base

class Dataset(base.Base):
    "Test the dataset API endpoint."

    def test_public_datasets(self):
        "Get public datasets."
        url = f"{base.SETTINGS['ROOT_URL']}/datasets/public"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_user_datasets(self):
        "Get user's datasets."
        url = f"{base.SETTINGS['ROOT_URL']}/datasets/user/{base.SETTINGS['USERNAME']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_all_datasets(self):
        "Get all datasets."
        url = f"{base.SETTINGS['ROOT_URL']}/datasets/all"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_create_dataset(self):
        "Create and delete a dataset."
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/"
        title = "My title"
        description = "My description."
        # Create the dataset.
        response = self.POST(url, json={"title": title,
                                        "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["title"], title)
        self.assertEqual(dataset["description"], description)
        # Delete the dataset.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.DELETE(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        
    def test_upload_json_dataset(self):
        "Create, upload, update and destroy a dataset using JSON."
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/"
        title = "My title"
        description = "My description."
        first = collections.OrderedDict()
        first["col1"] = 1
        first["col2"] = "apa"
        data = [first,
                {"col1": 2, "col2": "blarg"},
                {"col1": 3, "col2": None}]

        # Create the dataset.
        response = self.POST(url, json={"title": title,
                                        "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload JSON data content.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.json"
        response = self.PUT(url, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Update data, and upload.
        data.append({"col1": 4, "col2": "stuff"})
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.json"
        response = self.PUT(url, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Delete the dataset.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.DELETE(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        
    def test_upload_csv_dataset(self):
        "Create, upload and destroy a dataset using CSV."
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/"
        title = "My title"
        description = "My description."
        first = collections.OrderedDict()
        first["col1"] = 1
        first["col2"] = "apa"
        data = [first,
                {"col1": 2, "col2": "blarg"},
                {"col1": 3, "col2": None}]

        # Create the dataset.
        response = self.POST(url, json={"title": title,
                                        "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload CSV data content.
        outfile = io.StringIO()
        writer = csv.DictWriter(outfile, ["col1", "col2"])
        writer.writeheader()
        for record in data:
            writer.writerow(record)
        outfile.seek(0)
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.csv"
        response = self.PUT(url, data=outfile)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Update data, and upload as CSV.
        data.append({"col1": 4, "col2": "stuff"})
        outfile = io.StringIO()
        writer = csv.DictWriter(outfile, ["col1", "col2"])
        writer.writeheader()
        for record in data:
            writer.writerow(record)
        outfile.seek(0)
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.csv"
        response = self.PUT(url, data=outfile)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Read data directly from CSV file.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.csv"
        with open("test.csv", "rb") as infile:
            response = self.PUT(url, data=infile)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        with open("test.csv", "r") as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Delete the dataset.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.DELETE(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        
    def test_upload_dataset_update_bad(self):
        "Create, upload dataset and attempt bad update."
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/"
        title = "My title"
        description = "My description."
        first = collections.OrderedDict()
        first["col1"] = 1
        first["col2"] = "apa"
        data = [first,
                {"col1": 2, "col2": "blarg"},
                {"col1": 3, "col2": None}]

        # Create the dataset.
        response = self.POST(url, json={"title": title,
                                        "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload JSON data content.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.json"
        response = self.PUT(url, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Upload JSON data content with data that doesn't fit.
        bad_data = data[:]      # Shallow copy
        bad_data.append({"col1": "a string, not an integer", "col2": -1})
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}.json"
        response = self.PUT(url, json=bad_data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Check content and meta; compare to original data.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.GET(url)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Delete the dataset.
        url = f"{base.SETTINGS['ROOT_URL']}/dataset/{dataset['iuid']}"
        response = self.DELETE(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

if __name__ == '__main__':
    base.run()
