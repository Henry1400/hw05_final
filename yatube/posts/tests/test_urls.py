from django.test import TestCase, Client
from posts.models import Post, Group, User
from http import HTTPStatus
from django.urls import reverse
from django.core.cache import cache


class PostURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовое описание поста')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание')
        self.pages = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        }

    def test_url_guest_client(self):
        """Доступ неавторизованного пользователя"""
        for page in self.pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_urls_authorized_client(self):
        """Доступ авторизованного пользователя"""
        pages_2 = {
            '/create/',
            f'/posts/{self.post.id}/edit/'
        }
        self.pages.update(pages_2)
        for page in self.pages:
            response = self.authorized_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            'posts/index.html': reverse(
                'posts:posts'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_wrong_uri_returns_404(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
