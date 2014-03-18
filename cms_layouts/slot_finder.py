from django.core.exceptions import ImproperlyConfigured
from .settings import FIXED_PLACEHOLDERS
import difflib


class MissingRequiredPlaceholder(Exception):

    def __init__(self, slot):
        self.slot = slot

    def __str__(self):
        return repr(self.slot)


def get_fixed_section_slots(slots):
    fixed_from_slots = {}
    for section, slot_data in FIXED_PLACEHOLDERS.items():
        fixed_slot_name, finder_kw = slot_data
        find_func =  get_finder(finder_kw)
        fixed_from_slots[section] = find_func(slots, fixed_slot_name)
    return fixed_from_slots


def get_finder(keyword):
    if keyword == 'similar':
        return get_similar
    if keyword == 'exact':
        return get_exact
    # TODO allow custom finders from other apps
    raise ImproperlyConfigured("There is no slot finder for %s." % keyword)


def get_similar(slots, required):
    matches = difflib.get_close_matches('content', slots)
    if matches:
        return matches[0]
    raise MissingRequiredPlaceholder(required)


def get_exact(slots, required):
    if required in slots:
        return required
    raise MissingRequiredPlaceholder(required)
