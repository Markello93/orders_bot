# Бот для проверки авторизации клиента и рассылки уведомлений

## Описание проекта
Данный бот предназначен для проверки авторизации пользователей через внешний API и отправки уведомлений. Он написан с использованием **Python** и **Aiogram**, с возможностью развертывания в **Docker**. 

Проект включает тестовый API на **FastAPI**, который можно использовать для проверки функционала. 

---
## Клонирование репозитория
### Используйте одну из следующих команд для клонирования:

```bash
git@github.com:Markello93/orders_bot.git
```
#### Через HTTPS: 
```bash
https://github.com/Markello93/orders_bot.git
```
## Настройка переменных окружения
Для работы приложения необходимо создать файл .env в корневой директории и указать следующие переменные окружения:

`BOT = token_вашего_телеграм_бота`
 `EXTERNAL_API_URL: URL эндпоинта внешнего API для проверки авторизации.`
 ```bash 
Пример:
EXTERNAL_API_URL=http://web_app:8000/test/check_access
 ```

### Получение ключа бота
* Перейти по ссылке в чат с BotFather https://telegram.me/BotFather
* напечатать команду /start
* напечатать команду /newbot
* ввести username для Вашего бота
* Скопировать token бота из сообщения от BotFather
* Вставить token в .env  файл BOT =
## Запуск приложения
### Локальный запуск тестового API и бота
Чтобы развернуть тестовый API и бота в одной локальной сети, используйте следующую команду:

```sh
docker compose -f docker-compose_local.yml up -d
```
### Запуск только бота:

```sh
docker compose -f docker-compose_bot.yml up -d
```
### Эндпоинты тестового API

1. **Проверка авторизации**  
   **Метод**: `POST`  
   **URL**: `/test/check_access`  
   Принимает номер телефона и идентификатор пользователя.

   **Пример запроса**:  
   ```json
   {
     "phone_number": "+123456789",
     "user_id": 12345
   }
      ```
   **Пример ответа**:
      ```json
    {
        "authorized": true
    }
      ```
2. **Отправка уведомления**  
   **Метод**: `POST`  
   **URL**: `/test/send_chat`  
   Принимает идентификатор пользователя и сообщение. В тестовом API структура json представлена в модели **SendChatRequest** в файле `api_routes/py_models`.

    **Пример запроса**:  
      ```json
    { 
         "chat_id": 12345,
         "message": {"order_id": "string","address": "string"}
    }
      ```
    **Пример ответа**:
      ```json
    {
        "status": 200,
        "message": "Message sent to Telegram successfully."
    }
    ```

## Дополнительная информация

- **Функция для обработки и форматирования сообщений**:  
  Находится в файле `api_routes/parse_utils.py`.

- **Валидатор номеров телефона**:  
  Находится в файле `src/utils.py`.

- **Роуты тестового API**:  
  Все эндпоинты описаны в `api_routes/routes.py`.
