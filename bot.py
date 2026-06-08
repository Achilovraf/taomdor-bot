import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

STATUS_LABELS = {
    "yangi": "🆕 Yangi",
    "tayyorlanmoqda": "👨‍🍳 Tayyorlanmoqda",
    "yetkazilmoqda": "🛵 Yetkazilmoqda",
    "yetkazildi": "✅ Yetkazildi",
    "bekor": "❌ Bekor qilindi"
}

def admin_keyboard(order_id: int, current_status: str) -> InlineKeyboardMarkup:
    buttons = []
    statuses = ["yangi", "tayyorlanmoqda", "yetkazilmoqda", "yetkazildi", "bekor"]
    row = []
    for status in statuses:
        if status != current_status:
            row.append(InlineKeyboardButton(
                text=STATUS_LABELS[status],
                callback_data=f"status:{order_id}:{status}"
            ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def format_order_for_admin(order: dict) -> str:
    status = STATUS_LABELS.get(order['status'], order['status'])
    text = (
        f"📦 *Buyurtma #{order['id']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 *Ism:* {order['name']}\n"
        f"📞 *Telefon:* {order['phone']}\n"
        f"📍 *Manzil:* {order['address']}\n"
        f"💳 *To'lov:* {order['payment']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🍽 *Taomlar:*\n{order['items']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami:* {order['total']}\n"
        f"📊 *Holat:* {status}\n"
        f"🕐 *Vaqt:* {order['created_at']}"
    )
    if order.get('comment'):
        text += f"\n💬 *Izoh:* {order['comment']}"
    return text

@dp.message()
async def handle_message(message: types.Message):
    text = message.text or ""
    
    # Buyurtma xabarini parse qilish
    if "📦 Yangi buyurtma" in text or "Buyurtma" in text:
        order_data = parse_order(text)
        if order_data:
            order_id = db.save_order(
                name=order_data.get('name', 'Noma\'lum'),
                phone=order_data.get('phone', '—'),
                address=order_data.get('address', '—'),
                payment=order_data.get('payment', '—'),
                items=order_data.get('items', '—'),
                total=order_data.get('total', '—'),
                comment=order_data.get('comment', ''),
                chat_id=message.chat.id
            )
            
            # Mijozga tasdiqlash
            await message.reply(
                f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
                f"Buyurtma raqami: *#{order_id}*\n"
                f"Tez orada operatorimiz siz bilan bog'lanadi.\n\n"
                f"📞 Savol bo'lsa: +998 50 772-72-72",
                parse_mode="Markdown"
            )
            
            # Adminlarga xabar
            order = db.get_order(order_id)
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        format_order_for_admin(order),
                        parse_mode="Markdown",
                        reply_markup=admin_keyboard(order_id, "yangi")
                    )
                except Exception as e:
                    logger.error(f"Admin ga xabar yuborishda xato: {e}")
        else:
            # Oddiy xabar — adminlarga yo'naltirish
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"📨 *Yangi xabar:*\n\n{text}\n\n"
                        f"От: {message.from_user.full_name} (ID: {message.chat.id})",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Xato: {e}")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.data.startswith("status:"):
        _, order_id, new_status = callback.data.split(":")
        order_id = int(order_id)
        
        old_order = db.get_order(order_id)
        db.update_status(order_id, new_status)
        order = db.get_order(order_id)
        
        # Admin xabarini yangilash
        await callback.message.edit_text(
            format_order_for_admin(order),
            parse_mode="Markdown",
            reply_markup=admin_keyboard(order_id, new_status)
        )
        
        # Mijozga holat haqida xabar
        status_label = STATUS_LABELS.get(new_status, new_status)
        if order['chat_id']:
            try:
                await bot.send_message(
                    order['chat_id'],
                    f"📦 *Buyurtma #{order_id} holati yangilandi*\n\n"
                    f"Yangi holat: {status_label}\n\n"
                    f"📞 Savol: +998 50 772-72-72",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Mijozga xabar yuborishda xato: {e}")
        
        await callback.answer(f"Holat o'zgartirildi: {status_label}")

@dp.message(Command("orders"))
async def cmd_orders(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    orders = db.get_recent_orders(status="yangi")
    if not orders:
        await message.answer("🆕 Yangi buyurtmalar yo'q.")
        return
    for order in orders:
        await message.answer(
            format_order_for_admin(order),
            parse_mode="Markdown",
            reply_markup=admin_keyboard(order['id'], order['status'])
        )

@dp.message(Command("all"))
async def cmd_all(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    orders = db.get_recent_orders(limit=10)
    if not orders:
        await message.answer("Buyurtmalar yo'q.")
        return
    for order in orders:
        await message.answer(
            format_order_for_admin(order),
            parse_mode="Markdown",
            reply_markup=admin_keyboard(order['id'], order['status'])
        )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    stats = db.get_stats()
    await message.answer(
        f"📊 *Statistika*\n\n"
        f"📦 Jami buyurtmalar: {stats['total']}\n"
        f"🆕 Yangi: {stats['yangi']}\n"
        f"👨‍🍳 Tayyorlanmoqda: {stats['tayyorlanmoqda']}\n"
        f"🛵 Yetkazilmoqda: {stats['yetkazilmoqda']}\n"
        f"✅ Yetkazildi: {stats['yetkazildi']}\n"
        f"❌ Bekor: {stats['bekor']}",
        parse_mode="Markdown"
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "👨‍💼 *Admin panel*\n\n"
            "/orders — Yangi buyurtmalar\n"
            "/all — Oxirgi 10 buyurtma\n"
            "/stats — Statistika",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🍽 *Taomdor botiga xush kelibsiz!*\n\n"
            "Buyurtma berish uchun saytimizga o'ting:\n"
            "📞 +998 50 772-72-72",
            parse_mode="Markdown"
        )

def parse_order(text: str) -> dict:
    """Saytdan kelgan buyurtma matnini parse qilish"""
    data = {}
    lines = text.split('\n')
    
    items_lines = []
    in_items = False
    
    for line in lines:
        line = line.strip()
        if '👤' in line or 'Ism:' in line:
            data['name'] = line.split(':', 1)[-1].strip()
        elif '📞' in line or 'Telefon:' in line:
            data['phone'] = line.split(':', 1)[-1].strip()
        elif '📍' in line or 'Manzil:' in line:
            data['address'] = line.split(':', 1)[-1].strip()
        elif '💳' in line or "To'lov:" in line or 'Tolov:' in line:
            data['payment'] = line.split(':', 1)[-1].strip()
        elif '💬' in line or 'Izoh:' in line:
            data['comment'] = line.split(':', 1)[-1].strip()
        elif '💰' in line or 'Jami:' in line:
            data['total'] = line.split(':', 1)[-1].strip()
            in_items = False
        elif '🍽' in line or 'Taomlar:' in line:
            in_items = True
        elif in_items and line and '━' not in line:
            items_lines.append(line)
    
    if items_lines:
        data['items'] = '\n'.join(items_lines)
    
    return data if data.get('name') or data.get('phone') else None

async def main():
    db.init()
    logger.info("🤖 Taomdor Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
