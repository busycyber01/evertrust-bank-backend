from marshmallow import ValidationError

def validate_request(schema, data):
    try:
        return schema().load(data)
    except ValidationError as err:
        raise ValueError(err.messages)