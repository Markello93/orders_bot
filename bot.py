import asyncio
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from src.core.settings import settings
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import aiohttp

from src.utills import validate_phone

load_dotenv()
EXTERNAL_API_URL = settings.EXTERNAL_API_URL
bot_key = settings.BOT
bot = Bot(token=bot_key)

router = Router()


class Authorization(StatesGroup):
    waiting_for_phone_number = State()


@router.message(CommandStart())
async def process_start_command(message: types.Message, state: FSMContext):
    """Обрабатывает команду /start, инициирует процесс авторизации."""
    await state.set_state(Authorization.waiting_for_phone_number)
    await message.reply(
        "Привет! Пожалуйста, введите ваш номер телефона для авторизации."
    )


@router.message(Authorization.waiting_for_phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    """Обрабатывает номер телефона, проверяет его на внешнем API."""
    phone_number = message.text
    user_id = message.from_user.id
    if message.text.lower() == "/cancel":
        await state.clear()
        await message.reply(
            "Процесс авторизации прерван. Если вы хотите авторизоваться используйте команду /start "
        )
        return
    try:
        validate_phone(phone_number)
    except ValueError as e:
        await message.reply(
            str(e) + " Если вы хотите отменить процесс, используйте команду /cancel."
        )
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                EXTERNAL_API_URL,
                json={"phone_number": phone_number, "user_id": user_id},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    is_authorized = data.get("authorized", True)

                    if is_authorized:
                        await message.reply(
                            "Вы успешно авторизованы. Теперь вы будете получать уведомления."
                        )
                    else:
                        await message.reply(
                            "Ваш номер телефона не авторизован. Попробуйте снова."
                        )
                else:
                    await message.reply(
                        "Произошла ошибка при проверке номера телефона."
                    )
    except Exception as e:
        await message.reply(
            f"Произошла ошибка {e} при проверке номера. Попробуйте позже."
        )
    await state.clear()


@router.message(Command(commands=["/cancel"]))
async def cancel_authorization(message: types.Message, state: FSMContext):
    """Команда /cancel отменяет процесс авторизации."""
    await state.clear()
    await message.reply("Процесс авторизации отменен.")


@router.message()
async def ignore_messages(message: types.Message, state: FSMContext):
    """Игнорирует все сообщения от неавторизованных пользователей."""
    current_state = await state.get_state()

    if current_state == Authorization.waiting_for_phone_number.state:
        await message.reply(
            "Пожалуйста, введите номер телефона для авторизации. Если хотите отменить, используйте /cancel."
        )
    else:
        await message.reply(
            "Если вы хотите начать процесс авторизации, используйте команду /start."
        )


async def main() -> None:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
