import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

# ---------------- CONFIG ----------------
TOKEN = "8206582920:AAGdbywxnZlCm2SaqHwfDM-2vbdHGl9cYkI"
ADMIN_ID = 6570342010
bot = Bot(TOKEN)
dp = Dispatcher()

# ---------------- DATABASE ----------------
conn = sqlite3.connect("taxi.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS drivers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    car TEXT,
    driver_id TEXT,
    route TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    direction TEXT,
    location TEXT,
    user_phone TEXT,
    status TEXT DEFAULT 'pending',
    accepted_by TEXT,
    created_at TEXT
)""")

conn.commit()

# ---------------- FSM States ----------------
class AddDriver(StatesGroup):  # Admin uchun
    name = State()
    phone = State()
    car = State()
    driver_id = State()
    route = State()

class RegisterDriver(StatesGroup):  # Haydovchi uchun
    name = State()
    phone = State()
    car = State()
    route = State()

class OrderTaxi(StatesGroup):
    direction = State()
    location = State()
    phone = State()

# ---------------- START ----------------
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    kb = [
        [InlineKeyboardButton(text="🚖 Farg'ona → Rishton", callback_data="order_FR")],
        [InlineKeyboardButton(text="🚖 Rishton → Farg'ona", callback_data="order_RF")],
        [InlineKeyboardButton(text="🚗 Haydovchi bo‘lib kirmoqchiman", callback_data="register_driver")]
    ]

    if msg.from_user.id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="➕ Admin haydovchi qo‘shish", callback_data="add_driver")])
        kb.append([InlineKeyboardButton(text="📋 Haydovchilar ro‘yxati", callback_data="all_drivers")])
        kb.append([InlineKeyboardButton(text="📦 Buyurtmalar ro‘yxati", callback_data="all_orders")])
        kb.append([InlineKeyboardButton(text="🗑 Haydovchini o‘chirish", callback_data="delete_driver")])
        kb.append([InlineKeyboardButton(text="📊 Statistika", callback_data="stats")])

    await msg.answer("🚖 Yo‘nalishni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ✅ Haydovchi ro‘yxatdan o‘tish
@dp.callback_query(F.data == "register_driver")
async def register_driver_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("👤 Ismingizni kiriting:")
    await state.set_state(RegisterDriver.name)

@dp.message(RegisterDriver.name)
async def driver_reg_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("📞 Telefon raqamingizni kiriting:")
    await state.set_state(RegisterDriver.phone)

@dp.message(RegisterDriver.phone)
async def driver_reg_phone(msg: types.Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    await msg.answer("🚗 Mashina markasini kiriting:")
    await state.set_state(RegisterDriver.car)

@dp.message(RegisterDriver.car)
async def driver_reg_car(msg: types.Message, state: FSMContext):
    await state.update_data(car=msg.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Farg‘ona → Rishton", callback_data="reg_route_FR")],
        [InlineKeyboardButton(text="Rishton → Farg‘ona", callback_data="reg_route_RF")],
        [InlineKeyboardButton(text="Ikkalasi ham", callback_data="reg_route_BOTH")]
    ])
    await msg.answer("🛣 Yo‘nalishni tanlang:", reply_markup=kb)
    await state.set_state(RegisterDriver.route)

@dp.callback_query(RegisterDriver.route, F.data.startswith("reg_route_"))
async def save_driver_registration(call: types.CallbackQuery, state: FSMContext):
    route = "FR" if call.data == "reg_route_FR" else "RF" if call.data == "reg_route_RF" else "BOTH"
    await state.update_data(route=route)
    data = await state.get_data()

    cursor.execute("INSERT INTO drivers(name, phone, car, driver_id, route) VALUES(?,?,?,?,?)",
                   (data["name"], data["phone"], data["car"], str(call.from_user.id), data["route"]))
    conn.commit()

    await call.message.answer("✅ Siz haydovchi sifatida ro‘yxatdan o‘tdingiz!")
    await state.clear()

# ✅ Admin haydovchi qo‘shishi
@dp.callback_query(F.data == "add_driver")
async def add_driver_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Sizda ruxsat yo‘q!")
    await call.message.answer("👤 Haydovchi ismini kiriting:")
    await state.set_state(AddDriver.name)

@dp.message(AddDriver.name)
async def add_driver_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("📞 Haydovchi telefon raqamini kiriting:")
    await state.set_state(AddDriver.phone)

@dp.message(AddDriver.phone)
async def add_driver_phone(msg: types.Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    await msg.answer("🚗 Mashina markasini kiriting:")
    await state.set_state(AddDriver.car)

@dp.message(AddDriver.car)
async def add_driver_car(msg: types.Message, state: FSMContext):
    await state.update_data(car=msg.text)
    await msg.answer("👤 Telegram ID ni kiriting:")
    await state.set_state(AddDriver.driver_id)

@dp.message(AddDriver.driver_id)
async def add_driver_id(msg: types.Message, state: FSMContext):
    await state.update_data(driver_id=msg.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Farg‘ona → Rishton", callback_data="admin_route_FR")],
        [InlineKeyboardButton(text="Rishton → Farg‘ona", callback_data="admin_route_RF")],
        [InlineKeyboardButton(text="Ikkalasi ham", callback_data="admin_route_BOTH")]
    ])
    await msg.answer("🛣 Yo‘nalishni tanlang:", reply_markup=kb)
    await state.set_state(AddDriver.route)

@dp.callback_query(AddDriver.route, F.data.startswith("admin_route_"))
async def save_driver_admin(call: types.CallbackQuery, state: FSMContext):
    route = "FR" if call.data == "admin_route_FR" else "RF" if call.data == "admin_route_RF" else "BOTH"
    await state.update_data(route=route)
    data = await state.get_data()
    cursor.execute("INSERT INTO drivers(name, phone, car, driver_id, route) VALUES(?,?,?,?,?)",
                   (data["name"], data["phone"], data["car"], data["driver_id"], route))
    conn.commit()
    await call.message.answer("✅ Haydovchi qo‘shildi!")
    await state.clear()


@dp.callback_query(F.data == "all_drivers")
async def all_drivers(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Sizda ruxsat yo‘q!")
    cursor.execute("SELECT name, phone, car, route FROM drivers")
    drivers = cursor.fetchall()
    if drivers:
        text = "📋 Haydovchilar ro‘yxati:\n\n"
        for d in drivers:
            route = d[3].replace("FR", "Farg‘ona→Rishton").replace("RF", "Rishton→Farg‘ona").replace("BOTH", "Ikkalasi ham")
            text += f"👤 {d[0]}\n📞 {d[1]}\n🚗 {d[2]}\n🛣 Yo‘nalish: {route}\n\n"
        await call.message.answer(text)
    else:
        await call.message.answer("❌ Hozircha haydovchilar yo‘q!")

# ✅ Qo‘shimcha ADMIN FUNKSIYALARI:
@dp.callback_query(F.data == "all_orders")
async def all_orders(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Sizda ruxsat yo‘q!")
    cursor.execute("SELECT id, direction, location, user_phone, status FROM orders ORDER BY id DESC LIMIT 10")
    orders = cursor.fetchall()
    if orders:
        text = "📦 So‘nggi 10 ta buyurtma:\n\n"
        for o in orders:
            direction = "Farg‘ona→Rishton" if o[1] == "FR" else "Rishton→Farg‘ona"
            text += f"📌 ID: {o[0]}\n🛣 {direction}\n📍 {o[2]}\n📞 {o[3]}\n📋 Holat: {o[4]}\n\n"
        await call.message.answer(text)
    else:
        await call.message.answer("❌ Buyurtmalar yo‘q!")

@dp.callback_query(F.data == "delete_driver")
async def delete_driver_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Sizda ruxsat yo‘q!")
    cursor.execute("SELECT id, name FROM drivers")
    drivers = cursor.fetchall()
    if not drivers:
        return await call.message.answer("❌ Haydovchilar yo‘q!")
    kb = InlineKeyboardMarkup()
    for d in drivers:
        kb.add(InlineKeyboardButton(text=f"❌ {d[1]}", callback_data=f"del_{d[0]}"))
    await call.message.answer("🗑 O‘chirish uchun haydovchini tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith("del_"))
async def confirm_delete_driver(call: types.CallbackQuery):
    driver_id = int(call.data.split("_")[1])
    cursor.execute("DELETE FROM drivers WHERE id=?", (driver_id,))
    conn.commit()
    await call.answer("✅ Haydovchi o‘chirildi!", show_alert=True)
    await call.message.delete()

@dp.callback_query(F.data == "stats")
async def show_stats(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Sizda ruxsat yo‘q!")
    cursor.execute("SELECT COUNT(*) FROM drivers")
    drivers_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='accepted'")
    accepted_orders = cursor.fetchone()[0]
    text = f"📊 Statistika:\n\n👥 Haydovchilar: {drivers_count}\n📦 Buyurtmalar: {orders_count}\n✅ Qabul qilingan: {accepted_orders}"
    await call.message.answer(text)

# ✅ BUYURTMA QISMI (eski kod)
@dp.callback_query(F.data.startswith("order_"))
async def order_handler(call: types.CallbackQuery, state: FSMContext):
    direction = "FR" if call.data == "order_FR" else "RF"
    await state.update_data(direction=direction)
    await state.set_state(OrderTaxi.location)
    await call.message.answer("📍 Manzilingizni kiriting:")

@dp.message(OrderTaxi.location)
async def get_location(msg: types.Message, state: FSMContext):
    await state.update_data(location=msg.text)
    await msg.answer("📞 Telefon raqamingizni kiriting:")
    await state.set_state(OrderTaxi.phone)

@dp.message(OrderTaxi.phone)
async def get_phone(msg: types.Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    data = await state.get_data()
    user_id = msg.from_user.id
    direction = data["direction"]
    location = data["location"]
    phone = data["phone"]

    cursor.execute("INSERT INTO orders(user_id, direction, location, user_phone, created_at) VALUES(?,?,?,?,?)",
                   (user_id, direction, location, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    order_id = cursor.lastrowid
    conn.commit()

    await msg.answer("✅ Buyurtmangiz qabul qilindi! Haydovchilar bilan bog‘lanmoqda...")
    await state.clear()

    cursor.execute("SELECT driver_id FROM drivers WHERE route=? OR route='BOTH'", (direction,))
    drivers = cursor.fetchall()
    if drivers:
        for d in drivers:
            driver_chat_id = int(d[0])
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{order_id}")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
            ])
            text = f"🚖 <b>Yangi buyurtma!</b>\n\n📍 Yo‘nalish: {'Farg‘ona→Rishton' if direction == 'FR' else 'Rishton→Farg‘ona'}\n📌 Manzil: {location}"
            try:
                await bot.send_message(driver_chat_id, text, parse_mode="HTML", reply_markup=kb)
            except:
                pass
    else:
        await msg.answer("❌ Hozircha haydovchilar yo‘q!")

@dp.callback_query(F.data.startswith("phone_"))
async def send_phone(call: types.CallbackQuery):
    order_id = int(call.data.split("_")[1])
    cursor.execute("SELECT user_phone FROM orders WHERE id=?", (order_id,))
    phone = cursor.fetchone()
    if phone:
        await call.answer("✅ Telefon raqami yuborildi!", show_alert=True)
        await call.message.answer(f"📞 Buyurtmachi telefon raqami: (+998) {phone[0]}")
    else:
        await call.answer("❌ Telefon raqami topilmadi!", show_alert=True)

@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(call: types.CallbackQuery):
    order_id = int(call.data.split("_")[1])
    cursor.execute("SELECT status, user_id, direction, location FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()
    if not order:
        return await call.answer("❌ Buyurtma topilmadi!", show_alert=True)
    status, user_id, direction, location = order
    if status != "pending":
        return await call.answer("❌ Buyurtma allaqachon qabul qilingan!", show_alert=True)

    cursor.execute("UPDATE orders SET status='accepted', accepted_by=? WHERE id=?", (call.from_user.id, order_id))
    conn.commit()

    cursor.execute("SELECT name, phone, car FROM drivers WHERE driver_id=?", (str(call.from_user.id),))
    driver = cursor.fetchone()
    if not driver:
        return await call.answer("❌ Haydovchi ma’lumotlari topilmadi!", show_alert=True)

    driver_name, driver_phone, driver_car = driver

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Telegram orqali", url=f"tg://user?id={user_id}")],
        [InlineKeyboardButton(text="📞 Qo‘ng‘iroq orqali", callback_data=f"phone_{order_id}")]
    ])
    await call.message.edit_text("✅ Buyurtmani qabul qildingiz!\nBog‘lanish usulini tanlang:", reply_markup=kb)

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Buyurtmangizni haydovchi qabul qildi!\n\n👤 Ismi: <b>{driver_name}</b>\n📞 Telefon: <b>{driver_phone}</b>\n🚗 Mashina: <b>{driver_car}</b>",
            parse_mode="HTML"
        )
    except:
        pass

    cursor.execute("SELECT driver_id FROM drivers WHERE route=? OR route='BOTH'", (direction,))
    all_drivers = cursor.fetchall()
    for d in all_drivers:
        driver_chat_id = int(d[0])
        if driver_chat_id != call.from_user.id:
            try:
                await bot.send_message(driver_chat_id, "❌ Buyurtma boshqa haydovchi tomonidan qabul qilindi!")
            except:
                pass

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
