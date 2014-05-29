from django.core.exceptions import ImproperlyConfigured
from cms.models import Placeholder
from cms.plugins.text.models import Text
from .settings import FIXED_PLACEHOLDERS
import difflib


class MissingRequiredPlaceholder(Exception):

    def __init__(self, slot):
        self.slot = slot

    def __str__(self):
        return repr(self.slot)


def get_mock_placeholder(lang, html_content=None):
    """
    Returns a placeholder instance with a text plugin that can be used for
        rendering a layout.
    """
    mock_placeholder = Placeholder()
    mock_plugin = Text(body=(html_content or 'Fixed content'))
    mock_plugin.plugin_type = 'TextPlugin'
    mock_plugin.placeholder_id = mock_plugin.pk = 0
    setattr(mock_placeholder, '_%s_plugins_cache' % lang, [mock_plugin])
    return mock_placeholder


def get_fixed_section_slots(slots):
    fixed_from_slots = {}
    for section, slot_data in FIXED_PLACEHOLDERS.items():
        fixed_slot_name, finder_kw = slot_data
        find_func = get_finder(finder_kw)
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
