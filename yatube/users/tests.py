from http import HTTPStatus
from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages(self):
        pages: tuple = (
            '/users/signup/',
            '/users/logout/',
            '/users/login/',
            '/users/password_change/',
            '/users/password_change/done/',
            '/users/password_reset/',
            '/users/password_reset/done/',
            '/users/reset/<uidb64>/<token>/',
            '/users/reset/done/'
        )
        for page in pages:
            response = self.guest_client.get(page)
            error_name: str = f'Ошибка: нет доступа до страницы {page}'
            self.assertEqual(response.status_code, HTTPStatus.OK, error_name)
