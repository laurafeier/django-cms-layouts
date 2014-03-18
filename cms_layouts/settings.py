from django.conf import settings


FIXED_PLACEHOLDERS = {
    'header': getattr(settings, 'CMS_LAYOUT_FIXED_PLACEHOLDER_HEADER',
                      ('extra-page-content', 'exact')),
    'content': getattr(settings, 'CMS_LAYOUT_FIXED_PLACEHOLDER_CONTENT',
                      ('content', 'similar')),
}
