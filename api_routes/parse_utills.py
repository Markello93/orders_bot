import re
from datetime import datetime, timedelta


def format_date(date_string):
    """Форматирует дату в виде "ДД Мес ГГ:ММ" с русскими сокращениями месяцев, конвертируя в МСК.

    Args:
        date_string: Строка с датой в ISO 8601 формате.

    Returns:
        Строка с форматированной датой.
    """
    # Парсим строку в объект datetime
    date_obj = datetime.fromisoformat(date_string.replace("Z", "+00:00"))

    # Добавляем 3 часа для перевода времени в Московское
    date_obj = date_obj + timedelta(hours=3)

    # Список сокращений месяцев на русском языке
    months_ru = ["янв.", "февр.", "марта", "апр.", "мая", "июня", "июля",
                 "авг.", "сент.", "октб.", "нояб.", "дек."]

    # Форматируем и возвращаем строку
    return f"{date_obj.day} {months_ru[date_obj.month - 1]} {date_obj.year} {date_obj.hour:02}:{date_obj.minute:02}"


def escape_markdown_v2(text):
    """
    Экранирует текст для использования в Telegram Markdown V2.
    """
    escape_chars = r"~`>#=|{}"
    return re.sub(r"([{}])".format(re.escape(escape_chars)), r"\\\1", text)


def parse_order_message(message_data: dict):
    """
    Формирует текст сообщения из JSON-данных заказа, добавляет кнопки управления.
    """
    # Тип доставки
    delivery_type = message_data["delivery"]["type"]
    delivery_type_mapping = {
        "DELIVERY": "Доставка",
        "TO_OUTSIDE": "Самовывоз",
        "ON_PLACE": "На месте",
    }
    delivery_type_text = delivery_type_mapping.get(
        delivery_type, "Неизвестный тип доставки"
    )

    # Информация о доставке
    delivery_info = []
    if delivery_type == "DELIVERY":
        delivery_address = message_data["delivery"].get("address", "Адрес не указан")
        delivery_info.append(f"🗺  Адрес доставки: *{delivery_address}*\n")
        delivery_info.append(
            f"🔐 Код для курьера: *{message_data['delivery']['pickupCode']}*\n"
        )
        additional_info = [
            (
                f"кв. *{message_data['delivery']['flat']}*"
                if message_data["delivery"].get("flat")
                else ""
            ),
            (
                f"этаж *{message_data['delivery']['floor']}*"
                if message_data["delivery"].get("floor")
                else ""
            ),
            (
                f"подъезд *{message_data['delivery']['porch']}*"
                if message_data["delivery"].get("porch")
                else ""
            ),
            (
                f"код двери *{message_data['delivery']['doorCode']}*"
                if message_data["delivery"].get("doorCode")
                else ""
            ),

        ]
        additional_info = [info for info in additional_info if info]
        if additional_info:
            delivery_info.append(
                "Дополнительные сведения: " + ", ".join(additional_info)
            )
    elif delivery_type in {"TO_OUTSIDE", "ON_PLACE"}:
        restaurant_address = message_data.get("restaurantAddress",
                                              "Адрес ресторана не указан")
        delivery_info.append(f"📍 Адрес ресторана: {restaurant_address}")

    # Формирование списка продуктов
    products = []
    for product in message_data["products"]:
        product_name = f"*{product['title']}*"
        weight_info = f" (вес: {product['weight']})" if product.get(
            "weight") else ""
        product_details = f"*(х{product['amount']})* — {product['price']} ₽"
        product_line = f"▫️ {product_name}{weight_info} {product_details}"
        if product.get("additions"):
            additions = "\n".join(
                [
                    f"     + {add['title']} (х{add['amount']}) — {add['price']} ₽"
                    for add in product["additions"]
                ]
            )
            product_line += f"\n{additions}"
        products.append(product_line)

    products_text = "\n".join(products)

    place = message_data["places"]
    place_title = place.get("title", "Место не указано")
    ready_time = (
        format_date(message_data["readyTime"])
        if message_data.get("readyTime")
        else "Не указано"
    )

    # Определение статуса
    status_mapping = {
        "CANCELLED_BY_PROVIDER":  "Отменен кассиром.",
        "CANCELLED_BY_CLIENT": "Отменен клиентом.",
        "IN_PROGRESS": "Взят в работу",
        "PAID": "Оплачен",
        "CANCELED_BY_TIMEOUT": "Заказ отменён - не был взят в работу",
        "COMPLETED": "Выполнен"
    }
    status_text = status_mapping.get(
        message_data["status"], "Статус не определен"
    )
    delivery_price_text = ""
    if message_data['delivery'].get("price") and delivery_type == "DELIVERY":
        delivery_price_text = f"🏎  Доставка: {message_data['delivery']['price']} ₽\n"

    message_text = escape_markdown_v2(
        f"Заказ №: *{message_data['orderNumber']}*\n"
        f"🕒 Время выдачи: *{ready_time}*\n"
        f"📦 Способ получения: *{delivery_type_text}*\n"
        f"💳 Статус заказа: *{status_text}*\n"
        f"👤 Клиент: *{message_data['customerInfo']['customerName']}* "
        f"({message_data['customerInfo']['customerPhone']})\n"
        f"👥 Количество персон: *{message_data.get('personsCount', 'не указано')}*\n\n"
        f"📍 Место: {place_title}\n"
        f"{''.join(delivery_info)}\n\n"
        f"🛒 Состав заказа:\n"
        f"{products_text}\n"
        f"{delivery_price_text}"
        f"💰 Итого: {message_data['totalCost']} ₽"
    )
    order_link = message_data.get("order_link")
    if order_link:
        message_text += escape_markdown_v2(
            f"\n\n[Ссылка для просмотра заказа в браузере]({order_link})"
        ) + " "

    return message_text

