"Example of how to update the content of a dataset."

import requests  # The well-known third-party package.

# The API key authenticates a specific account in the system.
# That account must either be the owner of the dataset,
# or have role 'admin' to be allowed to update the dataset.

APIKEY = "a7a4b1d2ee404c87a42daa5b5232f894"

# The URL for the content of the dataset. Needs to be changed for your case.
# The UUID is the identifier of the dataset, which must already exist.
# The suffix determines the format of the data to PUT.

JSON_URL = "http://127.0.0.1:5005/api/dataset/6e5696ff2059423ca40d3f59936a6671.json"

# The dataset content is a list of dicts (records).
# The keys of each record and the types of the values must
# match the fields in the existing dataset.
# The order of the key/value pairs within a record is not significant.

# This data could be read from file using 'json.load()' instead.

data = [
    {"date": "2020-05-01", "count": 1345, "class": "negative"},
    {"date": "2020-05-01", "count": 45, "class": "positive"},
    {"date": "2020-05-01", "count": 1, "class": "failed"},
    {"date": "2020-05-02", "count": 1670, "class": "negative"},
    {"date": "2020-05-02", "count": 39, "class": "positive"},
    {"date": "2020-05-02", "count": 0, "class": "failed"},
    {"date": "2020-05-03", "count": 1509, "class": "negative"},
    {"date": "2020-05-03", "count": 44, "class": "positive"},
    {"date": "2020-05-03", "count": 3, "class": "failed"},
]

# ==== How to upload JSON file data. ====

response = requests.put(JSON_URL, headers={"x-apikey": APIKEY}, json=data)
print(response)  # Success if this is 204 (= HTTP "No Content").

# If the API key is bad, the response will be 403 ("Forbidden").
# If the dataset is bad in some way, the response will be 400 ("Bad Request").
# When any error, nothing will have been changed in the dataset on the server.

# ==== How to upload CSV file data. ====

import csv
import tempfile

# First we create a temporary CSV file and read the data from it.
# The order of the keys *is* significant in CSV format!

with tempfile.TemporaryFile("w+t") as outfile:
    writer = csv.DictWriter(outfile, ["date", "count", "class"])
    writer.writeheader()
    for record in data:
        writer.writerow(record)
    outfile.seek(0)
    csv_data = outfile.read()

# Note the suffix 'csv' here! This determines how the input data is interpreted.

CSV_URL = "http://127.0.0.1:5005/api/dataset/6e5696ff2059423ca40d3f59936a6671.csv"

response = requests.put(CSV_URL, headers={"x-apikey": APIKEY}, data=csv_data)
print(response)  # Success if this is 204 (= HTTP "No Content").
