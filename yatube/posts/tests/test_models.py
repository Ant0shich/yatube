from django.test import TestCase

from posts.models import Group, Post, User

CUT_TEXT = 15
TEXT = 'TEXT_FOR_TEST_CUT'
TITLE = 'Название'
SLUG = 'slug'
DESCRIPT = 'Описание'
USER = 'User'
HELP_TEXT_TITLE = 'Дайте короткое название'
HELP_TEXT_SLUG = 'Укажите slug'
HELP_TEXT_DESC = 'Добавьте описание'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPT,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
        )

    def test_models_have_correct_object_names(self):
        """Проверка: что у моделей корректно работает __str__, title"""
        fields_posts_group = {
            self.post.text[:CUT_TEXT]: str(self.post),
            self.group.title: str(self.group)
        }
        for key, value in fields_posts_group.items():
            with self.subTest():
                self.assertEqual(key, value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        group = PostModelTest.group
        field_verboses = {
            'title': TITLE,
            'slug': SLUG,
            'description': DESCRIPT,
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        group = PostModelTest.group
        field_help_texts = {
            'title': HELP_TEXT_TITLE,
            'slug': HELP_TEXT_SLUG,
            'description': HELP_TEXT_DESC,
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)
