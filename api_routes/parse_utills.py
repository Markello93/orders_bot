import re
from datetime import datetime


def format_date(date_string):
    date_obj = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    return date_obj.strftime("%Y-%m-%d %H:%M")


def escape_markdown_v2(text):
    """
    Экранирует текст для использования в Telegram Markdown V2.
    """
    escape_chars = r"_[]~`>#=|{}"
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
        delivery_info.append(f"📍 *Адрес доставки*: {delivery_address}")

        additional_info = [
            (
                f"кв. {message_data['delivery']['flat']}"
                if message_data["delivery"].get("flat")
                else ""
            ),
            (
                f"этаж {message_data['delivery']['floor']}"
                if message_data["delivery"].get("floor")
                else ""
            ),
            (
                f"подъезд {message_data['delivery']['porch']}"
                if message_data["delivery"].get("porch")
                else ""
            ),
            (
                f"код двери {message_data['delivery']['doorCode']}"
                if message_data["delivery"].get("doorCode")
                else ""
            ),
            (
                f"статус доставки: {message_data['delivery']['status']}"
                if message_data["delivery"].get("status")
                else ""
            ),
        ]
        additional_info = [info for info in additional_info if info]
        if additional_info:
            delivery_info.append(
                "Дополнительные сведения: " + ", ".join(additional_info)
            )

    elif delivery_type == "TO_OUTSIDE":
        if message_data["delivery"].get("pickupCode"):
            delivery_info.append(
                f"📍 *Код самовывоза*: {message_data['delivery']['pickupCode']}"
            )

    # Формирование списка продуктов
    products = []
    for product in message_data["products"]:
        product_line = (
            f"- {product['title']} (x{product['amount']}) — {product['price']}₽"
        )
        if product.get("additions"):
            # Добавляем заголовок "Добавки"
            additions = "\n".join(
                [
                    f"  └➕ {add['title']} (x{add['amount']}) — {add['price']}₽"
                    for add in product["additions"]
                ]
            )
            product_line += f"\n*Добавки:*\n{additions}"
        products.append(product_line)
    products_text = "\n".join(products)

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

    # Определение статуса
    status_mapping = {
        "CANCELLED_BY_PROVIDER": ("❌", "Заказ был отменен провайдером."),
        "CANCELLED_BY_CLIENT": ("❌", "Заказ был отменен клиентом."),
        "IN_PROGRESS": ("📦", "Заказ взят в работу."),
        "PAID": ("📦", "Новый заказ."),
    }
    emoji, status_text = status_mapping.get(
        message_data["status"], ("ℹ️", "Статус не определен.")
    )

    # Формирование текста сообщения
    message_text = escape_markdown_v2(
        f"{emoji} *{status_text}*\n\n"
        f"📍 *Место*: {place_title}\n"
        f"🔢 *Номер заказа*: {message_data['orderNumber']}\n"
        f"👥 *Количество персон*: {message_data.get('personsCount', 'не указано')}\n"
        f"🕒 *Время выдачи*: {ready_time}\n"
        f"🕒 *Время заказа*: {created_at}\n"
        f"👤 *Клиент*: {message_data['customerInfo']['customerName']} ({message_data['customerInfo']['customerPhone']})\n"
        f"🚚 *Тип доставки*: {delivery_type_text}\n"
        f"{''.join(delivery_info)}\n"
        f"🛒 *Состав заказа:*\n{products_text}\n"
        f"💰 *Итого*: {message_data['totalCost']}₽"
    )

    return message_text
