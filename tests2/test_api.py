"Tests of the DataGraphics API."

import http.client
import json

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
    1) default
    2) file 'settings.json' in this directory
    """
    result = {
        "BROWSER": "Chrome",
        "BASE_URL": "http://127.0.0.1:5005/",
        "USERNAME": None,
        "PASSWORD": None,
        "APIKEY": None
    }

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in result:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    return result

def test_software_info(settings, schemas):
    "Get the "
    url = f"{settings['BASE_URL']}api/about/software"
    headers = {"x-apikey": settings["APIKEY"]}
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)

def test_root_data(settings, schemas):
    "Get root information."
    url = f"{settings['BASE_URL']}api"
    headers = {"x-apikey": settings["APIKEY"]}
    response = requests.get(url, headers=headers)
    assert response.status_code == http.client.OK
    check_schema(response, schemas)

def check_schema(response, schemas):
    """ Return the response JSON after checking it against
    the JSON Schema in the response header.
    """
    result = response.json()
    try:
        url = response.links['schema']['url']
    except KeyError:
        raise ValueError(f"No schema schema for {response.url}")
    try:
        schema = schemas[url]
    except KeyError:
        r = requests.get(url)
        assert r.status_code == http.client.OK
        schema = r.json()
        schemas[url] = schema
    jsonschema.validate(instance=result,
                        schema=schema,
                        format_checker=jsonschema.draft7_format_checker)
    return result
