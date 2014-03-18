from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.forms.util import ErrorList
from django.core.urlresolvers import reverse
from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.utils import get_language_from_request
from cms.utils.plugins import get_placeholders
from cms.forms.widgets import PluginEditor
from cms.forms.fields import PlaceholderFormField
from cms.models.pluginmodel import CMSPlugin
from .models import Layout
from .forms import LayoutForm
from .slot_finder import get_fixed_section_slots, MissingRequiredPlaceholder


class LayoutAdmin(PlaceholderAdmin):
    form = LayoutForm
    readonly_fields = ('page_used_by_this_layout',
                       'object_that_uses_this_layout')
    fieldsets = (
        (None, {
            'fields': ('page_used_by_this_layout',
                       'object_that_uses_this_layout'),
            'classes': ('extrapretty', 'wide', ),
        }),)

    def _get_change_url(self, obj):
        pattern = 'admin:%s_%s_change' % (obj._meta.app_label,
                                          obj._meta.module_name)
        url = reverse(pattern,  args=[obj.id])
        url_tag = ("<a href='%s'>%s: %s</a>" % (
            url, obj._meta.module_name, obj))
        return url_tag

    def object_that_uses_this_layout(self, layout):
        if not layout.content_object:
            return "(missing object)"
        return self._get_change_url(layout.content_object)
    object_that_uses_this_layout.allow_tags = True

    def page_used_by_this_layout(self, layout):
        if not layout.from_page:
            return "(missing page)"
        return self._get_change_url(layout.from_page)
    page_used_by_this_layout.allow_tags = True

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        """
        It seems this is only used for the list view. |Yo_oY|
        """
        return {'add': False, 'change': False, 'delete': False, }

    def _get_fixed_slot_formfield(self, section_name):
        help_text = (
            "<h3>This section will be populated with %s "
            "from the object that uses this layout</h3>") % section_name
        content_field = PlaceholderFormField(
            required=False, help_text=help_text)
        widget = content_field.widget
        widget.attrs['readonly'] = 'readonly'
        widget.attrs['style'] = 'display:none;'
        return content_field

    def _get_slot_formfield(self, placeholder, language):
        plugins = CMSPlugin.objects.filter(language=language,
            placeholder=placeholder, parent=None).order_by('position')
        from cms.plugin_pool import plugin_pool
        editor = PluginEditor(attrs={
            'installed': plugin_pool.get_all_plugins(),
            'list': plugins,
            'copy_languages': [],
            'show_copy': False,
            'language': language,
            'placeholder': placeholder,
        })
        return PlaceholderFormField(widget=editor, required=False)

    def _get_layout_placeholders_fields(self, request, layout):
        formfields = {}
        lang = get_language_from_request(request, layout.from_page)
        # get placeholder slots from page template
        slots = get_placeholders(layout.from_page.get_template())

        fixed_slots = get_fixed_section_slots(slots)
        for fixed_section_name, fixed_slot_name in fixed_slots.items():
            formfield = self._get_fixed_slot_formfield(fixed_section_name)
            formfields[fixed_slot_name] = formfield

        for slot in filter(lambda s: s not in formfields, slots):
            layout_placeholder = layout.get_or_create_placeholder(slot)
            formfield = self._get_slot_formfield(layout_placeholder, lang)
            formfields[slot] = formfield

        return formfields

    def get_form(self, request, obj=None, **kwargs):
        form = super(LayoutAdmin, self).get_form(request, obj, **kwargs)
        if not obj:
            return form
        try:
            formfields = self._get_layout_placeholders_fields(request, obj)
        except MissingRequiredPlaceholder, e:
            form.missing_required_placeholder_slot = ErrorList([
                "This layout is missing a required placeholder named %s."
                "Choose a different page for this layout that has the "
                "required placeholder or just add this placeholder in the "
                "page template." % (e.slot, )])
        else:
            form.missing_required_placeholder_slot = False
            form.base_fields.update(formfields)
        return form

    def edit_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin, pk=int(plugin_id))
        layout = Layout.objects.get(placeholders__holder=plugin.placeholder_id)
        setattr(request, 'current_page', layout.from_page)
        return super(LayoutAdmin, self).edit_plugin(request, plugin_id)

    def get_label_for_placeholder(self, placeholder):
        return ' '.join([x.capitalize() for x in placeholder.split(' ')])

admin.site.register(Layout, LayoutAdmin)
