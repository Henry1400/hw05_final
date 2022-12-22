import tempfile
import shutil
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from posts.models import Post, Group, User, Follow
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from django.test import Client, TestCase, override_settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

NUM = 13
NUM_1 = 10
NUM_2 = 3


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.user2 = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug-group',
            description='Тестовое описание'
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif",
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.user,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user2)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}):
                    'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def context_post(self, post):
        '''Однотипный код для проверки постов'''
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.context_post(post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context['page_obj'][0]
        group = response.context['group']
        self.context_post(post)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user.username})
        )
        post = response.context['page_obj'][0]
        self.context_post(post)
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context.get('post')
        self.context_post(post)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={'post_id': self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_group(self):
        """Проверяем создание поста на странице выбранной группы"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_post_dont_exist_in_enemy_group(self):
        """Проверяем, что Пост не попап в чужую группу."""
        form_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_cache(self):
        ''' Теста кэша.'''
        response = self.guest_client.get(reverse('posts:index'))
        result = response.content
        Post.objects.get(id=1).delete
        response2 = self.guest_client.get(reverse('posts:index'))
        result2 = response2.content
        self.assertEqual(result, result2)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug-group',
            description='Тестовое описание'
        )
        Post.objects.bulk_create(
            Post(text=f'Post {i}', author=cls.user, group=cls.group)
            for i in range(NUM))
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_paginator(self):
        '''Проверка: количество постов на первой и второй страницах.'''
        pages = {
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        }
        for page in pages:
            response1 = self.authorized_client.get(page)
            response2 = self.authorized_client.get(page + '?page=2')
            self.assertEqual(len(response1.context['page_obj']), NUM_1)
            self.assertEqual(len(response2.context['page_obj']), NUM_2)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user')
        cls.user_following = User.objects.create_user(username='user_1')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following}
            )
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться
        от других пользователей."""
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following}
            )
        )
        follow_count = Follow.objects.count()
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 0)
