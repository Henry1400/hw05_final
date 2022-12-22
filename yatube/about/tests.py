from http import HTTPStatus
from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages(self):
        pages: tuple = ('/about/author/', '/about/tech/')
        for page in pages:
            response = self.guest_client.get(page)
            error_name: str = f'Ошибка: нет доступа до страницы {page}'
            self.assertEqual(response.status_code, HTTPStatus.OK, error_name)
