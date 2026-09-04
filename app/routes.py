import uuid
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, request
from pymongo.errors import DuplicateKeyError

from .db import get_students_collection
from .validators import validate_create_payload, validate_update_payload

bp = Blueprint("students", __name__, url_prefix="/api/students")


def _to_output(doc):
    """Maps a raw Mongo document to the API's output shape (no access_token)."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "reg_no": doc["reg_no"],
        "email": doc["email"],
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }


def _find_by_id(collection, id_str):
    """Looks a student up by id. Returns None for a missing or malformed
    id -- both should surface as 404, not a 500 crash."""
    try:
        object_id = ObjectId(id_str)
    except (InvalidId, TypeError):
        return None
    return collection.find_one({"_id": object_id})


def _extract_token():
    """Pulls the token out of 'Authorization: Token <token>'."""
    header = request.headers.get("Authorization", "")
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "token":
        return None
    return parts[1]


def _is_owner(doc):
    token = _extract_token()
    return token is not None and token == doc.get("access_token")


@bp.route("", methods=["POST"])
def create_student():
    """
    POST /api/students/

    Body: {"name": "...", "reg_no": "...", "email": "..."}

    Returns the created student's id and access_token. The access_token
    is shown here ONCE -- save it and send it back as
    `Authorization: Token <access_token>` on every future request that
    touches this student's own record.
    """
    cleaned, errors = validate_create_payload(request.get_json(silent=True))
    if errors:
        return jsonify(errors), 400

    collection = get_students_collection()

    if collection.find_one({"reg_no": cleaned["reg_no"]}):
        return jsonify({"reg_no": ["A student with this registration number already exists."]}), 400
    if collection.find_one({"email": cleaned["email"]}):
        return jsonify({"email": ["A student with this email already exists."]}), 400

    now = datetime.now(timezone.utc)
    doc = {
        **cleaned,
        "access_token": uuid.uuid4().hex,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = collection.insert_one(doc)
    except DuplicateKeyError:
        return jsonify({"detail": "A student with this registration number or email already exists."}), 400

    doc["_id"] = result.inserted_id
    output = {**_to_output(doc), "access_token": doc["access_token"]}
    return jsonify(output), 201


@bp.route("/<student_id>", methods=["GET"])
def get_student(student_id):
    """GET /api/students/<id>/ -- own details only."""
    collection = get_students_collection()
    doc = _find_by_id(collection, student_id)
    if doc is None:
        return jsonify({"detail": "Student not found."}), 404
    if not _is_owner(doc):
        return jsonify({"detail": "You may only access your own student record."}), 403
    return jsonify(_to_output(doc)), 200


@bp.route("/<student_id>", methods=["PATCH", "PUT"])
def update_student(student_id):
    """
    PATCH or PUT /api/students/<id>/ -- update name only.
    reg_no and email are never read from the body, so they can't be
    changed here regardless of what's sent.
    """
    collection = get_students_collection()
    doc = _find_by_id(collection, student_id)
    if doc is None:
        return jsonify({"detail": "Student not found."}), 404
    if not _is_owner(doc):
        return jsonify({"detail": "You may only access your own student record."}), 403

    cleaned, errors = validate_update_payload(request.get_json(silent=True))
    if errors:
        return jsonify(errors), 400

    now = datetime.now(timezone.utc)
    collection.update_one({"_id": doc["_id"]}, {"$set": {"name": cleaned["name"], "updated_at": now}})
    updated = collection.find_one({"_id": doc["_id"]})
    return jsonify(_to_output(updated)), 200


@bp.route("/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    """DELETE /api/students/<id>/ -- permanently delete own account."""
    collection = get_students_collection()
    doc = _find_by_id(collection, student_id)
    if doc is None:
        return jsonify({"detail": "Student not found."}), 404
    if not _is_owner(doc):
        return jsonify({"detail": "You may only access your own student record."}), 403

    collection.delete_one({"_id": doc["_id"]})
    return jsonify({"detail": "Account deleted successfully."}), 200
