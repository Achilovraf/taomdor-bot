import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from database import Database
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
db = Database()

STATUS_LABELS = {
    "yangi": "🆕 Yangi",
    "tayyorlanmoqda": "👨‍🍳 Tayyorlanmoqda",
    "yetkazilmoqda": "🛵 Yetkazilmoqda",
    "yetkazildi": "✅ Yetkazildi",
    "bekor": "❌ Bekor"
}

def admin_keyboard(order_id, current_status):
    buttons = []
    row = []
    for status, label in STATUS_LABELS.items():
        if status != current_status:
            row.append(InlineKeyboardButton(label, callback_data=f"status:{order_id}:{status}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def format_order(order):
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

def parse_order(text):
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
        elif '💳' in line or "To'lov:" in line:
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

async def handle_message(update: Update, context):
    text = update.message.text or ""
    chat_id = update.message.chat_id

    if "Buyurtma" in text or "buyurtma" in text or "📦" in text:
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
                chat_id=chat_id
            )
            await update.message.reply_text(
                f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
                f"Buyurtma raqami: *#{order_id}*\n"
                f"Tez orada operatorimiz siz bilan bog'lanadi.\n\n"
                f"📞 Savol bo'lsa: +998 50 772\\-72\\-72",
                parse_mode="MarkdownV2"
            )
            order = db.get_order(order_id)
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        format_order(order),
                        parse_mode="Markdown",
                        reply_markup=admin_keyboard(order_id, "yangi")
                    )
                except Exception as e:
                    logger.error(f"Admin xato: {e}")

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    _, order_id, new_status = query.data.split(":")
    order_id = int(order_id)
    db.update_status(order_id, new_status)
    order = db.get_order(order_id)
    await query.edit_message_text(
        format_order(order),
        parse_mode="Markdown",
        reply_markup=admin_keyboard(order_id, new_status)
    )
    if order['chat_id']:
        try:
            status_label = STATUS_LABELS.get(new_status, new_status)
            await context.bot.send_message(
                order['chat_id'],
                f"📦 *Buyurtma #{order_id} holati:* {status_label}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mijoz xato: {e}")

async def cmd_start(update: Update, context):
    if update.effective_user.id in ADMIN_IDS:
        await update.message.reply_text(
            "👨‍💼 *Admin panel*\n\n/orders — Yangi buyurtmalar\n/all — Oxirgi 10\n/stats — Statistika",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🍽 *Taomdor botiga xush kelibsiz!*\n📞 +998 50 772-72-72",
            parse_mode="Markdown"
        )

async def cmd_orders(update: Update, context):
    if update.effective_user.id not in ADMIN_IDS:
        return
    orders = db.get_recent_orders(status="yangi")
    if not orders:
        await update.message.reply_text("🆕 Yangi buyurtmalar yo'q.")
        return
    for order in orders:
        await update.message.reply_text(format_order(order), parse_mode="Markdown",
                                        reply_markup=admin_keyboard(order['id'], order['status']))

async def cmd_all(update: Update, context):
    if update.effective_user.id not in ADMIN_IDS:
        return
    orders = db.get_recent_orders(limit=10)
    if not orders:
        await update.message.reply_text("Buyurtmalar yo'q.")
        return
    for order in orders:
        await update.message.reply_text(format_order(order), parse_mode="Markdown",
                                        reply_markup=admin_keyboard(order['id'], order['status']))

async def cmd_stats(update: Update, context):
    if update.effective_user.id not in ADMIN_IDS:
        return
    stats = db.get_stats()
    await update.message.reply_text(
        f"📊 *Statistika*\n\n"
        f"📦 Jami: {stats['total']}\n"
        f"🆕 Yangi: {stats['yangi']}\n"
        f"👨‍🍳 Tayyorlanmoqda: {stats['tayyorlanmoqda']}\n"
        f"🛵 Yetkazilmoqda: {stats['yetkazilmoqda']}\n"
        f"✅ Yetkazildi: {stats['yetkazildi']}\n"
        f"❌ Bekor: {stats['bekor']}",
        parse_mode="Markdown"
    )

def main():
    db.init()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("orders", cmd_orders))
    app.add_handler(CommandHandler("all", cmd_all))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 Taomdor Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
