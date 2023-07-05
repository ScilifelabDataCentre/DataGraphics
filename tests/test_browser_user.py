"""Test browser ordinary user access.

Requires a user account specified in the file 'settings.json' given by
- USER_USERNAME
- USER_PASSWORD

After installing from PyPi using the 'requirements.txt' file, one must do:
$ playwright install

To run while displaying browser window:
$ pytest --headed

Much of the code below was created using the playwright code generation feature:
$ playwright codegen http://localhost:5002/
"""

import json
import os
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
        "BASE_URL": "http://127.0.0.1:5000/",
        "USER_USERNAME": None,
        "USER_PASSWORD": None
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
    "Login to the system as ordinary user."
    page.goto(settings["BASE_URL"])
    page.click("text=Login")
    assert page.url == f"{settings['BASE_URL']}/user/login?"
    page.click('input[name="username"]')
    page.fill('input[name="username"]', settings["USER_USERNAME"])
    page.press('input[name="username"]', "Tab")
    page.fill('input[name="password"]', settings["USER_PASSWORD"])
    page.click("id=login")
    assert page.url == f"{settings['BASE_URL']}/datasets/user/{settings['USER_USERNAME']}"


# def test_user_page(settings, page):
#     "Test user information page."
#     login_user(settings, page)

#     page.goto(settings["BASE_URL"])
#     page.click(f"text=User {settings['USER_USERNAME']}")
#     assert page.url == f"{settings['BASE_URL']}/user/display/{settings['USER_USERNAME']}"


def test_create_dataset(settings, page):
    "Dataset create, update, delete."
    login_user(settings, page)

    page.goto(settings["BASE_URL"])
    page.click("text=Datasets")
    page.click("text=My datasets")
    assert page.url == f"{settings['BASE_URL']}/datasets/user/{settings['USER_USERNAME']}"

    page.click("text=Create dataset")

    # Prepare a JSON file to upload.
    try:
        filename = "/tmp/dataset.json"
        with open("/tmp/dataset.json", "w") as outfile:
            json.dump({"data": [{"id": 1, "height": 1.89, "age": 62, "name": "Per"},
                                {"id": 2, "height": 0.3, "age": 1, "name": "Kitten"}]},
                      outfile)
        page.click('input[name="title"]')
        title = "my test dataset"
        page.fill('input[name="title"]', title)
        with page.expect_file_chooser() as fc_info:
            page.click('input[name="file"]')
        file_chooser = fc_info.value
        file_chooser.set_files(filename)
        page.click('button:has-text("Create by file")')
    finally:
        os.remove(filename)
    assert page.locator("h2").inner_text().startswith(title)
    iuid = page.url.split("/")[-1]

    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click("#delete")
    assert page.url == f"{settings['BASE_URL']}/datasets/user/{settings['USER_USERNAME']}"
    # page.wait_for_timeout(3000)
