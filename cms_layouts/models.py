from django.db import models
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from cms.models.titlemodels import EmptyTitle
from cms.models.pagemodel import Page
from cms.models.placeholdermodel import Placeholder


class LayoutTitle(EmptyTitle):
    """
    The title object that will be used when renderig a layout.
    """
    title = "<No title provided>"
    slug = "<No slug provided>"
    path = ""
    meta_description = ""
    meta_keywords = ""
    menu_title = ""
    page_title = ""


class Layout(models.Model):

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    # should be used to identify different types of layouts for the same object
    layout_type = models.IntegerField(default=0)
    # keep link to the page from which this layout pulls template & placeholders
    from_page = models.ForeignKey(Page)

    def layout_type_display(self):
        if hasattr(self.content_object, 'layout_type_display'):
            return self.content_object.layout_type_display(self.layout_type)
        return '<missing-layout-type>'

    @property
    def hidden_placeholders(self):
        return Placeholder.objects.filter(layoutplaceholder__layout=self)

    @property
    def on_site(self):
        if hasattr(self.content_object, 'site'):
            return self.content_object.site
        if self.from_page:
            return self.from_page.site
        return Site.objects.get_current()

    def get_or_create_placeholder(self, slot):
        exists = self.hidden_placeholders.filter(slot=slot)[:1]
        if exists:
            return exists[0]
        new_placeholder = Placeholder.objects.create(slot=slot)
        layout_placeholder = LayoutPlaceholder.objects.create(
            holder=new_placeholder, layout=self)
        return new_placeholder

    def get_title_obj(self):
        if hasattr(self.content_object, 'get_title_obj'):
            return self.content_object.get_title_obj()
        return LayoutTitle

    def __unicode__(self):
        _type = 'Inherited from page'
        if self.hidden_placeholders:
            _type = 'Custom from page'
        return "<%s - %s>" % (_type, self.from_page)


class LayoutPlaceholder(models.Model):
    # instead of inheriting Placeholder and having to deal with all the
    #   DoesNotExists exceptions everywhere it's better to have only a fk to it
    holder = models.ForeignKey(Placeholder)
    # the placeholders linked to other models than Page and have slot names
    #   as the ones from page; these will be used when rendering this layout;
    #   when this layout does not have all placeholder slots defined then the
    #   ones from the linked page will be rendered
    layout = models.ForeignKey(Layout, related_name='placeholders')
