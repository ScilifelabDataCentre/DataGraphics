"Tests of the DataGraphics API."

import csv
import http.client
import io
import json
import os.path

import jsonschema
import pytest
import requests


@pytest.fixture(scope="module")
def schemas():
    "Return the schema definitions lookup."
    with open("schema.json") as infile:
        return json.load(infile)


@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    result = {
        "BROWSER": "Chrome",
        "BASE_URL": "http://127.0.0.1:5005/",
        "USERNAME": None,
        "PASSWORD": None,
        "APIKEY": None,
    }

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in result:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Ensure trailing slash.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/") + "/"
    return result


@pytest.fixture(scope="module")
def headers(settings):
    return {"x-apikey": settings["APIKEY"]}


def test_software_info(settings, headers, schemas):
    "Get the software info data, compare to its schema."
    url = f"{settings['BASE_URL']}api/about/software"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)


def test_root_data(settings, schemas):
    "Get root information, compare to its schema."
    url = f"{settings['BASE_URL']}api"
    headers = {"x-apikey": settings["APIKEY"]}
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)


def test_user_data(settings, headers, schemas):
    "Get user information."
    url = f"{settings['BASE_URL']}api/user/{settings['USERNAME']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)


def test_user_datasets(settings, headers, schemas):
    "Datasets access."
    url = f"{settings['BASE_URL']}api/datasets/user/{settings['USERNAME']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)


def test_create_dataset(settings, headers, schemas):
    "Datasets create, update, delete."
    url = f"{settings['BASE_URL']}api/dataset/"
    title = "My title"
    description = "My description."

    # Create the dataset.
    response = requests.post(
        url, headers=headers, json={"title": title, "description": description}
    )
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    assert dataset["$id"] == url
    assert dataset["title"] == title
    assert dataset["description"] == description
    assert dataset["public"] == False

    # Update the dataset information.
    title = "New title"
    response = requests.post(
        dataset["$id"], headers=headers, json={"title": title, "public": True}
    )
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["title"] == title
    assert dataset["public"] == True

    # Delete the dataset.
    response = requests.delete(dataset["$id"], headers=headers)
    assert response.status_code == http.client.NO_CONTENT


def test_upload_json_dataset(settings, headers, schemas):
    "Create, upload, update and destroy a dataset using JSON."
    url = f"{settings['BASE_URL']}api/dataset/"
    title = "My title"
    description = "My description."
    first = dict()
    first["col1"] = 1
    first["col2"] = "apa"
    data = [first, {"col1": 2, "col2": "blarg"}, {"col1": 3, "col2": None}]

    # Create the dataset.
    response = requests.post(
        url, headers=headers, json={"title": title, "description": description}
    )
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)

    # Upload JSON data content.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
    response = requests.put(url, headers=headers, json=data)
    assert response.status_code == http.client.NO_CONTENT

    # Check content and meta.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["n_records"] == len(data)
    assert len(dataset["meta"].keys()) == len(data[0].keys())
    assert sorted(dataset["meta"].keys()) == sorted(data[0].keys())

    # Update data, and upload.
    data.append({"col1": 4, "col2": "stuff"})
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
    response = requests.put(url, headers=headers, json=data)
    assert response.status_code == http.client.NO_CONTENT

    # Check content and meta.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["n_records"] == len(data)
    assert len(dataset["meta"].keys()) == len(data[0].keys())
    assert sorted(dataset["meta"].keys()) == sorted(data[0].keys())
    assert dataset["meta"]["col1"]["type"] == "integer"
    assert dataset["meta"]["col1"]["vega_lite_types"] == ["quantitative"]
    assert dataset["meta"]["col2"]["type"] == "string"
    assert dataset["meta"]["col2"]["vega_lite_types"] == ["nominal"]

    # Delete the dataset.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.delete(url, headers=headers)
    assert response.status_code == http.client.NO_CONTENT


def test_upload_csv_dataset(settings, headers, schemas):
    "Create, upload and destroy a dataset using CSV."
    url = f"{settings['BASE_URL']}api/dataset/"
    title = "My title"
    description = "My description."
    first = dict()
    first["col1"] = 1
    first["col2"] = "apa"
    data = [first, {"col1": 2, "col2": "blarg"}, {"col1": 3, "col2": None}]

    # Create the dataset.
    response = requests.post(
        url, headers=headers, json={"title": title, "description": description}
    )
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)

    # Upload CSV data content.
    outfile = io.StringIO()
    writer = csv.DictWriter(outfile, ["col1", "col2"])
    writer.writeheader()
    for record in data:
        writer.writerow(record)
    outfile.seek(0)
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}.csv"
    response = requests.put(url, headers=headers, data=outfile)
    assert response.status_code == http.client.NO_CONTENT

    # Check content and meta.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["n_records"] == len(data)
    assert len(dataset["meta"].keys()) == len(data[0].keys())
    assert sorted(dataset["meta"].keys()) == sorted(data[0].keys())
    assert dataset["meta"]["col1"]["type"] == "integer"
    assert dataset["meta"]["col1"]["vega_lite_types"] == ["quantitative"]
    assert dataset["meta"]["col2"]["type"] == "string"
    assert dataset["meta"]["col2"]["vega_lite_types"] == ["nominal"]

    # Update data, and upload as CSV.
    data.append({"col1": 4, "col2": "stuff"})
    outfile = io.StringIO()
    writer = csv.DictWriter(outfile, ["col1", "col2"])
    writer.writeheader()
    for record in data:
        writer.writerow(record)
    outfile.seek(0)
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}.csv"
    response = requests.put(url, headers=headers, data=outfile)
    assert response.status_code == http.client.NO_CONTENT

    # Check content and meta.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["n_records"] == len(data)
    assert len(dataset["meta"].keys()) == len(data[0].keys())
    assert sorted(dataset["meta"].keys()) == sorted(data[0].keys())

    # Delete the dataset.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.delete(url, headers=headers)
    assert response.status_code == http.client.NO_CONTENT


def test_upload_dataset_update_bad(settings, headers, schemas):
    "Create, upload dataset and attempt bad update."
    url = f"{settings['BASE_URL']}api/dataset/"
    title = "My title"
    description = "My description."
    first = dict()
    first["col1"] = 1
    first["col2"] = "apa"
    data = [first, {"col1": 2, "col2": "blarg"}, {"col1": 3, "col2": None}]

    # Create the dataset.
    response = requests.post(
        url, headers=headers, json={"title": title, "description": description}
    )
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)

    # Upload JSON data content.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
    response = requests.put(url, headers=headers, json=data)
    assert response.status_code == http.client.NO_CONTENT

    # Check content and meta.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["n_records"] == len(data)
    assert len(dataset["meta"].keys()) == len(data[0].keys())
    assert sorted(dataset["meta"].keys()) == sorted(data[0].keys())

    # Upload JSON data content with data that doesn't fit.
    bad_data = data[:]  # Shallow copy
    bad_data.append({"col1": "a string, not an integer", "col2": -1})
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}.json"
    response = requests.put(url, headers=headers, json=bad_data)
    assert response.status_code == http.client.BAD_REQUEST

    # Check content and meta; compare to original data.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)
    assert dataset["n_records"] == len(data)
    assert len(dataset["meta"].keys()) == len(data[0].keys())
    assert sorted(dataset["meta"].keys()) == sorted(data[0].keys())

    # Delete the dataset.
    url = f"{settings['BASE_URL']}api/dataset/{dataset['iuid']}"
    response = requests.delete(url, headers=headers)
    assert response.status_code == http.client.NO_CONTENT


def test_public_graphics(settings, headers, schemas):
    "Get public graphics."
    url = f"{settings['BASE_URL']}api/graphics/public"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)


def test_user_graphics(settings, headers, schemas):
    "Get user's graphics."
    url = f"{settings['BASE_URL']}api/graphics/user/{settings['USERNAME']}"
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)


def test_create_graphic(settings, headers, schemas):
    "Create, update and delete a graphic."

    # First create the dataset.
    url = f"{settings['BASE_URL']}api/dataset/"
    response = requests.post(url, headers=headers, json={"title": "test"})
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)

    # Upload JSON data content to the dataset.
    data = [
        {"col1": 1, "col2": 3.0, "col3": "c1"},
        {"col1": 2, "col2": 4.1, "col3": "c2"},
        {"col1": 3, "col2": 3.3, "col3": "c1"},
    ]
    response = requests.put(dataset["$id"] + ".json", headers=headers, json=data)
    assert response.status_code == http.client.NO_CONTENT

    # Get the updated dataset containing the data content URLs.
    response = requests.get(dataset["$id"], headers=headers)
    assert response.status_code == http.client.OK
    dataset = check_schema(response, schemas)

    # Create the graphic, which will have an error.
    url = f"{settings['BASE_URL']}api/graphic/"
    response = requests.post(
        url, headers=headers, json={"title": "test", "dataset": dataset["iuid"]}
    )
    assert response.status_code == http.client.OK
    graphic = check_schema(response, schemas)
    assert bool(graphic["error"])

    # Update the specification to make it correct.
    response = requests.post(
        graphic["$id"],
        headers=headers,
        json={
            "specification": {
                "data": {"url": dataset["content"]["csv"]["href"]},
                "mark": "point",
                "encoding": {
                    "x": {"field": "col1", "type": "quantitative"},
                    "y": {"field": "col2", "type": "quantitative"},
                },
            }
        },
    )
    assert response.status_code == http.client.OK
    graphic = check_schema(response, schemas)
    assert not bool(graphic["error"])

    # Delete the graphic.
    response = requests.delete(graphic["$id"], headers=headers)
    assert response.status_code == http.client.NO_CONTENT

    # Delete the dataset.
    response = requests.delete(dataset["$id"], headers=headers)
    assert response.status_code == http.client.NO_CONTENT


def test_links(settings, headers):
    "Check that all links from the root and onwards can be traversed."
    base_url = f"{settings['BASE_URL']}api"
    visited = set()
    not_yet_visited = set([base_url])
    while not_yet_visited:
        url = not_yet_visited.pop()
        # A URL containing an extension is data, and should not be visited.
        if os.path.splitext(url)[1]:
            continue
        # Do not follow links to external resources.
        if not url.startswith(base_url):
            continue
        response = requests.get(url, headers=headers)
        assert response.status_code == http.client.OK
        visited.add(url)
        traverse(response.json(), visited, not_yet_visited)


def traverse(data, visited, not_yet_visited):
    "Pick out href's and traverse down the structure."
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "href" and isinstance(value, str) and value not in visited:
                not_yet_visited.add(value)
            traverse(value, visited, not_yet_visited)
    elif isinstance(data, list):
        for value in data:
            traverse(value, visited, not_yet_visited)
    else:  # Ignore all other data.
        pass


def check_schema(response, schemas):
    """Return the response JSON after checking it
    against the JSON Schema in the response header.
    """
    result = response.json()
    try:
        url = response.links["schema"]["url"]
    except KeyError:
        raise ValueError(f"No schema schema for {response.url}")
    try:
        schema = schemas[url]
    except KeyError:
        r = requests.get(url)
        assert r.status_code == http.client.OK
        schema = r.json()
        schemas[url] = schema
    jsonschema.validate(
        instance=result, schema=schema, format_checker=jsonschema.draft7_format_checker
    )
    return result
