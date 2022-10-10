# Сервис Food_bot
Чатбот, в котором пользователь получает рецепты по подписке. Имеется возможность выбора предпочитаемой диеты. Первые три рецепта предоставляются бесплатно, далее необходимо оформить подписку. Данные вносятся через парсинг сайтов.  
## Запуск:

### 1. Копируем содержимое проекта себе в рабочую директорию
```
git clone <метод копирования>
```

### 2. Разворачиваем внутри скопированного проекта виртуальное окружение:
```
python -m venv <название виртуального окружения>
```

### 3. Устанавливаем библиотеки:
```
pip install -r requirements.txt
```

### 4. Для хранения переменных окружения создаем файл .env:
```
touch .env
```
Генерируем секретный ключ DJANGO в интерактивном режиме python:
* `python`
* `import django`
* `from django.core.management.utils import get_random_secret_key`
* `print(get_random_secret_key())`
    
Копируем строку в `.env` файл: `DJANGO_KEY='ваш ключ'` 

Для тестирования бота добавляем токен в `.env` файл: `TG_TOKEN='токен вашего бота'`
