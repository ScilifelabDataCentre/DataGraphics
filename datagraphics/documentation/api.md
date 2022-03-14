---
title: API for programmatic access
level: 0
ordinal: 100
---

The Application Programming Interface (API) uses JSON. Access is
granted by an API key which is set for a user account.

Several of the web pages have a button in the upper right corner
labelled **API** which links to the corresponding API resource.

The documentation pages linked to on the right-hand side describes
which of the HTTP operations (GET, PUT, POST, DELETE) are allowed,
which input is required, what they do, and which output is produced.

Using the [`requests` module](https://requests.readthedocs.io/en/master/),
this is a minimal example of how to use the API. It fetches a list
of the public datasets and outputs their titles.

<hr>

```
import requests

### Headers containing API key for authentication.
headers = {"x-apikey": "549782425f324eb098ce42f260e41e7a"}

### Get the top API endpoints.
url = "{{ url_for('api.root') }}"
response = requests.get(url, headers=headers)
print(response.status_code)    # Should output '200'

data = response.json()    # Contains links to other resources.

### Get list of current public datasets and output titles.
url = data["datasets"]["public"]["href"]
response = requests.get(url, headers=headers)

data = response.json()
for dataset in data["datasets"]:
    print(dataset["title"])
```

<hr>

More examples of how to use the API can be found in the `test` folder
of the software distribution; see the
[DataGraphics GitHub repo](https://github.com/pekrau/DataGraphics/tree/devel/test).
