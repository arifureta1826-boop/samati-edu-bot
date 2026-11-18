import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "8101370403:AAEERl5Juy6-wxKrSCku-0Hng_8I99R6UG8"

# Adminlarning Telegram ID raqamlari ro'yxati
ADMIN_IDS = [7193226157 ,  1013283682]  

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_data = State()

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ozbekiston_eng_yangi_tarixi_1 TEXT,
            ozbekiston_eng_yangi_tarixi_2 TEXT,
            ozbekiston_eng_yangi_tarixi_3 TEXT,
            ozbekiston_eng_yangi_tarixi_4 TEXT,
            dinshunoslik_1 TEXT,
            dinshunoslik_2 TEXT,
            dinshunoslik_3 TEXT,
            dinshunoslik_4 TEXT,
            falsafa_1 TEXT,
            falsafa_2 TEXT,
            falsafa_3 TEXT,
            falsafa_4 TEXT,
            pedagogik_interfaol_metodlar TEXT,
            ozbekiston_tarixi_adabiyotlar TEXT,
            falsafa_adabiyotlar TEXT,
            dinshunoslik_adabiyotlar TEXT,
            ijodkor_talabalar TEXT,
            qoshimcha_adabiyotlar TEXT,
            izohli_lugat TEXT,
            video_darslar TEXT,
            namunaviy_darslar TEXT,
            lohiya_muallifi TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM materials")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO materials DEFAULT VALUES")
    conn.commit()
    conn.close()

# Asosiy menyu tugmalari va ularning bazadagi nomlari
COLUMNS = {
    "🇺🇿 O'zb. eng yangi tarixi": "ozbekiston_eng_yangi_tarixi",
    "🕌 Dinshunoslik": "dinshunoslik",
    "🧠 Falsafa": "falsafa",
    "📊 Pedagogik metodlar": "pedagogik_interfaol_metodlar",
    "📚 O'zb. tarixi adabiyot": "ozbekiston_tarixi_adabiyotlar",
    "📖 Falsafa adabiyot": "falsafa_adabiyotlar",
    "📘 Dinshunoslik adabiyot": "dinshunoslik_adabiyotlar",
    "✍️ Ijodkor talabalar": "ijodkor_talabalar",
    "📁 Qo'shimcha adabiyot": "qoshimcha_adabiyotlar",
    "🔍 Izohli lug'at": "izohli_lugat",
    "🎬 Video darslar": "video_darslar",
    "📋 Namunaviy darslar": "namunaviy_darslar",
    "👨‍💻 Loyiha muallifi": "lohiya_muallifi",
}

# 4 ta bosqichga ega bo'lgan fanlar bazadagi nomlari
SUB_SUBJECTS_DB = ["ozbekiston_eng_yangi_tarixi", "dinshunoslik", "falsafa"]

@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    
    keys = list(COLUMNS.keys())
    keyboard_buttons = []
    for i in range(0, len(keys), 2):
        row = [KeyboardButton(text=keys[i])]
        if i + 1 < len(keys):
            row.append(KeyboardButton(text=keys[i+1]))
        keyboard_buttons.append(row)
    
    if user_id in ADMIN_IDS:
        keyboard_buttons.append([KeyboardButton(text="✏️ Ma'lumot qo'shish/o'zgartirish")])

    markup = ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )
    
    await message.answer("📚 Kerakli bo'limni pastdagi tugmalardan tanlang:", reply_markup=markup)

@dp.message(F.text == "✏️ Ma'lumot qo'shish/o'zgartirish")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    buttons = [
        [InlineKeyboardButton(text=f"Tahrirlash: {title}", callback_data=f"edit_main_{db_col}")]
        for title, db_col in COLUMNS.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Qaysi bo'limga ma'lumot kiritmoqchisiz? Tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("edit_main_"))
async def edit_main_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    db_col = callback.data.replace("edit_main_", "")
    
    if db_col in SUB_SUBJECTS_DB:
        buttons = [
            [InlineKeyboardButton(text="1-bosqich", callback_data=f"edit_sub_{db_col}_1")],
            [InlineKeyboardButton(text="2-bosqich", callback_data=f"edit_sub_{db_col}_2")],
            [InlineKeyboardButton(text="3-bosqich", callback_data=f"edit_sub_{db_col}_3")],
            [InlineKeyboardButton(text="4-bosqich", callback_data=f"edit_sub_{db_col}_4")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text("Qaysi bosqich uchun ma'lumot kiritasiz?", reply_markup=keyboard)
    else:
        title = next((k for k, v in COLUMNS.items() if v == db_col), db_col)
        await state.update_data(target_column=db_col, title=title)
        await state.set_state(Form.waiting_for_data)
        await callback.message.delete()
        await callback.message.answer(f"✍️ <b>{title}</b> uchun yangi ma'lumotni yuboring:", parse_mode="HTML")
    
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_sub_"))
async def edit_sub_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    # edit_sub_ozbekiston_eng_yangi_tarixi_1 formatini qismga ajratamiz
    data_parts = callback.data.replace("edit_sub_", "").rsplit("_", 1)
    db_col = data_parts[0]
    course = data_parts[1]
    
    target_column = f"{db_col}_{course}"
    base_title = next((k for k, v in COLUMNS.items() if v == db_col), db_col)
    title = f"{base_title} ({course}-bosqich)"

    await state.update_data(target_column=target_column, title=title)
    await state.set_state(Form.waiting_for_data)
    
    await callback.message.delete()
    await callback.message.answer(f"✍️ <b>{title}</b> uchun yangi ma'lumotni yuboring:", parse_mode="HTML")
    await callback.answer()

@dp.message(Form.waiting_for_data)
async def save_user_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    user_data = await state.get_data()
    target_column = user_data.get("target_column")
    title = user_data.get("title")
    text = message.text

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE materials SET {target_column} = ? WHERE id = 1", (text,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ <b>{title}</b> bo'limiga ma'lumot muvaffaqiyatli saqlandi!", parse_mode="HTML")

@dp.message(F.text.in_(COLUMNS.keys()))
async def show_material(message: Message):
    title = message.text
    db_column = COLUMNS[title]

    if db_column in SUB_SUBJECTS_DB:
        buttons = [
            [InlineKeyboardButton(text="1-bosqich", callback_data=f"show_{db_column}_1")],
            [InlineKeyboardButton(text="2-bosqich", callback_data=f"show_{db_column}_2")],
            [InlineKeyboardButton(text="3-bosqich", callback_data=f"show_{db_column}_3")],
            [InlineKeyboardButton(text="4-bosqich", callback_data=f"show_{db_column}_4")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"🎓 <b>{title}</b> bo'yicha kerakli bosqichni tanlang:", parse_mode="HTML", reply_markup=keyboard)
    else:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute(f"SELECT {db_column} FROM materials WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        content = row[0] if row and row[0] else "⚠️ Bu bo'limga hali ma'lumot kiritilmagan."
        await message.answer(f"📖 <b>{title}</b>:\n\n{content}", parse_mode="HTML")

@dp.callback_query(F.data.startswith("show_"))
async def show_course_material(callback: CallbackQuery):
    data_parts = callback.data.replace("show_", "").rsplit("_", 1)
    db_col = data_parts[0]
    course = data_parts[1]
    
    target_column = f"{db_col}_{course}"
    base_title = next((k for k, v in COLUMNS.items() if v == db_col), db_col)
    title = f"{base_title} ({course}-bosqich)"

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT {target_column} FROM materials WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    content = row[0] if row and row[0] else "⚠️ Bu bosqichga hali ma'lumot kiritilmagan."
    
    await callback.message.answer(f"📖 <b>{title}</b>:\n\n{content}", parse_mode="HTML")
    await callback.answer()

async def main():
    init_db()
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())