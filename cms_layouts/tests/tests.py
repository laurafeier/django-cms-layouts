from django.test import TestCase
from django.test.client import RequestFactory
from cms_layouts.models import Layout, LayoutTitle
from cms_layouts.layout_response import LayoutResponse
from cms.api import create_page, add_plugin
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
            '|articleTitle|header|articleContent|footer')

    def test_layout_replaces_other_slots(self):
        overwrite_header = self.article.layout.get_or_create_placeholder('header')
        add_plugin(overwrite_header, 'TextPlugin', 'en', body='articleHeader')

        request = RequestFactory().get('None')
        response = LayoutResponse(
            self.article, self.article.layout, request).make_response()
        self.assertEqual(response.content,
            "|articleTitle|articleHeader|articleContent|footer")

        # make sure original page is the same
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.master_page_content)

    def test_layout_replaces_title(self):
        overwrite_header = self.article.layout.get_or_create_placeholder('header')
        add_plugin(overwrite_header, 'TextPlugin', 'en', body='articleHeader')
        custom_title = LayoutTitle()
        custom_title.title = 'LayoutTitle'

        request = RequestFactory().get('None')
        response = LayoutResponse(
            self.article, self.article.layout, request, title=custom_title).make_response()
        self.assertEqual(response.content,
            "|LayoutTitle|articleHeader|articleContent|footer")

        # make sure original page is the same
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.master_page_content)


