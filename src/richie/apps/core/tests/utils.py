"""
Useful stuff for testing
"""
import io
import os
import random

from cms.test_utils.testcases import CMSTestCase


class CMSPluginTestCase(CMSTestCase):
    """
    Enriched CMS test case object to include useful stuff about plugin
    rendering.
    """

    def get_practical_plugin_context(self, extra_context=None):
        """
        Build a template context with dummy request object and
        instanciated content renderer suitable to perform full rendering of
        any plugin.

        Note:
            CMSTestCase use a dummy AnonymousUser on default behavior you may
            override with a custom user if you an ``user`` attribute to your
            test case object.

        Keyword Arguments:
            extra_context (dict): Dictionnary to add extra variable to context.
                Default to an empty dict.

        Returns:
            django.template.Context: Template context filled with request
            object as ``request`` item and content renderer as
            ``cms_content_renderer`` item.
        """
        context = self.get_context()
        if extra_context:
            context.update(extra_context)

        renderer = self.get_content_renderer(request=context["request"])

        # 'cms_content_renderer' is the attempted item name from CMS rendering
        # machinary
        context["cms_content_renderer"] = renderer

        return context


def file_getter(basedir, image_type):
    """
    This function can be passed to factory boy ImageField to dynamically generate
    image fields.

    It randomly pick up an image from targeted directory (base dir + 'fixtures' dir +
    image type dir).

    Arguments:
        basedir (string): Base directory for fixtures directory, commonly the
            app test directory.
        image_type (string): Directory name in fixtures dir that contains some image to
            pick up.

    Returns:
        callable: A function that picks a random image for a given type of image (logo,
        banner,...)
    """

    def pick_random():
        """
        Pick a random file from fixtures within the image type passed as argument to the parent
        function.
        """
        image_directory = os.path.join(basedir, os.path.join("fixtures", image_type))
        filename = random.choice(os.listdir(image_directory))

        # Factory boy's "from_func" param is expecting a file but does not seem to close it
        # properly. Let's load the content of the file in memory and pass it as a BytesIO to
        # factory boy so that the file is nicely closed
        with open(os.path.join(image_directory, filename), "rb") as image_file:
            in_memory_file = io.BytesIO(image_file.read())
            in_memory_file.name = filename
        return in_memory_file

    return pick_random
