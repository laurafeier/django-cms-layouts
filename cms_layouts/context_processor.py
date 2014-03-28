from django.template import Context, Template


def add_extra_html(instance, placeholder, rendered_content, original_context):
    """
        Adds some html content after the first plugin from a specific
        placeholder gets rendered
    """
    html_before = getattr(placeholder, '_extra_html_before', '')
    html_after = getattr(placeholder, '_extra_html_after', '')
    if not html_before and not html_after:
        return rendered_content

    template_data = ['{{rendered_content|safe}}']
    context = Context({'rendered_content': rendered_content})

    if html_before:
        template_data.insert(0, '{{html_before|safe}}')
        context.update({'html_before': html_before})
        del placeholder._extra_html_before
    if html_after:
        template_data.append('{{html_after|safe}}')
        context.update({'html_after': html_after})
        del placeholder._extra_html_after

    return Template(''.join(template_data)).render(context)
