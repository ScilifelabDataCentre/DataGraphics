"Test the API Dataset resource."

import collections
import csv
import http.client
import io
import unittest

import requests

import utils


class Dataset(utils.ApiMixin, unittest.TestCase):
    "Test the API Dataset resource."

    def test_public_datasets(self):
        "Get public datasets."
        url = f"{self.settings['BASE_URL']}api/datasets/public"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_user_datasets(self):
        "Get user's datasets."
        url = f"{self.settings['BASE_URL']}api/datasets/user/{self.settings['USERNAME']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_all_datasets(self):
        "Get all datasets."
        url = f"{self.settings['BASE_URL']}api/datasets/all"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_create_dataset(self):
        "Create, update and delete a dataset."
        url = f"{self.settings['BASE_URL']}api/dataset/"
        title = "My title"
        description = "My description."

        # Create the dataset.
        response = requests.post(url,
                                 headers=self.headers,
                                 json={"title": title,
                                       "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        self.assertEqual(dataset["$id"], url)
        self.assertEqual(dataset["title"], title)
        self.assertEqual(dataset["description"], description)
        self.assertEqual(dataset["public"], False)

        # Update the dataset information.
        title = "New title"
        response = requests.post(dataset["$id"], 
                                 headers=self.headers,
                                 json={"title": title, 
                                       "public": True})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["title"], title)
        self.assertEqual(dataset["public"], True)

        # Delete the dataset.
        response = requests.delete(dataset["$id"], headers=self.headers)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        
    def test_upload_json_dataset(self):
        "Create, upload, update and destroy a dataset using JSON."
        url = f"{self.settings['BASE_URL']}api/dataset/"
        title = "My title"
        description = "My description."
        first = collections.OrderedDict()
        first["col1"] = 1
        first["col2"] = "apa"
        data = [first,
                {"col1": 2, "col2": "blarg"},
                {"col1": 3, "col2": None}]

        # Create the dataset.
        response = requests.post(url,
                                 headers=self.headers,
                                 json={"title": title,
                                        "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload JSON data content.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
        response = requests.put(url, headers=self.headers, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Update data, and upload.
        data.append({"col1": 4, "col2": "stuff"})
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
        response = requests.put(url, headers=self.headers, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))
        self.assertEqual(dataset["meta"]["col1"]["type"], "integer")
        self.assertEqual(dataset["meta"]["col1"]["vega_lite_types"],
                         ["quantitative"])
        self.assertEqual(dataset["meta"]["col2"]["type"], "string")
        self.assertEqual(dataset["meta"]["col2"]["vega_lite_types"],
                         ["nominal"])

        # Delete the dataset.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        
    def test_upload_csv_dataset(self):
        "Create, upload and destroy a dataset using CSV."
        url = f"{self.settings['BASE_URL']}api/dataset/"
        title = "My title"
        description = "My description."
        first = collections.OrderedDict()
        first["col1"] = 1
        first["col2"] = "apa"
        data = [first,
                {"col1": 2, "col2": "blarg"},
                {"col1": 3, "col2": None}]

        # Create the dataset.
        response = requests.post(url,
                                 headers=self.headers,
                                 json={"title": title,
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
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.csv"
        response = requests.put(url, headers=self.headers, data=outfile)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))
        self.assertEqual(dataset["meta"]["col1"]["type"], "integer")
        self.assertEqual(dataset["meta"]["col1"]["vega_lite_types"],
                         ["quantitative"])
        self.assertEqual(dataset["meta"]["col2"]["type"], "string")
        self.assertEqual(dataset["meta"]["col2"]["vega_lite_types"],
                         ["nominal"])

        # Update data, and upload as CSV.
        data.append({"col1": 4, "col2": "stuff"})
        outfile = io.StringIO()
        writer = csv.DictWriter(outfile, ["col1", "col2"])
        writer.writeheader()
        for record in data:
            writer.writerow(record)
        outfile.seek(0)
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.csv"
        response = requests.put(url, headers=self.headers, data=outfile)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Read data directly from CSV file.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.csv"
        with open("test.csv", "rb") as infile:
            response = requests.put(url, headers=self.headers, data=infile)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        with open("test.csv", "r") as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Delete the dataset.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        
    def test_upload_dataset_update_bad(self):
        "Create, upload dataset and attempt bad update."
        url = f"{self.settings['BASE_URL']}api/dataset/"
        title = "My title"
        description = "My description."
        first = collections.OrderedDict()
        first["col1"] = 1
        first["col2"] = "apa"
        data = [first,
                {"col1": 2, "col2": "blarg"},
                {"col1": 3, "col2": None}]

        # Create the dataset.
        response = requests.post(url,
                                 headers=self.headers,
                                 json={"title": title,
                                       "description": description})
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)

        # Upload JSON data content.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
        response = requests.put(url, headers=self.headers, json=data)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check content and meta.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Upload JSON data content with data that doesn't fit.
        bad_data = data[:]      # Shallow copy
        bad_data.append({"col1": "a string, not an integer", "col2": -1})
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
        response = requests.put(url, headers=self.headers, json=bad_data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Check content and meta; compare to original data.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.OK)
        dataset = self.check_schema(response)
        self.assertEqual(dataset["n_records"], len(data))
        self.assertEqual(len(dataset["meta"].keys()), len(data[0].keys()))
        self.assertEqual(sorted(dataset["meta"].keys()), sorted(data[0].keys()))

        # Delete the dataset.
        url = f"{self.settings['BASE_URL']}api/dataset/{dataset['iuid']}"
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
