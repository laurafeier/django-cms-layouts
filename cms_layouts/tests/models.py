from django.db import models
from cms.models.fields import PlaceholderField
from cms_layouts.models import LayoutTitle, Layout
from django.contrib.contenttypes.generic import GenericRelation


class Article(models.Model):

    title = models.CharField('title', max_length=50)
    content = PlaceholderField('content', related_name='article_entry_content')

    def render_header(self, request, context):
        return 'articleHeader'

    def get_title_obj(self):
        article_title = LayoutTitle()
        article_title.title = self.title
        return article_title

    def _delete_placeholder(self, placeholder):
        # delete plugins before in order to bypass the
        #   Placeholder.DoesNotExist exceptions occuring in
        #   django-cms/cms/signals.py: update_plugin_positions
        for plugin in placeholder.cmsplugin_set.all():
            plugin.delete()
        placeholder.delete()

    def delete(self):
        if self.content_id:
            self._delete_placeholder(self.content)
        super(Article, self).delete()

    layouts = GenericRelation(Layout)

    @property
    def layout(self):
        if not self.pk:
            return None
        layout = self.layouts.all()[:1]
        if layout:
            return layout[0]
        return None
