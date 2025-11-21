import re
import uuid


def is_valid_url(url):
    """Check if a string is a valid URL. Valid URLs are of the form 'protocol://hostname[:port]/path'.
    Args:
        url: The string to be checked.
    Returns:
        A boolean value indicating whether the string is a valid
    """
    pattern = re.compile(r"^(s3|https|http|tcp|smb|ftp)://[a-zA-Z0-9.-]+(?:/[^\s]*)?$")
    return bool(pattern.match(url))


def is_valid_uuid(s):
    """Check if a string is a valid UUID. Valid UUIDs are of the form 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'.
    Args:
        s: The string to be checked.
    Returns:
        A boolean value indicating whether the string is a valid UUID.
    """
    try:
        # Try converting the string to a UUID object
        uuid_obj = uuid.UUID(s)
        # Check if the string matches the canonical form of the UUID (with lowercase hexadecimal and hyphens)
        return str(uuid_obj) == s
    except Exception:
        return False