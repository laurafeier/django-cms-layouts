from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.contenttypes.models import ContentType
from cms_layouts.models import Layout, LayoutTitle, LayoutPlaceholder
from cms_layouts.layout_response import LayoutResponse
from cms.api import create_page, add_plugin
from cms.models import Placeholder
from .models import Article


class TestLayoutResponse(TestCase):

    def setUp(self):
        self.master = create_page(
            'master', 'page_template.html', language='en', published=True)
        self.article = Article.objects.create(title='articleTitle')
        add_plugin(self.article.content, 'TextPlugin', 'en', body='articleContent')
        article_layout = Layout()
        article_layout.from_page = self.master
        article_layout.content_object = self.article
        article_layout.save()
        # make content for master page
        text_required = []
        for phd in self.master.placeholders.all():
            add_plugin(phd, 'TextPlugin', 'en', body=phd.slot)
            text_required.append(phd.slot)
        self.master_page_content = "|master|%s" % '|'.join(text_required)

    def test_layout_replaces_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.master_page_content)

        request = RequestFactory().get('None')
        response = LayoutResponse(
            self.article, self.article.layout, request).make_response()
        self.assertEqual(response.content,
            '|articleTitle|header|articleHeader|articleContent|footer')

    def test_layout_replaces_other_slots(self):
        overwrite_header = self.article.layout.get_or_create_placeholder('header')
        add_plugin(overwrite_header, 'TextPlugin', 'en',
                   body='articleOverwriteHeader')

        request = RequestFactory().get('None')
        response = LayoutResponse(
            self.article, self.article.layout, request).make_response()
        self.assertEqual(response.content,
            "|articleTitle|articleOverwriteHeader|articleHeader|articleContent|footer")

        # make sure original page is the same
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.master_page_content)

    def test_layout_replaces_title(self):
        overwrite_header = self.article.layout.get_or_create_placeholder('header')
        add_plugin(overwrite_header, 'TextPlugin', 'en',
                   body='articleOverwriteHeader')
        custom_title = LayoutTitle()
        custom_title.title = 'LayoutTitle'

        request = RequestFactory().get('None')
        response = LayoutResponse(
            self.article, self.article.layout, request, title=custom_title).make_response()
        self.assertEqual(response.content,
            "|LayoutTitle|articleOverwriteHeader|articleHeader|articleContent|footer")

        # make sure original page is the same
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.master_page_content)

    def test_response_not_found_for_missing_fixed_section(self):
        self.master.template = 'page_no_extra_content.html'
        self.master.save()
        request = RequestFactory().get('None')
        response = LayoutResponse(
            self.article, self.article.layout, request).make_response()
        self.assertEqual(response.status_code, 404)

    def test_layout_deletion_on_page_delete(self):
        asd = self.article.layout.get_or_create_placeholder('header')
        self.master.delete()
        self.assertEqual(Layout.objects.count(), 0)
        self.assertEqual(LayoutPlaceholder.objects.count(), 0)
        # only the ones from article should remain
        self.assertEqual(Placeholder.objects.count(), 1)

    def test_layout_placeholder_deletion_on_layout_delete(self):
        layout = self.article.layout
        # make sure layout has a placeholder
        asd = layout.get_or_create_placeholder('header')
        self.assertEqual(LayoutPlaceholder.objects.count(), 1)
        # 4 placeholders from master page + 1 from article + 1 overwrite
        self.assertEqual(Placeholder.objects.count(), 6)
        layout.delete()
        self.assertEqual(LayoutPlaceholder.objects.count(), 0)
        self.assertEqual(Placeholder.objects.count(), 5)

    def test_layout_gets_deleted_when_article_gets_deleted(self):
        layout = self.article.layout
        # make sure layout has a placeholder
        asd = layout.get_or_create_placeholder('header')
        self.assertEqual(LayoutPlaceholder.objects.count(), 1)
        # 4 placeholders from master page + 1 from article + 1 overwrite
        self.assertEqual(Placeholder.objects.count(), 6)
        self.article.delete()
        self.assertEqual(LayoutPlaceholder.objects.count(), 0)
        self.assertEqual(Layout.objects.count(), 0)
        self.assertEqual(Placeholder.objects.count(), 4)
