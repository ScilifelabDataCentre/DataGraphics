"Run all API tests."

import api_base

from test_api_root import Root
from test_api_about import About
from test_api_user import User
from test_api_dataset import Dataset
from test_api_graphic import Graphic


if __name__ == '__main__':
    api_base.run()
