from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseNotFound
from cms.utils import get_language_from_request
from cms.models.placeholdermodel import Placeholder
from cms.utils.plugins import get_placeholders
from cms.plugins.utils import get_plugins
from .slot_finder import (
    get_fixed_section_slots, MissingRequiredPlaceholder, get_mock_placeholder)


class LayoutResponse(object):

    def __init__(self, object_for_layout, layout, request,
                 context=None, title=None):
        self.content_object = object_for_layout
        self.layout = layout
        self.request = request
        self.context = context or RequestContext(request)
        self.title = title or self._get_title_for_context()

    def _get_title_for_context(self):
        # the title of the object with content that gets rendered has priority
        if hasattr(self.content_object, 'get_title_obj'):
            return self.content_object.get_title_obj()
        return self.layout.get_title_obj()

    def _call_render(self, method_name):
        return getattr(self.content_object, method_name)(
            self.request, self.context)

    def _wrap_in_placeholder(self, method_name):
        return get_mock_placeholder(get_language_from_request(self.request),
                                    self._call_render(method_name))

    def _get_fixed_slots(self, slots):
        fixed_content = {}
        fixed_sections = get_fixed_section_slots(slots)
        # section_name need to be either properties named header/content that
        #   return a placeholder instance or methods named
        #   render_header/render_content(with request&context params) that will
        #   return html code; the html will be set in a mock placeholder as
        #   a text plugin html
        for section_name, slot_found in fixed_sections.items():
            method_name = "render_%s" % section_name
            if (hasattr(self.content_object, section_name) or
                    hasattr(self.content_object, method_name)):
                # get content/header placeholder
                placeholder = (
                    getattr(self.content_object, section_name, None) or
                    self._wrap_in_placeholder(method_name))

                if not isinstance(placeholder, Placeholder):
                    raise HttpResponseNotFound(
                        "<h1>Cannot find content for this layout</h1>")
                # get extra html for header/content
                for extra_attr in ('extra_html_before', 'extra_html_after'):
                    section_attr = extra_attr + "_" + section_name
                    html = getattr(self.content_object, section_attr, None)
                    if html is None:
                        continue
                    if callable(html):
                        html = self._call_render(section_attr)
                    # set attribute for the plugins context processor
                    context_processor_attr = "_" + extra_attr
                    setattr(placeholder, context_processor_attr, html)

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
        # set the placeholders on the current page before django-cms does.
        # this variable name is used by cms to hold placeholders with all
        #   plugins. By setting this variable before cms, we ensure that cms
        #   will not cache the `real` page placeholders and will use the ones
        #   we set
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
        template_to_render = current_page.get_template()
        return render_to_response(
            template_to_render, self.context)
