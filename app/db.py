"""
MongoDB connection, kept as a single client per process.

USE_MONGOMOCK=True (set automatically by tests) swaps in an in-memory
Mongo stand-in so the test suite doesn't need a real server running.
Everything else -- running the app for real -- always uses a genuine
MongoDB server via PyMongo.
"""

import os

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client

    if os.environ.get("USE_MONGOMOCK") == "True":
        import mongomock

        _client = mongomock.MongoClient()
    else:
        from pymongo import MongoClient

        uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri)

    return _client


def get_students_collection():
    db_name = os.environ.get("MONGO_DB_NAME", "student_portal")
    collection = get_client()[db_name]["students"]
    collection.create_index("reg_no", unique=True)
    collection.create_index("email", unique=True)
    return collection


def reset_client():
    """Used by tests to force a fresh client between test runs."""
    global _client
    _client = None
