"""Handle files hashing and upload path."""
import os
import hashlib


def hash_file(filename: str) -> str:
    """Hash the file name while preserving the extension."""
    hashed_name = hashlib.sha256(filename.encode('utf-8')).hexdigest()
    extension = os.path.splitext(filename)[1]
    return f"{hashed_name}{extension}"

def hash_profile(instance, filename):
    return f"profile/{hash_file(filename)}"

def hash_license(instance, filename):
    return f"license/{hash_file(filename)}"

def hash_document(instance, filename):
    return f"document/{hash_file(filename)}"

def hash_file(instance, filename):
    return f"file/{hash_file(filename)}"

