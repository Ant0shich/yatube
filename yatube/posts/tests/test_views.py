from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.conf import settings

from posts.models import Group, Post, User, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

import tempfile
import shutil

COUNT_POST_THTEE = 3
COUNT_POST_TEN = 10
TEXT = 'TEXT_FOR_TEST_CUT'
TITLE = 'Название'
SLUG = 'slug'
DESCRIPT = 'Описание'
TITLE_2 = 'Название_2'
SLUG_2 = 'slug_2'
DESCRIPT_2 = 'Описание_2'
AUTHOR = 'Author'
USER = 'User'

SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
             )

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USER)
        cls.author = User.objects.create(username=AUTHOR)
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPT
        )
        cls.group2 = Group.objects.create(
            title=TITLE_2,
            slug=SLUG_2,
            description=DESCRIPT_2
        )
        cls.UPLOADED = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text=TEXT,
            author=cls.author,
            group=cls.group,
            image=cls.UPLOADED
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_urls_pages_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name, template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_page_show_correct_context(self):
        """Проверка: Форма создания поста - post_create."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_on_index_group_profile_create(self):
        """Проверка: Созданный пост появился на Группе, Профайле, Главной"""
        reverse_page_names_post = {
            reverse('posts:index'): self.group.slug,
            reverse('posts:profile', kwargs={
                'username': self.user}): self.group.slug,
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): self.group.slug,
        }
        for value, expected in reverse_page_names_post.items():
            response = self.client.get(value)
            for object in response.context['page_obj']:
                post_group = object.group.slug
                with self.subTest(value=value):
                    self.assertEqual(post_group, expected)

    def test_index_page_show_correct_context(self):
        """Проверка: Шаблон index с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, TEXT)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)
        self.assertIn('page_obj', response.context)

    def test_group_list_page_show_correct_context(self):
        """Проверка: Шаблон group_list с правильным контекстом"""
        response = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': SLUG})))
        group = response.context['page_obj'][0]
        self.assertEqual(group.group, self.group)
        self.assertEqual(group.text, TEXT)
        self.assertEqual(group.author, self.author)
        self.assertIn('page_obj', response.context)
        self.assertEqual(group.image, self.post.image)

    def test_profile_page_shows_correct_context(self):
        """Проверка: Шаблон profile с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.text, TEXT)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.image, self.post.image)
        self.assertIn('page_obj', response.context)

    def test_post_detail_list_page_show_correct_context(self):
        """Проверка: Шаблон post_detai с правильным контекстом"""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})))
        post_detail = response.context['post']
        self.assertEqual(post_detail.text, TEXT)
        self.assertEqual(post_detail.group, self.group)
        self.assertEqual(post_detail.image, self.post.image)
        self.assertEqual(post_detail.author, self.author)

    def test_post_not_in_other_group(self):
        """Проверка: Созданный пост не появился в иной группе"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group2.slug}
            )
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))
        group2 = response.context.get('group')
        self.assertNotEqual(group2, self.group)

    def test_cache_index_page(self):
        """"Проверка: Кэш на странице Index"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_response = response.content
        post = Post.objects.get(pk=self.post.id)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_response)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPT,
        )
        cls.posts = [
            Post(
                text=f'{TEXT} {number_post}',
                author=cls.user,
                group=cls.group,
            )
            for number_post in range(13)
        ]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_author = Client()

    def test_page_contains_ten_records(self):
        """Проверка: пагинация на 1, 2 странице index, group_list, profile"""
        pagin_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,))
        )
        pages_units = (
            ('?page=1', COUNT_POST_TEN),
            ('?page=2', COUNT_POST_THTEE)
        )
        for address, args in pagin_urls:
            for page, count_posts in pages_units:
                with self.subTest(page=page):
                    response = self.authorized_author.get(
                        reverse(address, args=args) + page
                    )
            self.assertEqual(len(response.context['page_obj']), count_posts)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.another_user = User.objects.create_user(username=AUTHOR)
        cls.post = Post.objects.create(
            text=TEXT,
            author=cls.another_user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_user = Client()
        self.author_user.force_login(self.another_user)

    def test_authorized_client_follow(self):
        """Проверка: Пользователь может пописаться на другого автора"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': AUTHOR}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user).exists()
        )

    def test_authorized_client_unfollow(self):
        """Проверка: Пользователь может отаисаться от автора"""
        Follow.objects.create(
            user=self.user,
            author=self.another_user
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': AUTHOR}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user
            ).exists()
        )

    def test_new_post_does_not_appear_for_nonfollowers(self):
        """Проверка: запись пользователя не отображается в ленте тех,
        кто на него не подписан."""
        user_response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        user_content = user_response.context['page_obj']
        self.assertNotIn(self.post, user_content)

    def test_following_posts_showing_to_followers(self):
        """ Проверка: запись пользователя отображается в ленте тех,
        кто на него подписан."""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': AUTHOR}
            )
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        following_post = response.context['page_obj'][0].text
        self.assertEqual(following_post, self.post.text)
