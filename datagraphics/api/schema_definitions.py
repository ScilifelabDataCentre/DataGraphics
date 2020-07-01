"JSON Schema definitions components."

link = {
    "title": "A link to a resource.",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "href": {"type": "string", "format": "uri"},
        "count": {"type": "integer"},
        "content-type": {"type": "string", "default": "application/json"},
        "format": {"type": "string", "default": "json"}
    },
    "required": ["href"],
    "additionalProperties": False
}

user = {
    "title": "The user account associated with the current resource.",
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "href": {"type": "string", "format": "uri"}
    },
    "required": ["username", "href"],
    "additionalProperties": False
}

logs_link = {
    "title": "Link to the log of changes for the entity.",
    "type": "object",
    "properties": {
        "href": {"type": "string", "format": "uri"}
    },
    "required": ["href"],
    "additionalProperties": False
}

property_names = {"pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$"}

iobody = {
    "title": "Input/output data body.",
    "type": "object",
    "properties": {
        "content-type": {"type": "string"},
        "schema": {
            "title": "JSON schema of data body content.",
            "type": "object",
            "properties": {
                "href": {"type": "string", "format": "uri"}
            },
            "required": ["href"],
            "additionalProperties": False
        }
    },
    "required": ["content-type"],
    "additionalProperties": False
}

io = {
    "oneOf": [
        {"$ref": "#/definitions/iobody"},
        {"type": "array",
         "items": {"$ref": "#/definitions/iobody"}
        }
    ]
}

operations = {
    "title": "Operations for modifying the DataGraphics server data.",
    "type": "object",
    "propertyNames": property_names,
    "additionalProperties": {
        "title": "The property name is the type of entity operated on.",
        "type": "object",
        "propertyNames": property_names,
        "additionalProperties": {
            "title": "The property name is the operation.",
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string", "format": "uri-template"},
                "variables": {
                    "type": "object"
                },
                "method": {
                    "type": "string",
                    "enum": ["POST", "PUT", "DELETE"]
                },
                "input": io,
                "output": io,
            },
            "required": ["href", "method"]
        }
    }
}
