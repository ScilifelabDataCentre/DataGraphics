"""Test browser admin user access.

Requires a user account specified in the file 'settings.json' given by
- ADMIN_USERNAME
- ADMIN_PASSWORD

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
    result = {
        "BASE_URL": "http://127.0.0.1:5005/",
        "ADMIN_USERNAME": None,
        "ADMIN_PASSWORD": None
    }

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in result:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Remove any trailing slash.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/")
    return result


def login_user(settings, page):
    "Login to the system as admin user."
    page.goto(settings["BASE_URL"])
    page.click("text=Login")
    assert page.url == f"{settings['BASE_URL']}/user/login?"
    page.click('input[name="username"]')
    page.fill('input[name="username"]', settings["ADMIN_USERNAME"])
    page.press('input[name="username"]', "Tab")
    page.fill('input[name="password"]', settings["ADMIN_PASSWORD"])
    page.click("id=login")
    assert page.url == f"{settings['BASE_URL']}/datasets/user/{settings['ADMIN_USERNAME']}"


def test_admin_pages(settings, page):
    "Test admin-pecific pages."
    login_user(settings, page)

    page.goto(settings["BASE_URL"])
    page.click("text=Admin")
    page.click("text=All users")
    assert page.url == f"{settings['BASE_URL']}/user/all"

    page.click("text=Admin")
    page.click("text=Settings")
    assert page.url == f"{settings['BASE_URL']}/about/settings"
