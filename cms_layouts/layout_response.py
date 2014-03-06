from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseNotFound
from cms.models.pagemodel import Page
from cms.models.titlemodels import EmptyTitle
from cms.models.placeholdermodel import Placeholder
from cms.utils import get_template_from_request
from cms.utils.plugins import get_placeholders
from cms.plugins.utils import get_plugins
from .helpers import get_content_slot


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

    def _fill_content(self):
        if hasattr(self.content_object, 'content'):
            # content needs to be a placeholder instance
            placeholder = self.content_object.content
            if not isinstance(placeholder, Placeholder):
                raise HttpResponseNotFound(
                    "<h1>Cannot find content for this layout</h1>")
            return placeholder
        return Placeholder()

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
        original_slots = {
            phd.slot: phd
            for phd in page.placeholders.filter(slot__in=slots)}

        overwritten_slots = {
            phd.slot: phd
            for phd in self.layout.hidden_placeholders.filter(
                slot__in=slots, cmsplugin__isnull=False)}

        for slot in slots:
            placeholder = (overwritten_slots.get(slot, None) or
                           original_slots.get(slot, None))
            setattr(placeholder, 'page', page)
            self._cache_plugins_for_placeholder(placeholder)
            placeholder_cache[page.pk][slot] = placeholder
        # set placeholder content
        content_slot = get_content_slot(slots)
        placeholder_cache[page.pk][content_slot] = self._fill_content()
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
        current_page = self._prepare_page_for_context()
        # don't allow cms toolbar
        setattr(self.request, 'toolbar', False)
        setattr(self.request, 'current_page', current_page)
        template_to_render = get_template_from_request(
            self.request, current_page, no_current_page=True)
        return render_to_response(
            template_to_render, RequestContext(self.request))

