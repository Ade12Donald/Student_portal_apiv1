"""Small, dependency-free request validation -- no framework needed for this."""

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_create_payload(data):
    """Returns (cleaned_dict, errors_dict). errors_dict is empty if valid."""
    errors = {}

    if not isinstance(data, dict):
        return None, {"detail": "Request body must be a JSON object."}

    name = data.get("name")
    reg_no = data.get("reg_no")
    email = data.get("email")

    if not name or not isinstance(name, str) or not name.strip():
        errors["name"] = ["This field is required."]
    if not reg_no or not isinstance(reg_no, str) or not reg_no.strip():
        errors["reg_no"] = ["This field is required."]
    if not email or not isinstance(email, str) or not EMAIL_RE.match(email):
        errors["email"] = ["A valid email address is required."]

    if errors:
        return None, errors

    return {
        "name": name.strip(),
        "reg_no": reg_no.strip(),
        "email": email.strip().lower(),
    }, {}


def validate_update_payload(data):
    """Update is restricted to `name` only -- reg_no/email are never
    read from the body here, so they can't be changed through this
    endpoint no matter what's sent."""
    errors = {}

    if not isinstance(data, dict):
        return None, {"detail": "Request body must be a JSON object."}

    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors["name"] = ["This field is required."]

    if errors:
        return None, errors

    return {"name": name.strip()}, {}
