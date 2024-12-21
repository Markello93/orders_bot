import re
from datetime import datetime


def format_date(date_string):
    date_obj = datetime.fromisoformat(date_string.replace("Z", "+00:00"))

    return date_obj.strftime("%Y-%m-%d %H:%M")


def escape_markdown_v2(text):
    """
    Экранирует текст для использования в Telegram Markdown V2.
    """
    # Символы, которые нужно экранировать для Markdown V2
    escape_chars = r"_[]~`>#=|{}"
    return re.sub(r"([{}])".format(re.escape(escape_chars)), r"\\\1", text)


def parse_order_message(message_data: dict):
    """
    Формирует текст сообщения из JSON-данных заказа, добавляет кнопки управления.
    """
    # Тип доставки
    delivery_type = message_data["delivery"]["type"]

    # Определение текста для типа доставки
    delivery_type_mapping = {
        "DELIVERY": "Доставка",
        "TO_OUTSIDE": "Самовывоз",
        "ON_PLACE": "На месте",
    }
    delivery_type_text = delivery_type_mapping.get(delivery_type, "Неизвестный тип доставки")

    # Формируем информацию о доставке, включая только ненулевые значения
    delivery_info = []
    if delivery_type == "DELIVERY":
        if message_data["delivery"].get("address"):
            delivery_info.append(f"ул. {message_data['delivery']['address']}")
        if message_data["delivery"].get("flat"):
            delivery_info.append(f"кв. {message_data['delivery']['flat']}")
        if message_data["delivery"].get("floor"):
            delivery_info.append(f"этаж {message_data['delivery']['floor']}")
        if message_data["delivery"].get("porch"):
            delivery_info.append(f"подъезд {message_data['delivery']['porch']}")
        if message_data["delivery"].get("doorCode"):
            delivery_info.append(f"код двери {message_data['delivery']['doorCode']}")
        if message_data["delivery"].get("status"):
            delivery_info.append(
                f"статус доставки {message_data['delivery']['status']}"
            )
    elif delivery_type == "TO_OUTSIDE":
        delivery_info.append("Самовывоз")
    elif delivery_type == "ON_PLACE":
        delivery_info.append("На месте")

    # Собирать информацию о доставке в одну строку
    delivery_info_str = ", ".join(delivery_info) if delivery_info else "Не указано"

    # Код самовывоза
    pickup_code = (
        f"{message_data['delivery'].get('pickupCode')}\n"
        if message_data["delivery"].get("pickupCode")
        else ""
    )

    # Продукты
    products = "\n".join(
        [
            f"- {p['title']} (x{p['amount']}) — {p['price']}₽"
            for p in message_data["products"]
        ]
    )

    # Дополнения к продуктам
    for product in message_data["products"]:
        if product.get("additions"):
            additions = "\n".join(
                [
                    f"    + {add['title']} (x{add['amount']}) — {add['price']}₽"
                    for add in product["additions"]
                ]
            )
            products += f"\n{additions}"

    # Информация о месте
    place = message_data["places"]
    place_title = place.get("title", "Место не указано")
    ready_time = (
        format_date(message_data["readyTime"])
        if message_data.get("readyTime")
        else "Не указано"
    )
    created_at = (
        format_date(message_data["createdAt"])
        if message_data.get("createdAt")
        else "Не указано"
    )

    # Формирование текста сообщения
    message_text = escape_markdown_v2(
        f"📦 *Новый заказ!*\n\n"
        f"📍 *Место*: {place_title}\n"
        f"🔢 *Номер заказа*: {message_data['orderNumber']}\n"
        f"👥 *Количество персон*: {message_data.get('personsCount', 'не указано')}\n"
        f"🕒 *Время выдачи*: {ready_time}\n"
        f"🕒 *Время заказа*: {created_at}\n"
        f"👤 *Клиент*: {message_data['customerInfo']['customerName']} "
        f"({message_data['customerInfo']['customerPhone']})\n"
        f"🚚 *Тип доставки*: {delivery_type_text}\n"
        f"📍 *Адрес доставки*: {delivery_info_str}\n"
        f"📍 *Код самовывоза*: {pickup_code}\n"
        f"📜 *Статус заказа*: {message_data['status']}\n\n"
        f"🛒 *Состав заказа:*\n{products}\n"
        f"💰 *Итого*: {message_data['totalCost']}₽"
    )

    # Кнопки управления заказом
    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ Подтвердить заказ",
                    "url": message_data.get("order_approve"),
                },
                {"text": "❌ Отменить заказ", "url": message_data.get("order_cancel")},
            ]
        ]
    }

    return message_text, inline_keyboard