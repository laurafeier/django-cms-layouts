from django.db import models
from cms.models.fields import PlaceholderField
from cms_layouts.models import LayoutTitle, Layout
from django.contrib.contenttypes.models import ContentType


class Article(models.Model):

    title = models.CharField('title', max_length=50)
    content = PlaceholderField('content', related_name='article_entry')

    def get_title_obj(self):
        article_title = LayoutTitle()
        article_title.title = self.title
        return article_title

    @property
    def layout(self):
        if not self.pk:
            return None
        layout = Layout.objects.filter(object_id=self.id,
            content_type=ContentType.objects.get_for_model(Article))[:1]
        if layout:
            return layout[0]
        return None
