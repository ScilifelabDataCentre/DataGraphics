# DataGraphics documentation

DataGraphics is a system for serving static **datasets** and
displaying **graphics** (plots, charts) that visualize the
datasets. It uses [Vega-Lite](https://vega.github.io/vega-lite/),
which is a JavaScript library implementing a grammar of interactive
graphics using a [JSON syntax](https://www.json.org/json-en.html).

# Dataset

A dataset contains data as well as some metadata describing it. It is
owned by a user account.

The data in a dataset consists of a list of records, where each record
contains key-value pairs. The data is homogenous: Each record has the
same set of keys and the corresponding values are of the same type.

The datatypes allowed for the values in a record are the simple
datatypes defined in [JSON Schema](https://json-schema.org/):

- integer
- number
- boolean
- string

The keys and the datatypes of the corresponding values are determined
automatically from the data when is first loaded into a dataset. This
metadata cannot be changed once defined for a dataset.

The data contents can be downloaded from, and uploaded to, the dataset
[CSV](https://en.wikipedia.org/wiki/Comma-separated_values)
[JSON](https://en.wikipedia.org/wiki/JSON). When
updating the data contents, the new data must have the same fields
and types as the previous data; it is not possible to change this
for a dataset by uploading differently structured data.

A dataset is static in the sense that the data contents does not
change unless explicitly updated by uploading data to it. It is not
possible to edit or delete single records in a dataset; the update
operation sets the entire data contents.

The metadata of a dataset consists of a title, a description
(optionally using Markdown), information about the fields of the data
such as type and whether null values are present, and min, max, mean,
median, stdev, as appropriate. The title and description can be edited
by the owner, while the other metadata is set by the system.

In addition, each field is tagged with the Veg-Lite encoding types
applicable for it:

- quantitative
- temporal
- ordinal
- nominal
- geojson

# Graphic

A graphic is a visualization of a dataset. It is owned by a user
account. A dataset can be visualized by any number of graphic items.

A graphic is created for a specific dataset, which cannot be
changed. However, the contents of the dataset may be updated.

A graphic can have a different owner than the dataset it
uses. However, if the dataset becomes inaccessible for the owner of
the graphics for some reason (the dataset is deleted by its owner, or
is made private), the visualization of the graphic will no longer be
viewable.

Since a graphic refers to its dataset by a URL, changing the dataset
will change the content of the graphic visualization.

The specification of the visualization is written using the
[Vega-Lite](https://vega.github.io/vega-lite/) high-level
grammar. For more information on it, follow the link.

# Access privileges

Currently, the access privileges system is based on a very simple model
where an item can have one of two possible access settings:

- A **private** (the default) item can be viewed only by the owner of it.
- A **public** item can be viewed by anyone, including anonymous (not logged-in) users.

Regardless of private/public setting, an item can be created, edited
and deleted **only** by its owner.

The access setting of dataset or a graphic can be changed by its owner.

# User account

A user account in the system is required to create and edit datasets
and graphics. A dataset and graphic is always owned by one and only one
user account.

A user account may have the role **admin** which permits the account
to view and edit almost anything in the system via the web
interface. This includes:

- Changing ownership of items.
- Creating, editing, deleting and viewing all items.
- Registering, enabling or disabling other user accounts.


# How to

## Include a graphic in a web page

A graphic can be included in a web page at another site. The required
HTML code fragment can be downloaded from the graphic page by clicking
the `HTML code` button on the right hand side of the web page for the
graphic in the DataGraphics system.

Here is an example of the HTML code:

<hr>

```
<!-- The graphic will be rendered in this div element in the HTML page. -->
<div id="graphic"></div>

<!-- Add the code below to the JavaScript section of the HTML page. -->
<script src="https://cdn.jsdelivr.net/npm/vega@5.12.1"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@4.12.2"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@6.8.0"></script>
<script src="https://datagraphics.dckube.scilifelab.se/graphic/ddb1119aefce47d58d0b3a49e98b4fcc.js?id=graphic"></script>
```

<hr>

The first part of the fragment contains the `div` element where the
graphic will be rendered. It must have its `id` attribute set. The
value of this attribute must be passed as a query parameter to the URL
in the JavaScript in the last `script` element in the second part of
the fragment.

The second part of the fragment contains the <code>script</code> elements
including the various required JavaScript libraries, and the JavaScript
code which actually renders the graphic. This part of the fragment is
usually placed close to the end of the HTML document, just before the
`</body>` tag.

Please note that a graphic included on a web page at another site must
have **public** access set, and its dataset must also be
**public**. There is no way to include authentication information in
the HTML code on a page.


# API

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
