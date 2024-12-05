import json

from dotenv import load_dotenv
from fastapi import APIRouter

import aiohttp

from api_routes.py_models import InputData, SendChatRequest
from src.core.settings import settings
from api_routes.parse_utills import parse_order_message

load_dotenv()
bot_token = settings.BOT
router = APIRouter(prefix="/test", tags=["test API endpoints"])


@router.post("/check_access")
async def send_from_telegram(data: InputData):
    numbers = ["12345", "43213", "22333"]
    if data.phone_number in numbers:
        print(f"пользователь с user_id:{data.user_id}")
        return {"authorized": True}
    return {"authorized": False}


@router.post("/send_chat")
async def send_to_telegram(data: SendChatRequest):
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    dict_data = data.dict()
    text, inline_keyboard = parse_order_message(dict_data["message"])
    payload = {
        "chat_id": data.chat_id,
        "text": text,
        "reply_markup": json.dumps(inline_keyboard),
        "parse_mode": "Markdown",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_url, data=payload) as response:
                if response.status == 200:
                    return {
                        "status": 200,
                        "message": "Message sent to Telegram successfully.",
                    }
                else:
                    error_message = await response.text()
                    return {
                        "status": response.status,
                        "message": f"Failed to send message to Telegram: {error_message}",
                    }
    except Exception as e:
        return {"status": 500, "message": f"An error occurred: {str(e)}"}
