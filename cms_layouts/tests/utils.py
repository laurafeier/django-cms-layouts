from django.template.loader import BaseLoader
from django.template.base import TemplateDoesNotExist

class MockLoader(BaseLoader):

    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        if template_name == 'page_template.html':
            return ('{% load cms_tags %}|'
                    '{% page_attribute "page_title" %}|'
                    '{% placeholder "header" %}|'
                    '{% placeholder "some-content" %}|'
                    '{% placeholder "footer" %}', 'page_template.html')
        elif template_name == '404.html':
            return "404 Not Found", "404.html"
        else:
            raise TemplateDoesNotExist()
