import aiogram.types
import pydantic
import requests
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor

API_URL = "https://restcountries.com/v3.1"
TOKEN = "5834515976:AAExhTTab6JBixiQzS14B920A0f2xgQM5aU"

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

choose_keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True)
choose_keyboard.add("Поиск по названию", "Поиск по столице")


class Country(pydantic.BaseModel):
    name: str
    capital: str
    population: int
    area: float
    flag: str
    region: str
    subregion: str
    languages: list

    def __str__(self):
        return f"""
                [{self.name}]({self.flag}) - ___{self.region}___
                Регион: {self.region}
                Подрегион: {self.subregion}

                Население: ___{self.population}___
                Площадь: ___{self.area}___
                Языки: ___{', '.join(self.languages)}___

                """


class OneCountry(StatesGroup):
    query = State()


class OneCapital(StatesGroup):
    query = State()


def parse_object(input_country: dict) -> Country:
    return Country(name=input_country["name"]["official"], capital=input_country["capital"][0],
                   population=input_country["population"], area=input_country["area"],
                   flag=input_country["flags"]["png"],
                   region=input_country["region"], subregion=input_country["subregion"],
                   languages=list(input_country["languages"].keys()))


def get_country_by_name(country_name: str):
    response = requests.get(f"{API_URL}/name/{country_name}")
    if response.status_code != 200:
        return None
    response_body = response.json()
    country = parse_object(response_body[0])

    return country


def get_country_by_capital(capital_name: str):
    response = requests.get(f"{API_URL}/capital/{capital_name}")
    if response.status_code != 200:
        return None
    response_body = response.json()
    country = parse_object(response_body[0])

    return country


@dp.message_handler(commands=["start"])
async def welcome(message: aiogram.types.Message):
    await message.answer("Привет, я бот, который может показать тебе информацию о странах. "
                         "Напиши мне название страны, и я покажу тебе её информацию.",
                         reply_markup=choose_keyboard)


@dp.message_handler(lambda msg: msg.text == "Поиск по названию")
async def pre_get_country(message: aiogram.types.Message):
    await message.answer("Введите название страны на английском")
    await OneCountry.query.set()


@dp.message_handler(state=OneCountry.query)
async def get_country(message: aiogram.types.Message, state: FSMContext):
    country = get_country_by_name(message.text)
    if country is None:
        await message.answer("Страна не найдена")
    else:
        await message.answer(str(country), parse_mode=aiogram.types.ParseMode.MARKDOWN)
    await state.finish()


@dp.message_handler(lambda msg: msg.text == "Поиск по столице")
async def pre_get_by_capital(message: aiogram.types.Message):
    await message.answer("Введите название столицы на английском")
    await OneCapital.query.set()


@dp.message_handler(state=OneCapital.query)
async def get_country_capital(message: aiogram.types.Message, state: FSMContext):
    country = get_country_by_capital(message.text)
    if country is None:
        await message.answer("Страна не найдена")
    else:
        await message.answer(str(country), parse_mode=aiogram.types.ParseMode.MARKDOWN)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

