import difflib


def get_content_slot(slots):
    """
    Guess the first placeholder slot name from a list of slot names that is
    more similar to `content`.
    """
    matches = difflib.get_close_matches('content', slots)
    if matches:
        return matches[0]
    return None
