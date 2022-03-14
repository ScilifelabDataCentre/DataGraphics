---
title: How to include a graphic in a web page
level: 0
ordinal: 50
---

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
