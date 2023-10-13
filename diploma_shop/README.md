# Онлайн- магазин MEGANO
Онлайн - магазин (платформа, на которой размещена информация о товаре).
Проект разработан на фреймворке Django. Запуск проекта осуществляется путём
клонирования репозитория, установки необходимых .env-опций и выполнения миграции.
Админпанель управления интернет-магазином реализована с помощью Django Admin.
Установка БД проекта полностью осуществляется командой миграции.
В проекте реализована фикстура данных, которая добавляет покупателей с простым паролем (55660078aA), 
а также товары, категории товаров, цены, заказы, скидки и другие данные.

## Структура сайта
1. Главная страница.
2. Каталог с фильтром и сортировкой:
   - Сам каталог товаров.
   - Детальная страница товара, с отзывами.
3. Оформление заказа:
   - Корзина.
   - Оформление заказа.
   - Оплата.
4. Личный кабинет:
   - Личный кабинет.
   - Профиль.
   - История заказов.
5. Административный раздел:
   - Просмотр и редактирование товаров.
   - Просмотр и редактирование заказов.
   - Просмотр и редактирование категорий каталога.

## Технологии
- Django 4.2.3
- PostgreSQL 15
- Django Rest Framework 3.14.0
- Pillow 10.0.0

## Установка и настройка

### Предварительные требования
- Python 3.11
- pip
- virtualenv
- Django 4.2.3
- PostgreSQL 15
- Django Rest Framework 3.14.0
- Pillow 10.0.0

### Установка
1. Клонируйте репозиторий:
```bash
git clone [https://gitlab.skillbox.ru/aleksandr_leonchenko/python_django_diploma/-/tree/master1/diploma_shop]
```
2. Создайте и активируйте виртуальное окружение:
```bash
virtualenv venv
source venv/bin/activate  # на Linux/macOS
.\venv\Scripts\activate   # на Windows
```
3. Установите зависимости:
```bash
pip install -r requirements.txt
```
4. Настройте базу данных в settings.py и выполните миграции:
```bash
python manage.py migrate
```

## Запуск проекта
```bash
python manage.py runserver
```
Сервер работает на http://127.0.0.1:8000/

## Авторы
- Леонченко Александр

## Лицензия
Отсутствует