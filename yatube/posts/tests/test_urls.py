from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

TEXT = 'TEXT'
TITLE = 'Название'
SLUG = 'slug'
DESCRIPT = 'Описание'
AUTHOR = 'Author'
OTHER_USER = 'User'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_post = User.objects.create_user(
            username=AUTHOR
        )
        cls.other_user = User.objects.create_user(
            username=OTHER_USER
        )
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPT,
        )
        cls.post = Post.objects.create(
            text=TEXT,
            author=cls.author_post,
            group=cls.group
        )

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.author_post)
        self.other = Client()
        self.other.force_login(self.other_user)

    def test_post_list_url_exists_at_desired_location_for_all(self):
        """Тест доступности страницы по ожидаемому адресу."""
        pages_status = [
            [reverse('posts:index'),
                self.guest, HTTPStatus.OK],
            [reverse('posts:group_list', kwargs={'slug': self.group.slug}),
                self.guest, HTTPStatus.OK],
            [reverse('posts:profile', kwargs={'username': AUTHOR}),
                self.guest, HTTPStatus.OK],
            [reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
                self.guest, HTTPStatus.OK],
            [reverse('posts:post_create'), self.guest, HTTPStatus.FOUND],
            [reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                self.guest, HTTPStatus.FOUND],
            [reverse('posts:post_create'), self.other, HTTPStatus.OK],
            [reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                self.other, HTTPStatus.FOUND],
            [reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                self.author, HTTPStatus.OK],
            ['/unexisting_page/', self.author, HTTPStatus.NOT_FOUND]
        ]
        for address, client, code in pages_status:
            with self.subTest(address=address, client=client):
                self.assertEqual(
                    client.get(address).status_code, code
                )

    def test_create_edit_unavailability_by_guest(self):
        """Недоступность для гостя (Переадресация)."""
        resp = self.guest.get('/create/')
        self.assertRedirects(
            resp, '/auth/login/?next=%2Fcreate%2F', HTTPStatus.FOUND)

    def test_edit_unavailability_by_not_author(self):
        """Недоступность для не автора (Переадресация)."""
        resp = self.other.get('/posts/1/edit/')
        self.assertRedirects(
            resp, '/posts/1/', HTTPStatus.FOUND)

    def test__urls_author_templates(self):
        """Проврка на соответствие шаблона для автора редактирования"""
        resp = self.author.get('/posts/1/edit/')
        self.assertTemplateUsed(resp, 'posts/create_post.html')

    def test_accordance_urls_and_templates(self):
        """Проврка на соответствие урл и шаблонов"""
        url_templates_names = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.other.get(address)
                self.assertTemplateUsed(response, template)
