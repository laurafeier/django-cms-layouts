from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseNotFound
from cms.models.pagemodel import Page
from cms.models.titlemodels import EmptyTitle
from cms.models.placeholdermodel import Placeholder
from cms.utils import get_template_from_request, get_language_from_request
from cms.utils.plugins import get_placeholders
from cms.plugins.utils import get_plugins
from .slot_finder import (
    get_fixed_section_slots, MissingRequiredPlaceholder, get_mock_placeholder)


class LayoutResponse:

    def __init__(self, object_for_layout, layout, request, title=None):
        self.content_object = object_for_layout
        self.layout = layout
        self.request = request
        self.title = title or self._get_title_for_context()

    def _get_title_for_context(self):
        # the title of the object with content that gets rendered has priority
        if hasattr(self.content_object, 'get_title_obj'):
            return self.content_object.get_title_obj()
        return self.layout.get_title_obj()

    def _get_fixed_slots(self, slots):
        fixed_content = {}
        fixed_sections = get_fixed_section_slots(slots)
        # section_name need to be propeties named header/content and need to
        #   return a placeholder instance
        for section_name, slot_found in fixed_sections.items():
            if hasattr(self.content_object, section_name):
                # get content/header placeholder
                placeholder = getattr(self.content_object, section_name)
                if not isinstance(placeholder, Placeholder):
                    raise HttpResponseNotFound(
                        "<h1>Cannot find content for this layout</h1>")
                # get extra html for header/content
                extra_html_attr = 'extra_html_%s' % section_name
                if hasattr(self.content_object, extra_html_attr):
                    extra_html = getattr(self.content_object, extra_html_attr)
                    setattr(placeholder, '_extra_html', extra_html)
            else:
                placeholder = get_mock_placeholder(
                    get_language_from_request(self.request))
            fixed_content[slot_found] = placeholder
        return fixed_content

    def _cache_plugins_for_placeholder(self, placeholder):
        """
        Calls get_plugins which sets the cache attribute on the given
        placeholder instance.
        """
        get_plugins(self.request, placeholder)

    def _get_patched_current_page(self):
        """
        Returns the current page required by CMS when rendering plugins.
        Uses django cms placeholder tag rendering logic and sets the cache
        attributes on the current page in order to stop CMS from fetching
        the plugins from the actual page.
        """
        page = self.layout.from_page
        # set placeholders cache
        placeholder_cache = {page.pk: {}, }
        # TODO maybe memoize this func call
        slots = get_placeholders(page.get_template())

        overwritten_slots = {
            phd.slot: phd
            for phd in self.layout.hidden_placeholders.filter(
                slot__in=slots, cmsplugin__isnull=False)}

        # fixed placeholders(header/content)
        fixed_placeholders = self._get_fixed_slots(slots)

        for original_phd in page.placeholders.filter(slot__in=slots):
            slot = original_phd.slot
            placeholder = (fixed_placeholders.get(slot, None) or
                           overwritten_slots.get(slot, None) or
                           original_phd)
            setattr(placeholder, 'page', page)
            self._cache_plugins_for_placeholder(placeholder)
            placeholder_cache[page.pk][slot] = placeholder
        setattr(page, '_tmp_placeholders_cache', placeholder_cache)
        return page

    def _prepare_page_for_context(self):
        """
        Caches the plugins that will get rendered and sets a mock-like title
        object that will be used in the context rendering.
        """
        current_page = self._get_patched_current_page()

        def get_title_obj(*args, **kwargs):
            return self.title
        setattr(current_page, 'get_title_obj', get_title_obj)

        return current_page

    def make_response(self):
        try:
            current_page = self._prepare_page_for_context()
        except MissingRequiredPlaceholder, e:
            return HttpResponseNotFound(
                "<h1>Layout is missing placeholder %s</h1>" % e.slot)
        # don't allow cms toolbar
        setattr(self.request, 'toolbar', False)
        setattr(self.request, 'current_page', current_page)
        template_to_render = get_template_from_request(
            self.request, current_page, no_current_page=True)
        return render_to_response(
            template_to_render, RequestContext(self.request))

