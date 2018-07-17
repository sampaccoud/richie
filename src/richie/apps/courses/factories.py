"""
Courses factories
"""
import os
import random

from django.conf import settings
from django.core.files import File
from django.utils.text import slugify

import factory
from cms.api import add_plugin, create_page
from filer.models.imagemodels import Image

from ..core.tests.utils import file_getter
from .models import Course, Organization, Subject


def create_textplugin(cls, slot, language=None, html=True, max_nb_chars=None,
                      nb_paragraphs=None, plugin_type="TextPlugin"):
    """
    A common function to create and add a TextPlugin instance to a placeholder
    filled with some random text using Faker.

    Arguments:
        cls (model instance): Instance of a PageExtension used to search for
            given slot (aka a placeholder name).
        slot (string): A placeholder name available from page template.

    Keyword Arguments:
        language (string): Language code to use. If ``None`` (default) it will
            use default language from settings.
        html (boolean): If True, every paragraph will be surrounded with an
            HTML paragraph markup. Default is True.
        max_nb_chars (integer): Number of characters limit to create each
            paragraph. Default is None so a random number between 200 and 400
            will be used at each paragraph.
        nb_paragraphs (integer): Number of paragraphs to create in content.
            Default is None so a random number between 2 and 4 will be used.
        plugin_type (string or object): Type of plugin. Default use TextPlugin
            but you can any other similar plugin, aka a plugin which attempt
            only a ``body`` attribute.

    Returns:
        object: Created plugin instance.
    """
    language = language or settings.LANGUAGE_CODE
    container = "{:s}"
    if html:
        container = "<p>{:s}</p>"
    nb_paragraphs = nb_paragraphs or random.randint(2, 4)

    placeholder = cls.extended_object.placeholders.get(
        slot=slot
    )

    paragraphs = []
    for i in range(nb_paragraphs):
        max_nb_chars = max_nb_chars or random.randint(200, 400)
        paragraphs.append(
            factory.Faker("text", max_nb_chars=max_nb_chars).generate({})
        )
    body = [container.format(p) for p in paragraphs]

    return add_plugin(
        language=language,
        placeholder=placeholder,
        plugin_type=plugin_type,
        body="".join(body),
    )


class OrganizationFactory(factory.django.DjangoModelFactory):
    """
    A factory to automatically generate random yet meaningful organization page extensions
    in our tests.
    """

    class Meta:
        model = Organization
        exclude = ["parent", "title"]

    parent = None
    logo = factory.django.ImageField(
        width=180, height=100, from_func=file_getter(os.path.dirname(__file__), "logo")
    )
    # TODO: Make it unique since it's used to build 'code' that must be unique,
    # actually it can leads to fail sometime
    title = factory.Faker("company")

    @factory.lazy_attribute
    def extended_object(self):
        """
        Automatically create a related page with the random title
        """
        return create_page(
            self.title,
            "courses/cms/organization_detail.html",
            settings.LANGUAGE_CODE,
            parent=self.parent,
        )

    @factory.lazy_attribute
    def code(self):
        """
        Since `name` is required, let's just slugify it to get a meaningful code (and keep it
        below 100 characters)
        """
        return slugify(self.title)[:100]

    @factory.post_generation
    # pylint: disable=unused-argument, attribute-defined-outside-init, no-member
    def with_courses(self, create, extracted, **kwargs):
        """Add courses to ManyToMany relation."""
        if create and extracted:
            self.courses.set(extracted)

    @factory.post_generation
    # pylint: disable=unused-argument
    def with_content(self, create, extracted, **kwargs):
        """
        Add content plugins displayed in the "maincontent" placeholder of the organization page:
        - Picture plugin featuring a random banner image,
        - Text plugin featuring a long random description.
        """
        if create and extracted:
            language = settings.LANGUAGE_CODE

            # Add a banner with a random image
            placeholder = self.extended_object.placeholders.get(slot="banner")
            banner_file = file_getter(os.path.dirname(__file__), "banner")()
            wrapped_banner = File(banner_file, banner_file.name)
            banner = Image.objects.create(file=wrapped_banner)
            add_plugin(
                language=language,
                placeholder=placeholder,
                plugin_type="PicturePlugin",
                picture=banner,
                attributes={"alt": "banner image"},
            )

            # Add a text plugin with a long random description
            create_textplugin(self, "description",
                              nb_paragraphs=random.randint(2, 4))


class CourseFactory(factory.django.DjangoModelFactory):
    """
    A factory to automatically generate random yet meaningful course page extensions
    and their related page in our tests.

    The `active_session` field is set to a realistic Splitmongo course key in Open edX which
    matches the following pattern:

        {version}:{organization_code}+{number}+{session}

        e.g. "course-v1:CNAM+01032+session01"
    """

    class Meta:
        model = Course
        exclude = ["number", "parent", "session", "title", "version"]

    parent = None
    title = factory.Faker("catch_phrase")

    version = factory.Sequence(lambda n: "version-v{version}".format(version=n + 1))
    number = factory.Faker("numerify", text="#####")
    session = factory.Sequence(lambda n: "session{session:02d}".format(session=n + 1))

    active_session = factory.LazyAttribute(
        lambda o: "{version}:{organization_code}+{number}+{session}".format(
            version=o.version,
            organization_code=o.organization_main.code
            if o.organization_main
            else "xyz",
            number=o.number,
            session=o.session,
        )
    )
    organization_main = factory.SubFactory(OrganizationFactory)

    @factory.lazy_attribute
    def extended_object(self):
        """
        Automatically create a related page with the random title
        """
        return create_page(
            self.title,
            Course.TEMPLATE_DETAIL,
            settings.LANGUAGE_CODE,
            parent=self.parent,
        )

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_syllabus(self, create, extracted, **kwargs):
        """
        Add a text plugin for syllabus with a long random text
        """
        create_textplugin(self, "course_syllabus", nb_paragraphs=1)

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_format(self, create, extracted, **kwargs):
        """
        Add a text plugin for course format with a long random text
        """
        create_textplugin(self, "course_format", nb_paragraphs=1)

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_prerequisites(self, create, extracted, **kwargs):
        """
        Add a text plugin for pre requisites with a long random text
        """
        create_textplugin(self, "course_prerequisites", nb_paragraphs=1)

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_plan(self, create, extracted, **kwargs):
        """
        Add a text plugin for plan with a long random text
        """
        create_textplugin(self, "course_plan", nb_paragraphs=1)

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_content_license(self, create, extracted, **kwargs):
        """
        Add a text plugin for course content license with a long random text
        """
        create_textplugin(self, "license_course_content", nb_paragraphs=1)

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_participation_license(self, create, extracted, **kwargs):
        """
        Add a text plugin for course participation license with a long random text
        """
        create_textplugin(self, "license_course_participation", nb_paragraphs=1)

    @factory.post_generation
    # pylint: disable=unused-argument, attribute-defined-outside-init, no-member
    def with_subjects(self, create, extracted, **kwargs):
        """Add subjects to ManyToMany relation."""
        instances = kwargs.get("items", [])
        weight = kwargs.get("weight", 0)
        if create and extracted:
            self.subjects.set(random.sample(instances, weight))

    @factory.post_generation
    # pylint: disable=unused-argument, attribute-defined-outside-init
    def with_organizations(self, create, extracted, **kwargs):
        """Add organizations to ManyToMany relation."""
        instances = kwargs.get("items", [])
        weight = kwargs.get("weight", 0)
        if create and extracted:
            self.organizations.set(random.sample(instances, weight))


class SubjectFactory(factory.django.DjangoModelFactory):
    """
    A factory to automatically generate random yet meaningful subject page extensions
    and their related page in our tests.
    """

    class Meta:
        model = Subject
        exclude = ["title", "parent"]

    parent = None
    title = factory.Faker("catch_phrase")

    @factory.lazy_attribute
    def extended_object(self):
        """
        Automatically create a related page with the random title
        """
        return create_page(
            self.title,
            Subject.TEMPLATE_DETAIL,
            settings.LANGUAGE_CODE,
            parent=self.parent,
        )

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_banner(self, create, extracted, **kwargs):
        """
        Add a banner with a random image
        """
        language = settings.LANGUAGE_CODE
        banner_placeholder = self.extended_object.placeholders.get(slot="banner")

        banner_file = file_getter(os.path.dirname(__file__), "banner")()
        wrapped_banner = File(banner_file, banner_file.name)
        banner = Image.objects.create(file=wrapped_banner)

        add_plugin(
            language=language,
            placeholder=banner_placeholder,
            plugin_type="PicturePlugin",
            picture=banner,
            attributes={"alt": "banner image"},
        )

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_logo(self, create, extracted, **kwargs):
        """
        Add a logo with a random image
        """
        language = settings.LANGUAGE_CODE
        logo_placeholder = self.extended_object.placeholders.get(slot="logo")

        logo_file = file_getter(os.path.dirname(__file__), "logo")()
        wrapped_logo = File(logo_file, logo_file.name)
        logo = Image.objects.create(file=wrapped_logo)
        add_plugin(
            language=language,
            placeholder=logo_placeholder,
            plugin_type="PicturePlugin",
            picture=logo,
            attributes={"alt": "logo image"},
        )

    @factory.post_generation
    # pylint: disable=unused-argument
    def fill_description(self, create, extracted, **kwargs):
        """
        Add a text plugin for description with a long random text
        """
        create_textplugin(self, "description",
                          nb_paragraphs=random.randint(2, 4))

    @factory.post_generation
    # pylint: disable=unused-argument, attribute-defined-outside-init, no-member
    def with_courses(self, create, extracted, **kwargs):
        """Add courses to ManyToMany relation."""
        if create and extracted:
            self.courses.set(extracted)
