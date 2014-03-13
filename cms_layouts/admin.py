from django.contrib import admin
from django.shortcuts import get_object_or_404
from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.utils import get_language_from_request
from cms.utils.plugins import get_placeholders
from cms.forms.widgets import PluginEditor
from cms.forms.fields import PlaceholderFormField
from cms.models.pluginmodel import CMSPlugin
from .models import Layout
from .forms import LayoutForm
from .helpers import get_content_slot


class LayoutAdmin(PlaceholderAdmin):
    form = LayoutForm
    readonly_fields = ('from_page', 'content_object')
    fieldsets = (
        (None, {
            'fields': ('from_page', 'content_object'),
        }),)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        """
        It seems this is only used for the list view. |Yo_oY|
        """
        return {'add': False, 'change': False, 'delete': False, }

    def _get_content_formfield(self, content_slot):
        content_field = PlaceholderFormField(
            required = False,
            help_text="<h3>This section will be populated with content "
                      "from the object that uses this layout</h3>")
        widget = content_field.widget
        widget.attrs['readonly'] = 'readonly'
        widget.attrs['style'] = 'display:none;'
        return content_field

    def _get_placeholder_formfield(self, placeholder, language):
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
        page_language = get_language_from_request(request, layout.from_page)
        # get placeholder slots from page template
        slots = get_placeholders(layout.from_page.get_template())
        # content slot should not be editable
        content_slot = get_content_slot(slots)
        for slot in slots:
            if content_slot and slot == content_slot:
                formfield = self._get_content_formfield(content_slot)
            else:
                layout_placeholder = layout.get_or_create_placeholder(slot)
                formfield = self._get_placeholder_formfield(
                    layout_placeholder, page_language)
            formfields[slot] = formfield
        return formfields

    def get_form(self, request, obj=None, **kwargs):
        form = super(LayoutAdmin, self).get_form(request, obj, **kwargs)
        if not obj:
            return form
        formfields = self._get_layout_placeholders_fields(request, obj)
        for slot, formfield in formfields.items():
            form.base_fields[slot] = formfield
        return form

    def edit_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin, pk=int(plugin_id))
        layout = Layout.objects.get(placeholders__holder=plugin.placeholder_id)
        setattr(request, 'current_page', layout.from_page)
        return super(LayoutAdmin, self).edit_plugin(request, plugin_id)

    def get_label_for_placeholder(self, placeholder):
        return ' '.join([x.capitalize() for x in placeholder.split(' ')])

admin.site.register(Layout, LayoutAdmin)
