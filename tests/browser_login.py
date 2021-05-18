"Test the web site pages using Selenium. Logging in."

import time
import unittest

import selenium
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import utils


class LoginUser(utils.BrowserTestCase):
    "Test login as a user."

    def test_1_login(self):
        "Starting from the home page, login to a user account."

        # Home page.
        self.driver.get(self.settings["BASE_URL"])
        elem = self.driver.find_element_by_xpath("//form[@id='login-formlink']")
        elem = elem.find_element_by_tag_name("button")
        elem.click()

        # Login page; fill in user name and password in form.
        self.assertIn("Login", self.driver.title)
        elem = self.driver.find_element_by_name("username")
        elem.clear()
        elem.send_keys(self.settings["USERNAME"])
        elem = self.driver.find_element_by_name("password")
        elem.clear()
        elem.send_keys(self.settings["PASSWORD"])
        elem = self.driver.find_element_by_id("login-form-submit")
        elem.send_keys(Keys.RETURN)

        # Home page again.
        # Menu item "My datasets" is visible only when logged in.
        elem = self.driver.find_element_by_xpath("//div/preceding::a[@id='navbarDatasets']")
        elem.click()            # Must make pulldowm-menu visible.

        # Href in "My datasets" contains the user account name.
        elem = self.driver.find_element_by_link_text('My datasets')
        href = elem.get_attribute("href")
        self.assertEqual(href.split("/")[-1], self.settings["USERNAME"])
        elem.click()

        # Page listing the account's datasets.
        elem = self.driver.find_element_by_id("datasets")
        elems = elem.find_elements_by_xpath("//tbody/tr")
        self.assertGreaterEqual(len(elems), 0)

    def test_2_account(self):
        "Starting from login page, login and check user account."

        # Login page; fill in user name and password in form.
        self.driver.get(self.settings["BASE_URL"] + "user/login")
        self.assertIn("Login", self.driver.title)
        elem = self.driver.find_element_by_name("username")
        elem.clear()
        elem.send_keys(self.settings["USERNAME"])
        elem = self.driver.find_element_by_name("password")
        elem.clear()
        elem.send_keys(self.settings["PASSWORD"])
        elem = self.driver.find_element_by_id("login-form-submit")
        elem.send_keys(Keys.RETURN)

        # Home page. Find link to user account page.
        elem = self.driver.find_element_by_link_text(f"User {self.settings['USERNAME']}")
        elem.click()

        # User account page. Find API key.
        elem = self.driver.find_element_by_xpath("//th[text()='API key']/following-sibling::td")
        self.assertTrue(elem.text == "-" or len(elem.text) == 32)

    def test_3_logout(self):
        "Starting from the home page, login to a user account, and logout."

        # Home page.
        self.driver.get(self.settings["BASE_URL"])
        elem = self.driver.find_element_by_xpath("//form[@id='login-formlink']")
        elem = elem.find_element_by_tag_name("button")
        elem.click()

        # Login page; fill in user name and password in form.
        self.assertIn("Login", self.driver.title)
        elem = self.driver.find_element_by_name("username")
        elem.clear()
        elem.send_keys(self.settings["USERNAME"])
        elem = self.driver.find_element_by_name("password")
        elem.clear()
        elem.send_keys(self.settings["PASSWORD"])
        elem = self.driver.find_element_by_id("login-form-submit")
        elem.send_keys(Keys.RETURN)

        # Home page again. Find link to user account page.
        elem = self.driver.find_element_by_link_text(f"User {self.settings['USERNAME']}")
        elem.click()

        # User account page.
        elem = self.driver.find_element_by_xpath("//button[text()='Logout']")
        elem.click()

        # Home page again. No <div> with submenu under "Datasets".
        with self.assertRaises(NoSuchElementException) as cm:
            self.driver.find_element_by_xpath("//div/preceding::a[@id='navbarDatasets']")


if __name__ == "__main__":
    unittest.main()
