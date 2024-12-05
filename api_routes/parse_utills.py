def parse_order_message(message_data: dict):
    """
    Формирует текст сообщения из JSON-данных и добавляет кнопки управления заказом.
    """
    delivery_info = (
        f"ул. {message_data['delivery']['street']}, кв. {message_data['delivery']['flat']}, этаж {message_data['delivery']['floor']}"
        if message_data["delivery"]["street"]
        else "Адрес не указан"
    )
    products = "\n".join(
        [
            f"- {p['title']} (x{p['amount']}) — {p['price']}₽"
            for p in message_data["products"]
        ]
    )

    message_text = (
        f"📦 *Новый заказ!*\n\n"
        f"🏠 *Место*: {message_data['delivery']['type']}\n"
        f"🔢 *Номер заказа*: {message_data['orderNumber']}\n"
        f"🕒 *Время выдачи*: {message_data['readyTime']}\n"
        f"🕒 *Время заказа*: {message_data['createdAt']}\n"
        f"👤 *Клиент*: {message_data['customerInfo']['customerName']} "
        f"({message_data['customerInfo']['customerPhone']})\n"
        f"📍 *Адрес доставки*: {delivery_info}\n"
        f"🛒 *Заказано*:\n{products}\n"
        f"💰 *Итого*: {message_data['totalCost']}₽\n"
        f"🔗 [Ссылка на заказ]({message_data['order_link']})"
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить заказ", "url": message_data["order_approve"]},
                {"text": "❌ Отменить заказ", "url": message_data["order_cancel"]},
            ]
        ]
    }

    return message_text, inline_keyboard
