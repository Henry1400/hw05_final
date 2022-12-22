from django.test import TestCase
from posts.models import Group, Post, User
from django.conf import settings


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое описание поста',
        )

    def test_verbose_name(self):
        '''Проверка заполнения verbose_name'''
        field_verboses = {
            'group': 'Группа',
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                error_name = f'Поле {field} ожидало значение {expected_value}'
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value, error_name)

    def test_help_text(self):
        '''Проверка заполнения help_text'''
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                error_name = f'Поле {field} ожидало значение {expected_value}'
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value, error_name)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(self.group), self.group.title)
        self.assertEqual(
            str(self.post),
            self.post.text[:settings.LEN_OF_POSTS]
        )
