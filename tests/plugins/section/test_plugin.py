"""
Section plugin tests
"""
from django.db import IntegrityError
from django.test import TestCase
from django.test.client import RequestFactory

from cms.api import add_plugin
from cms.models import Placeholder
from cms.plugin_rendering import ContentRenderer

from richie.plugins.section.cms_plugins import SectionPlugin
from richie.plugins.section.factories import SectionFactory


class SectionTests(TestCase):
    """Section plugin tests case"""

    def test_section_title_required(self):
        """
        A "title" is required when instantiating a section.
        """
        with self.assertRaises(IntegrityError) as cm:
            SectionFactory(title=None)
        self.assertIn(
            'null value in column "title" violates not-null constraint',
            str(cm.exception),
        )

    def test_section_create_success(self):
        """
        Section plugin creation success
        """
        section = SectionFactory(title="Foo")
        self.assertEqual("Foo", section.title)

    def test_section_context_and_html(self):
        """
        Instanciating this plugin with an instance should populate the context
        and render in the template.
        """
        placeholder = Placeholder.objects.create(slot="test")

        # Create random values for parameters with a factory
        section = SectionFactory()

        model_instance = add_plugin(
            placeholder, SectionPlugin, "en", title=section.title
        )
        plugin_instance = model_instance.get_plugin_class_instance()
        context = plugin_instance.render({}, model_instance, None)

        # Check if "instance" is in context
        self.assertIn("instance", context)

        # Check if parameters, generated by the factory, are correctly set in "instance" of context
        self.assertEqual(context["instance"].title, section.title)

        # Get generated html for section title
        renderer = ContentRenderer(request=RequestFactory())
        html = renderer.render_plugin(model_instance, {})

        # Check rendered title
        self.assertIn(section.title, html)

        # Get created Section plugin instance
        target = placeholder.get_plugins().get(plugin_type="SectionPlugin")

        # Nest a Text plugin into the Section plugin
        model_instance = add_plugin(
            placeholder,
            plugin_type="TextPlugin",
            language="en",
            target=target,
            body="Lorem ipsum",
        )

        # Get generated html again with added Text plugin
        renderer = ContentRenderer(request=RequestFactory())
        html = renderer.render_plugin(model_instance, {})

        # Check rendered text body
        self.assertIn("Lorem ipsum", html)
