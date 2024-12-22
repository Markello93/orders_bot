import json

from dotenv import load_dotenv
from fastapi import APIRouter, Query

import aiohttp

from api_routes.py_models import EditChatRequest, InputData, SendChatRequest
from src.core.settings import settings
from api_routes.parse_utills import parse_order_message

load_dotenv()
bot_token = settings.BOT
router = APIRouter(prefix="/v1", tags=["test API endpoints"])


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str = Query(
        ...,
        description="Статус заказа",
        regex="^(IN_PROGRESS|CANCELLED_BY_PROVIDER|COMPLETED)$",
    ),
):
    print(f"запрос по  id {order_id} получили, статус : {status}")
    return {"message": f"запрос по  id {order_id} получили, статус : {status}"}


@router.post("/check_access")
async def send_from_telegram(data: InputData):
    numbers = ["12345", "43213", "22333", "+79213678992"]
    if data.phone_number in numbers:
        print(f"пользователь с user_id:{data.user_id}")
        return {"authorized": True}
    return {"authorized": False}


@router.post("/send_chat")
async def send_to_telegram(dict_data: dict):
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # dict_data = data.dict()
    text = parse_order_message(dict_data["message"])
    status = dict_data["message"]["status"]
    inline_keyboard = None

    if status == "PAID":
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Подтвердить заказ",
                        "callback_data": f"order_confirm:{dict_data['message']['id']}",
                    },
                    {
                        "text": "❌ Отменить заказ",
                        "callback_data": f"order_cancel:{dict_data['message']['id']}",
                    },
                ]
            ]
        }
    elif status == "IN_PROGRESS":
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Выполнить заказ",
                        "callback_data": f"order_complete:{dict_data['message']['id']}",
                    },
                ]
            ]
        }
    payload = {
        "chat_id": data.chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if inline_keyboard:
        payload["reply_markup"] = json.dumps(inline_keyboard)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_url, json=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    message_id = response_data["result"]["message_id"]
                    return {
                        "status": 200,
                        "message": "Message sent to Telegram successfully.",
                        "message_id": message_id,
                        "response_data": response_data,
                    }
                else:
                    error_message = await response.text()
                    return {
                        "status": response.status,
                        "message": f"Failed to send message to Telegram: {error_message}",
                    }
    except Exception as e:
        return {"status": 500, "message": f"An error occurred: {str(e)}"}


@router.delete("/delete_message")
async def delete_telegram_message(chat_id: int, message_id: int):
    telegram_url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_url, data=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("ok"):
                        return {
                            "status": 200,
                            "message": "Message deleted successfully.",
                            "response_data": response_data,
                        }
                    else:
                        return {
                            "status": response.status,
                            "message": f"Failed to delete message: {response_data.get('description')}",
                        }
                else:
                    error_message = await response.text()
                    return {
                        "status": response.status,
                        "message": f"Failed to delete message: {error_message}",
                    }
    except Exception as e:
        return {"status": 500, "message": f"An error occurred: {str(e)}"}


@router.post("/edit_chat")
async def edit_message(dict_data: dict):
    telegram_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    # dict_data = data.dict()
    text = parse_order_message(dict_data["message"])
    status = dict_data["message"]["status"]
    inline_keyboard = None

    if status == "PAID":
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Подтвердить заказ",
                        "callback_data": f"order_confirm:{dict_data['message']['id']}",
                    },
                    {
                        "text": "❌ Отменить заказ",
                        "callback_data": f"order_cancel:{dict_data['message']['id']}",
                    },
                ]
            ]
        }
    elif status == "IN_PROGRESS":
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Выполнить заказ",
                        "callback_data": f"order_complete:{dict_data['message']['id']}",
                    },
                ]
            ]
        }
    payload = {
        "chat_id": data.chat_id,
        "message_id": data.message_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if inline_keyboard:
        payload["reply_markup"] = json.dumps(inline_keyboard)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_url, data=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return {
                        "status": 200,
                        "message": "Message edited successfully.",
                        "response_data": response_data,
                    }
                else:
                    error_message = await response.text()
                    return {
                        "status": response.status,
                        "message": f"Failed to edit message: {error_message}",
                    }
    except Exception as e:
        return {"status": 500, "message": f"An error occurred: {str(e)}"}
