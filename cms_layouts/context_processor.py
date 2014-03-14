from django.template import Context, Template


def add_extra_html(instance, placeholder, rendered_content, original_context):
    """
        Adds some html content after the first plugin from a specific
        placeholder gets rendered
    """
    if hasattr(placeholder, '_extra_html'):
        extra_js = Template(
            '{{rendered_content|safe}}'
            '{{extra_html|safe}}')
        context = Context({
            'rendered_content': rendered_content,
            'extra_html': placeholder._extra_html
            })
        del placeholder._extra_html
        return extra_js.render(context)
    return rendered_content
