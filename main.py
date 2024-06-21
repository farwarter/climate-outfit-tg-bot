import math
import requests
import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

# Инициализация бота и диспетчера
bot = Bot(token='YOUR_BOT_TOKEN')
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет! Напиши мне название города, и я пришлю сводку погоды.")

# определяем направление ветра
def wind_direction(deg):
    if deg is not None:
        val = int((deg / 22.5) + 0.5)
        directions = ["северный", "северо-восточный", "восточный", "юго-восточный", "южный", "юго-западный", "западный", "северо-западный"]
        return directions[(val % 8)]
    return "направление неизвестно"

# настраиваем рекомендации в зависимости от полученных данных
def get_clothing_recommendation(temp, humidity, wind_speed, weather_description):
    recommendations = []

    # Температура
    if temp < 0:
        recommendations.append("теплая зимняя куртка, шарф, шапка и перчатки")
    elif 0 <= temp < 10:
        recommendations.append("легкая зимняя куртка или пальто, шарф и перчатки")
    elif 10 <= temp < 20:
        recommendations.append("куртка или свитер")
    elif 20 <= temp < 30:
        recommendations.append("футболка и легкие брюки или шорты/юбка, легкое платье")
    else:
        recommendations.append("Легкая одежда, шорты и майка")

    # Влажность
    if humidity > 80:
        recommendations.append("водонепроницаемая одежда и обувь")

    # Скорость ветра
    if wind_speed > 10:
        recommendations.append("ветрозащитная куртка")

    # Описание погоды
    if "дождь" in weather_description:
        recommendations.append("зонтик или дождевик")
    elif "снег" in weather_description:
        recommendations.append("теплая водонепроницаемая обувь")

    # Пасмурно или солнечно
    if "ясно" in weather_description or "солнечно" in weather_description:
        recommendations.append("солнцезащитные очки и светлый головной убор. Не забудьте солнцезащитный крем!")

    return "Рекомендации по одежде: " + ", ".join(recommendations)

# Обработчик для получения погоды
@dp.message_handler()
async def get_weather(message: types.Message):
    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={message.text}&lang=ru&units=metric&appid=YOUR_OPENWEATHER_KEY"
        )
        data = response.json()

        if response.status_code == 200:
            city = data['name']
            country = data['sys']['country']
            state = data.get('state', '')
            temp = round(data['main']['temp'])
            weather_description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            wind_speed = round(data['wind']['speed'], 1)
            wind_deg = data['wind']['deg']
            wind_dir = wind_direction(wind_deg) # текстовое обозначение направления ветра
            sunrise_timestamp = data['sys']['sunrise']
            sunset_timestamp = data['sys']['sunset']

            # полное название местоположения, включая город, область (если доступно) и страну
            location_info = f"{city}, {country}"
            if state:
                location_info = f"{city}, {state}, {country}"

            # Получаем временную зону города
            lat = data['coord']['lat']
            lon = data['coord']['lon']
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=lon, lat=lat)
            local_tz = pytz.timezone(timezone_str)

            # Преобразуем время восхода и заката в местное время
            sunrise_local = datetime.fromtimestamp(sunrise_timestamp, local_tz).strftime('%H:%M:%S, %d.%m.%Y')
            sunset_local = datetime.fromtimestamp(sunset_timestamp, local_tz).strftime('%H:%M:%S, %d.%m.%Y')
          
            length_of_the_day = str(datetime.fromtimestamp(sunset_timestamp) - datetime.fromtimestamp(sunrise_timestamp))

            clothing_recommendation = get_clothing_recommendation(temp, humidity, wind_speed, weather_description)

            await message.reply(f"Погода в городе {location_info}:\n\n"
                                f"Температура: {temp}°C, {weather_description}\n"
                                f"Влажность: {humidity}%\n"
                                f"Давление: {math.ceil(pressure/1.333)} мм.рт.ст\n"
                                f"Ветер: {wind_speed} м/с, {wind_dir}\n\n"
                                f"Восход солнца (местное время): {sunrise_local}\n"
                                f"Закат солнца (местное время): {sunset_local}\n"
                                f"Продолжительность дня: {length_of_the_day}\n\n"
                                f"{clothing_recommendation}\n\n"
                                f"Хорошего дня!")

        else:
            await message.reply("Город не найден, пожалуйста, проверьте название.")
    except Exception as e:
        await message.reply("Произошла ошибка при получении данных о погоде!")

# запуск бота
if __name__ == "__main__": # Проверка, что скрипт запускается непосредственно, а не импортируется как модуль
    executor.start_polling(dp, skip_updates=True) # С помощью метода executor.start_polling опрашиваем Dispatcher: ожидаем команду /start
