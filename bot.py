import asyncio
from urllib.parse import urlencode, urljoin

import requests
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.core.settings import settings
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import aiohttp


load_dotenv()
EXTERNAL_API_URL = settings.EXTERNAL_API_URL
API_CHECK_PHONE = settings.EXTERNAL_API_CHECK_ACCESS
bot_key = settings.BOT
bot = Bot(token=bot_key)

router = Router()

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)


class Authorization(StatesGroup):
    waiting_for_phone_number = State()


@router.message(CommandStart())
async def process_start_command(message: types.Message, state: FSMContext):
    """Обрабатывает команду /start, инициирует процесс авторизации."""
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Поделиться номером", request_contact=True))

    await state.set_state(Authorization.waiting_for_phone_number)
    await message.answer(
        "Привет! Вы можете поделиться своим номером телефона или ввести его вручную.",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@router.message(F.contact, Authorization.waiting_for_phone_number)
async def process_contact(message: types.Message, state: FSMContext):
    """Обрабатывает отправленный контакт."""
    phone_number = message.contact.phone_number
    user_id = message.from_user.id

    await message.reply(
        "Проверяем ваш номер телефона...", reply_markup=ReplyKeyboardRemove()
    )
    await authorize_phone(phone_number, user_id, message, state)


async def authorize_phone(
    phone_number: str, user_id: int, message: types.Message, state: FSMContext
):
    """Функция для проверки номера телефона через внешний API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_CHECK_PHONE,
                json={"phone_number": phone_number, "user_id": user_id},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    is_authorized = data.get("authorized", False)

                    if is_authorized:
                        await message.reply(
                            "Вы успешно авторизованы. Теперь вы будете получать уведомления."
                        )
                    else:
                        await message.reply(
                            "Ваш номер телефона не зарегистрирован в нашей базе. Пожалуйста обратитесь за помощью в службу поддержки Book-Eat."
                        )
                else:
                    await message.reply(
                        "Произошла ошибка при проверке номера телефона."
                    )
    except Exception as e:
        await message.reply(f"Произошла ошибка {e}. Попробуйте позже.")
    finally:
        await state.clear()


@router.message(Command(commands=["/cancel"]))
async def cancel_authorization(message: types.Message, state: FSMContext):
    """Команда /cancel отменяет процесс авторизации."""
    await state.clear()
    await message.reply("Процесс авторизации отменен.")


@router.message()
async def ignore_messages(message: types.Message, state: FSMContext):
    """Игнорирует любые сообщения, кроме команд /start и /cancel."""
    if message.text == "/cancel":
        await cancel_authorization(message, state)
        return

    current_state = await state.get_state()

    if current_state:
        await message.reply(
            "Я вас не понимаю. Пожалуйста, используйте команду /start для начала авторизации или /cancel для отмены."
        )
    else:
        await message.reply(
            "Добро пожаловать в нашего бота. Пожалуйста введите команду /start чтобы начать авторизацию. Если вы уже авторизированны - ожидайте уведомлений о заказах."
        )


async def send_request_to_url(url, params=None):
    """Отправка HTTP-запроса на внешний URL."""
    try:
        external_url = urljoin(EXTERNAL_API_URL, url)
        if params:
            query_string = urlencode(params)
            external_url = f"{external_url}?{query_string}"
        async with aiohttp.ClientSession() as session:
            async with session.put(external_url) as response:
                if response.status == 200:
                    return {"success": True, "message": "Request successful"}
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send request. Status: {response.status}",
                    }
    except Exception as e:
        return {"success": False, "message": f"Error sending request: {e}"}


@dp.callback_query(lambda c: c.data and c.data.startswith("order"))
async def handle_order_callback(callback_query: types.CallbackQuery):
    """Обрабатывает нажатие кнопки для подтверждения/отмены заказа."""
    callback_data = callback_query.data

    try:
        action, order_id = callback_data.split(":", 1)
    except ValueError:
        await callback_query.answer("Некорректный формат данных")
        return

    if action == "order_confirm":
        status = "IN_PROGRESS"
        message = "Вы подтвердили заказ, ожидайте уведомлений."
    elif action == "order_cancel":
        status = "CANCELLED_BY_PROVIDER"
        message = "Вы отменили заказ."
    elif action == "order_complete":
        status = "COMPLETED"
        message = "Вы выполнили заказ."
    else:
        status = "UNKNOWN"
        message = "Произошла ошибка при обработке статуса заказа"

    url = f"/v1/orders/{order_id}/status?status={status}"
    response = await send_request_to_url(url)

    if response["success"]:
        await bot.send_message(callback_query.message.chat.id, message)
    else:
        error_message = "Не удалось выполнить действие. Попробуйте позже"
        await bot.send_message(callback_query.message.chat.id, error_message)

    await callback_query.answer(
        message if response["success"] else "Действие не выполнено."
    )


async def main() -> None:

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
