"""Test browser anonymous access.

After installing from PyPi using the 'requirements.txt' file, one must do:
$ playwright install

To run while displaying browser window:
$ pytest --headed

Much of the code below was created using the playwright code generation feature:
$ playwright codegen http://localhost:5002/
"""

import json
import urllib.parse

import pytest
import playwright.sync_api


@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    result = {"BASE_URL": "http://127.0.0.1:5005/"}

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in ["BASE_URL"]:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Remove any trailing slash.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/")
    return result


def test_about(settings, page):  # 'page' fixture from 'pytest-playwright'
    "Test access to 'About' pages."
    page.goto(settings["BASE_URL"])
    page.click("text=About")
    page.click("text=Contact")
    assert page.url == f"{settings['BASE_URL']}/about/contact"

    page.go_back()
    page.click("text=About")
    page.click("text=Software")
    assert page.url == f"{settings['BASE_URL']}/about/software"


def test_documentation(settings, page):  # 'page' fixture from 'pytest-playwright'
    "Test access to 'Documentation' pages."
    page.goto(settings["BASE_URL"])
    page.click("text=Documentation")
    page.click("text=Overview")
    assert page.url == f"{settings['BASE_URL']}/documentation/overview"

    page.go_back()
    page.click("text=Documentation")
    page.click("text=URL endpoints")
    assert page.url == f"{settings['BASE_URL']}/documentation/endpoints"

    page.click("text=Documentation")
    page.click("text=API JSON Schemas")
    assert page.url == f"{settings['BASE_URL']}/documentation/schemas"
