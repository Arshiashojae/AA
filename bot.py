import telebot
from telebot import types
import sqlite3
import uuid

# ==================== تنظیمات ربات ====================
BOT_TOKEN = "8654237483:AAFHCuUoAUsyh4eHuDC3k4oneZE5uLF7cPc"
CHANNEL_ID = "@GhooghnoosVPN"
ADMIN_ID = 7274035412  

TRON_WALLET = "TNQtwfvGE5Ufg2TB61GobCfbhMQMBtfP36" 
TRX_PRICE_IN_TOMAN = 64842  

bot = telebot.TeleBot(BOT_TOKEN, num_threads=50)
DB_NAME = "bot_database.db"

ADMIN_STATES = {}

def db_execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    with sqlite3.connect(DB_NAME, timeout=30.0, check_same_thread=False) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute(query, params)
        res = None
        if fetchone:
            res = cursor.fetchone()
        elif fetchall:
            res = cursor.fetchall()
        if commit:
            conn.commit()
        return res

# ساخت و بروزرسانی جداول دیتابیس در شروع کار
db_execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referred_by INTEGER,
    invite_count INTEGER DEFAULT 0,
    has_received_free INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0
)""", commit=True)

db_execute("""CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    plan_name TEXT,
    config_text TEXT,
    date_added TEXT
)""", commit=True)

try:
    db_execute("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0", commit=True)
except sqlite3.OperationalError:
    pass

try:
    db_execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0", commit=True)
except sqlite3.OperationalError:
    pass

db_execute("""CREATE TABLE IF NOT EXISTS links (
    link_name TEXT PRIMARY KEY,
    capacity INTEGER,
    used_count INTEGER DEFAULT 0
)""", commit=True)

db_execute("""CREATE TABLE IF NOT EXISTS transactions (
    tx_id TEXT PRIMARY KEY,
    user_id INTEGER,
    plan_name TEXT,
    amount_trx REAL,
    status TEXT DEFAULT 'pending'
)""", commit=True)

try:
    db_execute("ALTER TABLE transactions ADD COLUMN amount_trx REAL", commit=True)
except sqlite3.OperationalError:
    pass

PLANS = {
    "plan_1gb":  {"name": "۱ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 180000},
    "plan_2gb":  {"name": "۲ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 360000},
    "plan_3gb":  {"name": "۳ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 540000},
    "plan_4gb":  {"name": "۴ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 720000},
    "plan_5gb":  {"name": "۵ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 900000},
    "plan_6gb":  {"name": "۶ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1080000},
    "plan_7gb":  {"name": "۷ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1260000},
    "plan_8gb":  {"name": "۸ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1440000},
    "plan_9gb":  {"name": "۹ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1620000},
    "plan_10gb": {"name": "۱۰ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1800000}
}

MENU_TITLES = {
    "menu_get_config": "🚀 دریافت کانفیگ رایگان",
    "menu_plans": "💎 خرید اکانت اختصاصی",
    "menu_referral": "👥 زیرمجموعه‌گیری / رفرال",
    "menu_wallet": "💳 افزایش موجودی",
    "menu_my_services": "📦 کانفیگ‌های من",
    "menu_support": "🛠 پشتیبانی آنلاین"
}

def setup_links():
    db_execute("INSERT OR IGNORE INTO links (link_name, capacity) VALUES (?, ?)", ("link10", 2), commit=True)

setup_links()

def generate_unique_config(user_id):
    unique_id = str(uuid.uuid4())
    server_details = "varzesh3.com:80?type=ws&path=%2F&host=kabotar.garfar.ir&security=none"
    return f"vless://{unique_id}@{server_details}#User-{user_id}"

def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def is_user_banned(user_id):
    res = db_execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if res and res[0] == 1:
        return True
    return False

def main_menu_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚀 دریافت کانفیگ رایگان", callback_data="menu_get_config"),
        types.InlineKeyboardButton("💎 خرید اکانت اختصاصی", callback_data="menu_plans"),
        types.InlineKeyboardButton("📦 کانفیگ‌های من", callback_data="menu_my_services"),
        types.InlineKeyboardButton("👥 زیرمجموعه‌گیری / رفرال", callback_data="menu_referral"),
        types.InlineKeyboardButton("💳 افزایش موجودی", callback_data="menu_wallet"),
        types.InlineKeyboardButton("🛠 پشتیبانی آنلاین", callback_data="menu_support")
    )
    return markup

def join_keyboard(start_param=""):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("ورود به کانال اسپانسر 📢", url=f"https://t.me/{CHANNEL_ID.replace('@','')}"))
    markup.add(types.InlineKeyboardButton("عضو شدم! بررسی کن ✅", callback_data=f"check_join:{start_param}"))
    return markup

def back_to_menu_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
    return markup

@bot.message_handler(func=lambda message: is_user_banned(message.from_user.id))
def handle_banned_users(message):
    try:
        bot.send_message(message.from_user.id, "❌ حساب کاربری شما در این ربات مسدود شده است.")
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: is_user_banned(call.from_user.id))
def handle_banned_callbacks(call):
    try:
        bot.answer_callback_query(call.id, "❌ حساب کاربری شما مسدود شده است.", show_alert=True)
    except Exception:
        pass

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        return
    first_name = message.from_user.first_name or "کاربر"
    text_args = message.text.split()
    start_param = text_args[1] if len(text_args) > 1 else ""
    
    try:
        log_param = f" با پارامتر [{start_param}]" if start_param else ""
        bot.send_message(ADMIN_ID, f"👣 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) ربات را استارت کرد{log_param}.", parse_mode="HTML")
    except Exception:
        pass

    user = db_execute("SELECT * FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    
    if not user:
        referred_by = None
        if start_param.isdigit() and int(start_param) != user_id:
            referred_by = int(start_param)
                
        db_execute("INSERT OR IGNORE INTO users (user_id, referred_by, balance, is_banned) VALUES (?, ?, 0, 0)", (user_id, referred_by), commit=True)

    if not check_membership(user_id):
        bot.send_message(user_id, "<b>⚠️ جهت استفاده از خدمات ربات و دریافت کانفیگ، ابتدا باید در کانال زیر عضو شوید:</b>", parse_mode="HTML", reply_markup=join_keyboard(start_param))
        return

    process_user_entry(user_id, start_param)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users_count = db_execute("SELECT COUNT(*) FROM users", fetchone=True)[0]
    pending_txs = db_execute("SELECT COUNT(*) FROM transactions WHERE status = 'pending'", fetchone=True)[0]
    
    msg = f"⚙️ <b>پنل مدیریت ربات ققنوس</b>\n\n" \
          f"📊 تعداد کل کاربران: {users_count} نفر\n" \
          f"⏳ تراکنش‌های در انتظار تایید: {pending_txs}\n" \
          f"💰 نرخ فعلی ترون: {TRX_PRICE_IN_TOMAN:,} تومان"
          
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("💵 تغییر قیمت ترون", callback_data="adm_change_trx"),
        types.InlineKeyboardButton("🚫 مدیریت مسدودسازی (بن)", callback_data="adm_ban_menu"),
        types.InlineKeyboardButton("📩 ارسال پیام اختصاصی به کاربر", callback_data="adm_send_direct"),
        types.InlineKeyboardButton("↩️ بسته شدن پنل ادمین", callback_data="adm_close")
    )
    bot.send_message(ADMIN_ID, msg, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and ADMIN_STATES.get(ADMIN_ID) in ['broadcast', 'change_trx', 'ban_id', 'unban_id', 'direct_user_id', 'direct_msg_text'])
def handle_admin_inputs(message):
    state = ADMIN_STATES.get(ADMIN_ID)
    if state == 'broadcast':
        ADMIN_STATES[ADMIN_ID] = None
        users = db_execute("SELECT user_id FROM users", fetchall=True)
        bot.send_message(ADMIN_ID, "⏳ فرآیند ارسال پیام همگانی آغاز شد...")
        success, failed = 0, 0
        for u in users:
            try:
                bot.send_message(u[0], message.text)
                success += 1
            except Exception:
                failed += 1
        bot.send_message(ADMIN_ID, f"✅ ارسال به پایان رسید.\n📥 موفق: {success}\n❌ ناموفق (بلاک): {failed}")
        
    elif state == 'change_trx':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            global TRX_PRICE_IN_TOMAN
            TRX_PRICE_IN_TOMAN = int(message.text)
            bot.send_message(ADMIN_ID, f"✅ قیمت ترون با موفقیت به {TRX_PRICE_IN_TOMAN:,} تومان تغییر یافت.")
        else:
            bot.send_message(ADMIN_ID, "❌ مقدار وارد شده معتبر نیست. باید عدد انگلیسی وارد کنید.")

    elif state == 'ban_id':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                db_execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,), commit=True)
                bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} با موفقیت مسدود (بن) شد.")
            else:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'unban_id':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                db_execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,), commit=True)
                bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} با موفقیت آزاد (آن‌بن) شد.")
            else:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'direct_user_id':
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                ADMIN_STATES[ADMIN_ID] = f"direct_msg_text:{target_id}"
                bot.send_message(ADMIN_ID, f"✍️ اکنون پیام خود را برای ارسال به کاربر {target_id} بفرستید:")
            else:
                ADMIN_STATES[ADMIN_ID] = None
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            ADMIN_STATES[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state and state.startswith("direct_msg_text:"):
        target_id = int(state.split(":")[1])
        ADMIN_STATES[ADMIN_ID] = None
        try:
            bot.send_message(target_id, message.text)
            bot.send_message(ADMIN_ID, f"✅ پیام شما با موفقیت به کاربر {target_id} ارسال شد.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطایی در ارسال پیام رخ داد. ممکن است ربات توسط کاربر بلاک شده باشد.\nجزئیات: {e}")

def process_user_entry(user_id, start_param):
    if start_param and not start_param.isdigit():
        link_data = db_execute("SELECT capacity, used_count FROM links WHERE link_name = ?", (start_param,), fetchone=True)
        
        if link_data:
            capacity, used_count = link_data
            if used_count >= capacity:
                bot.send_message(user_id, "❌ متاسفانه ظرفیت هدیه این لینک اختصاصی به پایان رسیده است.", reply_markup=main_menu_inline())
                return
                
            has_free = db_execute("SELECT has_received_free FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
            
            if has_free == 0:
                db_execute("UPDATE links SET used_count = used_count + 1 WHERE link_name = ?", (start_param,), commit=True)
                db_execute("UPDATE users SET has_received_free = 1 WHERE user_id = ?", (user_id,), commit=True)
                
                user_config = generate_unique_config(user_id)
                db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "هدیه ورود اختصاصی", user_config), commit=True)
                bot.send_message(user_id, f"🎉 <b>هدیه ویژه کانال فعال شد!</b>\n\nکانفیگ اختصاصی شما:\n\n<code>{user_config}</code>", parse_mode="HTML", reply_markup=main_menu_inline())
            else:
                bot.send_message(user_id, "❌ شما قبلاً هدیه رایگان ورود خود را دریافت کرده‌اید.", reply_markup=main_menu_inline())
            return
        else:
            bot.send_message(user_id, "❌ این لینک اختصاصی نامعتبر است.", reply_markup=main_menu_inline())
            return

    bot.send_message(user_id, "👋 به ربات هوشمند ما خوش آمدید.\n\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    try:
        bot.edit_message_text("👋 به منوی اصلی بازگشتید.\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_inline())
    except Exception:
        bot.send_message(call.message.chat.id, "👋 به منوی اصلی بازگشتید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_join:"))
def check_join_callback(call):
    user_id = call.from_user.id
    start_param = call.data.split(":")[1]
    
    if check_membership(user_id):
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
        
        ref_data = db_execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        if ref_data and ref_data[0]:
            inviter_id = ref_data[0]
            db_execute("UPDATE users SET invite_count = invite_count + 1 WHERE user_id = ?", (inviter_id,), commit=True)
            try:
                bot.send_message(inviter_id, "🎉 تبریک! یک کاربر جدید با لینک شما عضو شد و ۱ امتیاز دعوت دریافت کردید.")
            except Exception:
                pass
            db_execute("UPDATE users SET referred_by = NULL WHERE user_id = ?", (user_id,), commit=True)

        process_user_entry(user_id, start_param)
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "کاربر"
    action = call.data
    
    if not check_membership(user_id):
        bot.send_message(user_id, "⚠️ شما ابتدا باید در کانال عضو شوید.", reply_markup=join_keyboard())
        return

    try:
        button_name = MENU_TITLES.get(action, action)
        bot.send_message(ADMIN_ID, f"🎯 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) روی گزینه <b>[{button_name}]</b> کلیک کرد.", parse_mode="HTML")
    except Exception:
        pass

    if action == "menu_get_config":
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        if invite_count >= 15:
            new_count = invite_count - 15
            db_execute("UPDATE users SET invite_count = ? WHERE user_id = ?", (new_count, user_id), commit=True)
            
            user_config = generate_unique_config(user_id)
            db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "۱ گیگابایت (رفرال)", user_config), commit=True)
            
            msg_text = f"🎉 <b>تعداد دعوت‌های شما تایید شد!</b>\n\n" \
                       f"کانفیگ شما صادر و در بخش 'کانفیگ‌های من' ذخیره شد:\n\n" \
                       f"<code>{user_config}</code>\n\n" \
                       f"در صورت کار نکردن کانفیگ شما در قسمت پشتیبانی پیام ارسال کنید تا سرور جایگزین خدمتتون ارسال بشه\n" \
                       f"در صورت تشخیص رفرال فیک توسط شما سرور خودکار سرور غلط ارسال میکند اگر غیر این صورته و فیک نیست به پشتیبانی پیام بدید"
                       
            bot.send_message(user_id, msg_text, parse_mode="HTML", reply_markup=back_to_menu_markup())
        else:
            bot.send_message(user_id, f"❌ <b>تعداد دعوت‌های شما کافی نیست!</b>\n\nشما در حال حاضر {invite_count} دعوت فعال دارید. برای دریافت کانفیگ یک گیگابایتی تایم نامحدود به حداقل 15 دعوت نیاز دارید.", parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        msg = f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n🔗 لینک اختصاصی شما:\n<code>{ref_link}</code>\n\n📊 آمار دعوت‌های شما: <b>{invite_count}</b> نفر\n✨ با دعوت هر 15 نفر، می‌توانید ۱ کانفیگ یک گیگابایتی جدید دریافت کنید."
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_my_services":
        services = db_execute("SELECT plan_name, config_text, date_added FROM services WHERE user_id = ? ORDER BY date_added DESC", (user_id,), fetchall=True)
        if not services:
            bot.send_message(user_id, "❌ شما در حال حاضر هیچ کانفیگ فعال یا خریداری شده‌ای در سیستم ندارید.", reply_markup=back_to_menu_markup())
        else:
            msg = "📦 <b>لیست سرویس‌ها و کانفیگ‌های شما:</b>\n\n"
            for i, svc in enumerate(services, 1):
                msg += f"{i}. <b>{svc[0]}</b>\n📅 تاریخ: {svc[2]}\n<code>{svc[1]}</code>\n\n"
            bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_plans":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan_id, plan_info in PLANS.items():
            markup.add(types.InlineKeyboardButton(f"🛒 {plan_info['name']} ➡️ {plan_info['toman_price']:,} تومان", callback_data=f"buy_{plan_id}"))
        
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, f"💎 <b>لیست طرح‌ها و خرید اکانت اختصاصی:</b>\n\n👛 موجودی کیف پول شما: <b>{user_balance:,} تومان</b>\n\nلطفاً پلن مورد نظر را انتخاب کنید. اگر موجودی داشته باشید مستقیماً کسر می‌شود، در غیر این‌صورت می‌توانید حساب خود را شارژ کنید:", parse_mode="HTML", reply_markup=markup)

    elif action == "menu_wallet":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0se:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'unban_id':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                db_execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,), commit=True)
                bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} با موفقیت آزاد (آن‌بن) شد.")
            else:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'direct_user_id':
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                ADMIN_STATES[ADMIN_ID] = f"direct_msg_text:{target_id}"
                bot.send_message(ADMIN_ID, f"✍️ اکنون پیام خود را برای ارسال به کاربر {target_id} بفرستید:")
            else:
                ADMIN_STATES[ADMIN_ID] = None
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            ADMIN_STATES[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state and state.startswith("direct_msg_text:"):
        target_id = int(state.split(":")[1])
        ADMIN_STATES[ADMIN_ID] = None
        try:
            bot.send_message(target_id, message.text)
            bot.send_message(ADMIN_ID, f"✅ پیام شما با موفقیت به کاربر {target_id} ارسال شد.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطایی در ارسال پیام رخ داد. ممکن است ربات توسط کاربر بلاک شده باشد.\nجزئیات: {e}")

def process_user_entry(user_id, start_param):
    if start_param and not start_param.isdigit():
        link_data = db_execute("SELECT capacity, used_count FROM links WHERE link_name = ?", (start_param,), fetchone=True)
        
        if link_data:
            capacity, used_count = link_data
            if used_count >= capacity:
                bot.send_message(user_id, "❌ متاسفانه ظرفیت هدیه این لینک اختصاصی به پایان رسیده است.", reply_markup=main_menu_inline())
                return
                
            has_free = db_execute("SELECT has_received_free FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
            
            if has_free == 0:
                db_execute("UPDATE links SET used_count = used_count + 1 WHERE link_name = ?", (start_param,), commit=True)
                db_execute("UPDATE users SET has_received_free = 1 WHERE user_id = ?", (user_id,), commit=True)
                
                user_config = generate_unique_config(user_id)
                db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "هدیه ورود اختصاصی", user_config), commit=True)
                bot.send_message(user_id, f"🎉 <b>هدیه ویژه کانال فعال شد!</b>\n\nکانفیگ اختصاصی شما:\n\n<code>{user_config}</code>", parse_mode="HTML", reply_markup=main_menu_inline())
            else:
                bot.send_message(user_id, "❌ شما قبلاً هدیه رایگان ورود خود را دریافت کرده‌اید.", reply_markup=main_menu_inline())
            return
        else:
            bot.send_message(user_id, "❌ این لینک اختصاصی نامعتبر است.", reply_markup=main_menu_inline())
            return

    bot.send_message(user_id, "👋 به ربات هوشمند ما خوش آمدید.\n\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    try:
        bot.edit_message_text("👋 به منوی اصلی بازگشتید.\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_inline())
    except Exception:
        bot.send_message(call.message.chat.id, "👋 به منوی اصلی بازگشتید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_join:"))
def check_join_callback(call):
    user_id = call.from_user.id
    start_param = call.data.split(":")[1]
    
    if check_membership(user_id):
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
        
        ref_data = db_execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        if ref_data and ref_data[0]:
            inviter_id = ref_data[0]
            db_execute("UPDATE users SET invite_count = invite_count + 1 WHERE user_id = ?", (inviter_id,), commit=True)
            try:
                bot.send_message(inviter_id, "🎉 تبریک! یک کاربر جدید با لینک شما عضو شد و ۱ امتیاز دعوت دریافت کردید.")
            except Exception:
                pass
            db_execute("UPDATE users SET referred_by = NULL WHERE user_id = ?", (user_id,), commit=True)

        process_user_entry(user_id, start_param)
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "کاربر"
    action = call.data
    
    if not check_membership(user_id):
        bot.send_message(user_id, "⚠️ شما ابتدا باید در کانال عضو شوید.", reply_markup=join_keyboard())
        return

    try:
        button_name = MENU_TITLES.get(action, action)
        bot.send_message(ADMIN_ID, f"🎯 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) روی گزینه <b>[{button_name}]</b> کلیک کرد.", parse_mode="HTML")
    except Exception:
        pass

    if action == "menu_get_config":
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        if invite_count >= 15:
            new_count = invite_count - 15
            db_execute("UPDATE users SET invite_count = ? WHERE user_id = ?", (new_count, user_id), commit=True)
            
            user_config = generate_unique_config(user_id)
            db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "۱ گیگابایت (رفرال)", user_config), commit=True)
            
            msg_text = f"🎉 <b>تعداد دعوت‌های شما تایید شد!</b>\n\n" \
                       f"کانفیگ شما صادر و در بخش 'کانفیگ‌های من' ذخیره شد:\n\n" \
                       f"<code>{user_config}</code>\n\n" \
                       f"در صورت کار نکردن کانفیگ شما در قسمت پشتیبانی پیام ارسال کنید تا سرور جایگزین خدمتتون ارسال بشه\n" \
                       f"در صورت تشخیص رفرال فیک توسط شما سرور خودکار سرور غلط ارسال میکند اگر غیر این صورته و فیک نیست به پشتیبانی پیام بدید"
                       
            bot.send_message(user_id, msg_text, parse_mode="HTML", reply_markup=back_to_menu_markup())
        else:
            bot.send_message(user_id, f"❌ <b>تعداد دعوت‌های شما کافی نیست!</b>\n\nشما در حال حاضر {invite_count} دعوت فعال دارید. برای دریافت کانفیگ یک گیگابایتی تایم نامحدود به حداقل 15 دعوت نیاز دارید.", parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        msg = f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n🔗 لینک اختصاصی شما:\n<code>{ref_link}</code>\n\n📊 آمار دعوت‌های شما: <b>{invite_count}</b> نفر\n✨ با دعوت هر 15 نفر، می‌توانید ۱ کانفیگ یک گیگابایتی جدید دریافت کنید."
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_my_services":
        services = db_execute("SELECT plan_name, config_text, date_added FROM services WHERE user_id = ? ORDER BY date_added DESC", (user_id,), fetchall=True)
        if not services:
            bot.send_message(user_id, "❌ شما در حال حاضر هیچ کانفیگ فعال یا خریداری شده‌ای در سیستم ندارید.", reply_markup=back_to_menu_markup())
        else:
            msg = "📦 <b>لیست سرویس‌ها و کانفیگ‌های شما:</b>\n\n"
            for i, svc in enumerate(services, 1):
                msg += f"{i}. <b>{svc[0]}</b>\n📅 تاریخ: {svc[2]}\n<code>{svc[1]}</code>\n\n"
            bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_plans":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan_id, plan_info in PLANS.items():
            markup.add(types.InlineKeyboardButton(f"🛒 {plan_info['name']} ➡️ {plan_info['toman_price']:,} تومان", callback_data=f"buy_{plan_id}"))
        
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, f"💎 <b>لیست طرح‌ها و خرید اکانت اختصاصی:</b>\n\n👛 موجودی کیف پول شما: <b>{user_balance:,} تومان</b>\n\nلطفاً پلن مورد نظر را انتخاب کنید. اگر موجودی داشته باشید مستقیماً کسر می‌شود، در غیر این‌صورت می‌توانید حساب خود را شارژ کنید:", parse_mode="HTML", reply_markup=markup)

    elif action == "menu_wallet":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchonese:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'unban_id':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                db_execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,), commit=True)
                bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} با موفقیت آزاد (آن‌بن) شد.")
            else:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'direct_user_id':
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                ADMIN_STATES[ADMIN_ID] = f"direct_msg_text:{target_id}"
                bot.send_message(ADMIN_ID, f"✍️ اکنون پیام خود را برای ارسال به کاربر {target_id} بفرستید:")
            else:
                ADMIN_STATES[ADMIN_ID] = None
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            ADMIN_STATES[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state and state.startswith("direct_msg_text:"):
        target_id = int(state.split(":")[1])
        ADMIN_STATES[ADMIN_ID] = None
        try:
            bot.send_message(target_id, message.text)
            bot.send_message(ADMIN_ID, f"✅ پیام شما با موفقیت به کاربر {target_id} ارسال شد.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطایی در ارسال پیام رخ داد. ممکن است ربات توسط کاربر بلاک شده باشد.\nجزئیات: {e}")

def process_user_entry(user_id, start_param):
    if start_param and not start_param.isdigit():
        link_data = db_execute("SELECT capacity, used_count FROM links WHERE link_name = ?", (start_param,), fetchone=True)
        
        if link_data:
            capacity, used_count = link_data
            if used_count >= capacity:
                bot.send_message(user_id, "❌ متاسفانه ظرفیت هدیه این لینک اختصاصی به پایان رسیده است.", reply_markup=main_menu_inline())
                return
                
            has_free = db_execute("SELECT has_received_free FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
            
            if has_free == 0:
                db_execute("UPDATE links SET used_count = used_count + 1 WHERE link_name = ?", (start_param,), commit=True)
                db_execute("UPDATE users SET has_received_free = 1 WHERE user_id = ?", (user_id,), commit=True)
                
                user_config = generate_unique_config(user_id)
                db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "هدیه ورود اختصاصی", user_config), commit=True)
                bot.send_message(user_id, f"🎉 <b>هدیه ویژه کانال فعال شد!</b>\n\nکانفیگ اختصاصی شما:\n\n<code>{user_config}</code>", parse_mode="HTML", reply_markup=main_menu_inline())
            else:
                bot.send_message(user_id, "❌ شما قبلاً هدیه رایگان ورود خود را دریافت کرده‌اید.", reply_markup=main_menu_inline())
            return
        else:
            bot.send_message(user_id, "❌ این لینک اختصاصی نامعتبر است.", reply_markup=main_menu_inline())
            return

    bot.send_message(user_id, "👋 به ربات هوشمند ما خوش آمدید.\n\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    try:
        bot.edit_message_text("👋 به منوی اصلی بازگشتید.\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_inline())
    except Exception:
        bot.send_message(call.message.chat.id, "👋 به منوی اصلی بازگشتید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_join:"))
def check_join_callback(call):
    user_id = call.from_user.id
    start_param = call.data.split(":")[1]
    
    if check_membership(user_id):
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
        
        ref_data = db_execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        if ref_data and ref_data[0]:
            inviter_id = ref_data[0]
            db_execute("UPDATE users SET invite_count = invite_count + 1 WHERE user_id = ?", (inviter_id,), commit=True)
            try:
                bot.send_message(inviter_id, "🎉 تبریک! یک کاربر جدید با لینک شما عضو شد و ۱ امتیاز دعوت دریافت کردید.")
            except Exception:
                pass
            db_execute("UPDATE users SET referred_by = NULL WHERE user_id = ?", (user_id,), commit=True)

        process_user_entry(user_id, start_param)
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "کاربر"
    action = call.data
    
    if not check_membership(user_id):
        bot.send_message(user_id, "⚠️ شما ابتدا باید در کانال عضو شوید.", reply_markup=join_keyboard())
        return

    try:
        button_name = MENU_TITLES.get(action, action)
        bot.send_message(ADMIN_ID, f"🎯 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) روی گزینه <b>[{button_name}]</b> کلیک کرد.", parse_mode="HTML")
    except Exception:
        pass

    if action == "menu_get_config":
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        if invite_count >= 15:
            new_count = invite_count - 15
            db_execute("UPDATE users SET invite_count = ? WHERE user_id = ?", (new_count, user_id), commit=True)
            
            user_config = generate_unique_config(user_id)
            db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "۱ گیگابایت (رفرال)", user_config), commit=True)
            
            msg_text = f"🎉 <b>تعداد دعوت‌های شما تایید شد!</b>\n\n" \
                       f"کانفیگ شما صادر و در بخش 'کانفیگ‌های من' ذخیره شد:\n\n" \
                       f"<code>{user_config}</code>\n\n" \
                       f"در صورت کار نکردن کانفیگ شما در قسمت پشتیبانی پیام ارسال کنید تا سرور جایگزین خدمتتون ارسال بشه\n" \
                       f"در صورت تشخیص رفرال فیک توسط شما سرور خودکار سرور غلط ارسال میکند اگر غیر این صورته و فیک نیست به پشتیبانی پیام بدید"
                       
            bot.send_message(user_id, msg_text, parse_mode="HTML", reply_markup=back_to_menu_markup())
        else:
            bot.send_message(user_id, f"❌ <b>تعداد دعوت‌های شما کافی نیست!</b>\n\nشما در حال حاضر {invite_count} دعوت فعال دارید. برای دریافت کانفیگ یک گیگابایتی تایم نامحدود به حداقل 15 دعوت نیاز دارید.", parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        msg = f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n🔗 لینک اختصاصی شما:\n<code>{ref_link}</code>\n\n📊 آمار دعوت‌های شما: <b>{invite_count}</b> نفر\n✨ با دعوت هر 15 نفر، می‌توانید ۱ کانفیگ یک گیگابایتی جدید دریافت کنید."
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_my_services":
        services = db_execute("SELECT plan_name, config_text, date_added FROM services WHERE user_id = ? ORDER BY date_added DESC", (user_id,), fetchall=True)
        if not services:
            bot.send_message(user_id, "❌ شما در حال حاضر هیچ کانفیگ فعال یا خریداری شده‌ای در سیستم ندارید.", reply_markup=back_to_menu_markup())
        else:
            msg = "📦 <b>لیست سرویس‌ها و کانفیگ‌های شما:</b>\n\n"
            for i, svc in enumerate(services, 1):
                msg += f"{i}. <b>{svc[0]}</b>\n📅 تاریخ: {svc[2]}\n<code>{svc[1]}</code>\n\n"
            bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_plans":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan_id, plan_info in PLANS.items():
            markup.add(types.InlineKeyboardButton(f"🛒 {plan_info['name']} ➡️ {plan_info['toman_price']:,} تومان", callback_data=f"buy_{plan_id}"))
        
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, f"💎 <b>لیست طرح‌ها و خرید اکانت اختصاصی:</b>\n\n👛 موجودی کیف پول شما: <b>{user_balance:,} تومان</b>\n\nلطفاً پلن مورد نظر را انتخاب کنید. اگر موجودی داشته باشید مستقیماً کسر می‌شود، در غیر این‌صورت می‌توانید حساب خود را شارژ کنید:", parse_mode="HTML", reply_markup=markup)

    elif action == "menu_wallet":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?"(, (user_id,), fetchon    referred_by INTEGER,
    invite_count INTEGER DEFAULT 0,
    has_received_free INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0
)
""", commit=True)

db_execute("""
CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    plan_name TEXT,
    config_text TEXT,
    date_added TEXT
)
""", commit=True)

try:
    db_execute("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0", commit=True)
except sqlite3.OperationalError:
    pass

try:
    db_execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0", commit=True)
except sqlite3.OperationalError:
    pass

db_execute("""
CREATE TABLE IF NOT EXISTS links (
    link_name TEXT PRIMARY KEY,
    capacity INTEGER,
    used_count INTEGER DEFAULT 0
)
""", commit=True)

db_execute("""
CREATE TABLE IF NOT EXISTS transactions (
    tx_id TEXT PRIMARY KEY,
    user_id INTEGER,
    plan_name TEXT,
    amount_trx REAL,
    status TEXT DEFAULT 'pending'
)
""", commit=True)

try:
    db_execute("ALTER TABLE transactions ADD COLUMN amount_trx REAL", commit=True)
except sqlite3.OperationalError:
    pass

PLANS = {
    "plan_1gb":  {"name": "۱ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 180000},
    "plan_2gb":  {"name": "۲ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 360000},
    "plan_3gb":  {"name": "۳ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 540000},
    "plan_4gb":  {"name": "۴ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 720000},
    "plan_5gb":  {"name": "۵ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 900000},
    "plan_6gb":  {"name": "۶ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1080000},
    "plan_7gb":  {"name": "۷ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1260000},
    "plan_8gb":  {"name": "۸ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1440000},
    "plan_9gb":  {"name": "۹ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1620000},
    "plan_10gb": {"name": "۱۰ گیگابایت (کاربر و زمان نامحدود)", "toman_price": 1800000}
}

MENU_TITLES = {
    "menu_get_config": "🚀 دریافت کانفیگ رایگان",
    "menu_plans": "💎 خرید اکانت اختصاصی",
    "menu_referral": "👥 زیرمجموعه‌گیری / رفرال",
    "menu_wallet": "💳 افزایش موجودی",
    "menu_my_services": "📦 کانفیگ‌های من",
    "menu_support": "🛠 پشتیبانی آنلاین"
}

def setup_links():
    db_execute("INSERT OR IGNORE INTO links (link_name, capacity) VALUES (?, ?)", ("link10", 2), commit=True)

setup_links()

def generate_unique_config(user_id):
    unique_id = str(uuid.uuid4())
    server_details = "varzesh3.com:80?type=ws&path=%2F&host=kabotar.garfar.ir&security=none"
    return f"vless://{unique_id}@{server_details}#User-{user_id}"

def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def is_user_banned(user_id):
    res = db_execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if res and res[0] == 1:
        return True
    return False

def main_menu_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚀 دریافت کانفیگ رایگان", callback_data="menu_get_config"),
        types.InlineKeyboardButton("💎 خرید اکانت اختصاصی", callback_data="menu_plans"),
        types.InlineKeyboardButton("📦 کانفیگ‌های من", callback_data="menu_my_services"),
        types.InlineKeyboardButton("👥 زیرمجموعه‌گیری / رفرال", callback_data="menu_referral"),
        types.InlineKeyboardButton("💳 افزایش موجودی", callback_data="menu_wallet"),
        types.InlineKeyboardButton("🛠 پشتیبانی آنلاین", callback_data="menu_support")
    )
    return markup

def join_keyboard(start_param=""):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("ورود به کانال اسپانسر 📢", url=f"https://t.me/{CHANNEL_ID.replace('@','')}"))
    markup.add(types.InlineKeyboardButton("عضو شدم! بررسی کن ✅", callback_data=f"check_join:{start_param}"))
    return markup

def back_to_menu_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
    return markup

@bot.message_handler(func=lambda message: is_user_banned(message.from_user.id))
def handle_banned_users(message):
    try:
        bot.send_message(message.from_user.id, "❌ حساب کاربری شما در این ربات مسدود شده است.")
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: is_user_banned(call.from_user.id))
def handle_banned_callbacks(call):
    try:
        bot.answer_callback_query(call.id, "❌ حساب کاربری شما مسدود شده است.", show_alert=True)
    except Exception:
        pass

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        return
    first_name = message.from_user.first_name or "کاربر"
    text_args = message.text.split()
    start_param = text_args[1] if len(text_args) > 1 else ""
    
    try:
        log_param = f" با پارامتر [{start_param}]" if start_param else ""
        bot.send_message(ADMIN_ID, f"👣 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) ربات را استارت کرد{log_param}.", parse_mode="HTML")
    except Exception:
        pass

    user = db_execute("SELECT * FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    
    if not user:
        referred_by = None
        if start_param.isdigit() and int(start_param) != user_id:
            referred_by = int(start_param)
                
        db_execute("INSERT OR IGNORE INTO users (user_id, referred_by, balance, is_banned) VALUES (?, ?, 0, 0)", (user_id, referred_by), commit=True)

    if not check_membership(user_id):
        bot.send_message(user_id, "<b>⚠️ جهت استفاده از خدمات ربات و دریافت کانفیگ، ابتدا باید در کانال زیر عضو شوید:</b>", parse_mode="HTML", reply_markup=join_keyboard(start_param))
        return

    process_user_entry(user_id, start_param)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users_count = db_execute("SELECT COUNT(*) FROM users", fetchone=True)[0]
    pending_txs = db_execute("SELECT COUNT(*) FROM transactions WHERE status = 'pending'", fetchone=True)[0]
    
    msg = f"⚙️ <b>پنل مدیریت ربات ققنوس</b>\n\n" \
          f"📊 تعداد کل کاربران: {users_count} نفر\n" \
          f"⏳ تراکنش‌های در انتظار تایید: {pending_txs}\n" \
          f"💰 نرخ فعلی ترون: {TRX_PRICE_IN_TOMAN:,} تومان"
          
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("💵 تغییر قیمت ترون", callback_data="adm_change_trx"),
        types.InlineKeyboardButton("🚫 مدیریت مسدودسازی (بن)", callback_data="adm_ban_menu"),
        types.InlineKeyboardButton("📩 ارسال پیام اختصاصی به کاربر", callback_data="adm_send_direct"),
        types.InlineKeyboardButton("↩️ بسته شدن پنل ادمین", callback_data="adm_close")
    )
    bot.send_message(ADMIN_ID, msg, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and ADMIN_STATES.get(ADMIN_ID) in ['broadcast', 'change_trx', 'ban_id', 'unban_id', 'direct_user_id', 'direct_msg_text'])
def handle_admin_inputs(message):
    state = ADMIN_STATES.get(ADMIN_ID)
    if state == 'broadcast':
        ADMIN_STATES[ADMIN_ID] = None
        users = db_execute("SELECT user_id FROM users", fetchall=True)
        bot.send_message(ADMIN_ID, "⏳ فرآیند ارسال پیام همگانی آغاز شد...")
        success, failed = 0, 0
        for u in users:
            try:
                bot.send_message(u[0], message.text)
                success += 1
            except Exception:
                failed += 1
        bot.send_message(ADMIN_ID, f"✅ ارسال به پایان رسید.\n📥 موفق: {success}\n❌ ناموفق (بلاک): {failed}")
        
    elif state == 'change_trx':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            global TRX_PRICE_IN_TOMAN
            TRX_PRICE_IN_TOMAN = int(message.text)
            bot.send_message(ADMIN_ID, f"✅ قیمت ترون با موفقیت به {TRX_PRICE_IN_TOMAN:,} تومان تغییر یافت.")
        else:
            bot.send_message(ADMIN_ID, "❌ مقدار وارد شده معتبر نیست. باید عدد انگلیسی وارد کنید.")

    elif state == 'ban_id':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                db_execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,), commit=True)
                bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} با موفقیت مسدود (بن) شد.")
            else:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'unban_id':
        ADMIN_STATES[ADMIN_ID] = None
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                db_execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,), commit=True)
                bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} با موفقیت آزاد (آن‌بن) شد.")
            else:
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state == 'direct_user_id':
        if message.text.isdigit():
            target_id = int(message.text)
            user_exist = db_execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,), fetchone=True)
            if user_exist:
                ADMIN_STATES[ADMIN_ID] = f"direct_msg_text:{target_id}"
                bot.send_message(ADMIN_ID, f"✍️ اکنون پیام خود را برای ارسال به کاربر {target_id} بفرستید:")
            else:
                ADMIN_STATES[ADMIN_ID] = None
                bot.send_message(ADMIN_ID, "❌ این آیدی عددی در دیتابیس ربات یافت نشد.")
        else:
            ADMIN_STATES[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "❌ آیدی عددی وارد شده معتبر نیست.")

    elif state and state.startswith("direct_msg_text:"):
        target_id = int(state.split(":")[1])
        ADMIN_STATES[ADMIN_ID] = None
        try:
            bot.send_message(target_id, message.text)
            bot.send_message(ADMIN_ID, f"✅ پیام شما با موفقیت به کاربر {target_id} ارسال شد.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ خطایی در ارسال پیام رخ داد. ممکن است ربات توسط کاربر بلاک شده باشد.\nجزئیات: {e}")

def process_user_entry(user_id, start_param):
    if start_param and not start_param.isdigit():
        link_data = db_execute("SELECT capacity, used_count FROM links WHERE link_name = ?", (start_param,), fetchone=True)
        
        if link_data:
            capacity, used_count = link_data
            if used_count >= capacity:
                bot.send_message(user_id, "❌ متاسفانه ظرفیت هدیه این لینک اختصاصی به پایان رسیده است.", reply_markup=main_menu_inline())
                return
                
            has_free = db_execute("SELECT has_received_free FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
            
            if has_free == 0:
                db_execute("UPDATE links SET used_count = used_count + 1 WHERE link_name = ?", (start_param,), commit=True)
                db_execute("UPDATE users SET has_received_free = 1 WHERE user_id = ?", (user_id,), commit=True)
                
                user_config = generate_unique_config(user_id)
                db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "هدیه ورود اختصاصی", user_config), commit=True)
                bot.send_message(user_id, f"🎉 <b>هدیه ویژه کانال فعال شد!</b>\n\nکانفیگ اختصاصی شما:\n\n<code>{user_config}</code>", parse_mode="HTML", reply_markup=main_menu_inline())
            else:
                bot.send_message(user_id, "❌ شما قبلاً هدیه رایگان ورود خود را دریافت کرده‌اید.", reply_markup=main_menu_inline())
            return
        else:
            bot.send_message(user_id, "❌ این لینک اختصاصی نامعتبر است.", reply_markup=main_menu_inline())
            return

    bot.send_message(user_id, "👋 به ربات هوشمند ما خوش آمدید.\n\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    try:
        bot.edit_message_text("👋 به منوی اصلی بازگشتید.\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_inline())
    except Exception:
        bot.send_message(call.message.chat.id, "👋 به منوی اصلی بازگشتید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_join:"))
def check_join_callback(call):
    user_id = call.from_user.id
    start_param = call.data.split(":")[1]
    
    if check_membership(user_id):
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
        
        ref_data = db_execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        if ref_data and ref_data[0]:
            inviter_id = ref_data[0]
            db_execute("UPDATE users SET invite_count = invite_count + 1 WHERE user_id = ?", (inviter_id,), commit=True)
            try:
                bot.send_message(inviter_id, "🎉 تبریک! یک کاربر جدید با لینک شما عضو شد و ۱ امتیاز دعوت دریافت کردید.")
            except Exception:
                pass
            db_execute("UPDATE users SET referred_by = NULL WHERE user_id = ?", (user_id,), commit=True)

        process_user_entry(user_id, start_param)
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "کاربر"
    action = call.data
    
    if not check_membership(user_id):
        bot.send_message(user_id, "⚠️ شما ابتدا باید در کانال عضو شوید.", reply_markup=join_keyboard())
        return

    try:
        button_name = MENU_TITLES.get(action, action)
        bot.send_message(ADMIN_ID, f"🎯 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) روی گزینه <b>[{button_name}]</b> کلیک کرد.", parse_mode="HTML")
    except Exception:
        pass

    if action == "menu_get_config":
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        if invite_count >= 15:
            new_count = invite_count - 15
            db_execute("UPDATE users SET invite_count = ? WHERE user_id = ?", (new_count, user_id), commit=True)
            
            user_config = generate_unique_config(user_id)
            db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "۱ گیگابایت (رفرال)", user_config), commit=True)
            
            msg_text = f"🎉 <b>تعداد دعوت‌های شما تایید شد!</b>\n\n" \
                       f"کانفیگ شما صادر و در بخش 'کانفیگ‌های من' ذخیره شد:\n\n" \
                       f"<code>{user_config}</code>\n\n" \
                       f"در صورت کار نکردن کانفیگ شما در قسمت پشتیبانی پیام ارسال کنید تا سرور جایگزین خدمتتون ارسال بشه\n" \
                       f"در صورت تشخیص رفرال فیک توسط شما سرور خودکار سرور غلط ارسال میکند اگر غیر این صورته و فیک نیست به پشتیبانی پیام بدید"
                       
            bot.send_message(user_id, msg_text, parse_mode="HTML", reply_markup=back_to_menu_markup())
        else:
            bot.send_message(user_id, f"❌ <b>تعداد دعوت‌های شما کافی نیست!</b>\n\nشما در حال حاضر {invite_count} دعوت فعال دارید. برای دریافت کانفیگ یک گیگابایتی تایم نامحدود به حداقل 15 دعوت نیاز دارید.", parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        msg = f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n🔗 لینک اختصاصی شما:\n<code>{ref_link}</code>\n\n📊 آمار دعوت‌های شما: <b>{invite_count}</b> نفر\n✨ با دعوت هر 15 نفر، می‌توانید ۱ کانفیگ یک گیگابایتی جدید دریافت کنید."
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_my_services":
        services = db_execute("SELECT plan_name, config_text, date_added FROM services WHERE user_id = ? ORDER BY date_added DESC", (user_id,), fetchall=True)
        if not services:
            bot.send_message(user_id, "❌ شما در حال حاضر هیچ کانفیگ فعال یا خریداری شده‌ای در سیستم ندارید.", reply_markup=back_to_menu_markup())
        else:
            msg = "📦 <b>لیست سرویس‌ها و کانفیگ‌های شما:</b>\n\n"
            for i, svc in enumerate(services, 1):
                msg += f"{i}. <b>{svc[0]}</b>\n📅 تاریخ: {svc[2]}\n<code>{svc[1]}</code>\n\n"
            bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_plans":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan_id, plan_info in PLANS.items():
            markup.add(types.InlineKeyboardButton(f"🛒 {plan_info['name']} ➡️ {plan_info['toman_price']:,} تومان", callback_data=f"buy_{plan_id}"))
        
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, f"💎 <b>لیست طرح‌ها و خرید اکانت اختصاصی:</b>\n\n👛 موجودی کیف پول شما: <b>{user_balance:,} تومان</b>\n\nلطفاً پلن مورد نظر را انتخاب کنید. اگر موجودی داشته باشید مستقیماً کسر می‌شود، در غیر این‌صورت می‌توانید حساب خود را شارژ کنید:", parse_mode="HTML", reply_markup=markup)

    elif action == "menu_wallet":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone
            return

    bot.send_message(user_id, "👋 به ربات هوشمند ما خوش آمدید.\n\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    try:
        bot.edit_message_text("👋 به منوی اصلی بازگشتید.\nلطفاً یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_inline())
    except Exception:
        bot.send_message(call.message.chat.id, "👋 به منوی اصلی بازگشتید:", reply_markup=main_menu_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_join:"))
def check_join_callback(call):
    user_id = call.from_user.id
    start_param = call.data.split(":")[1]
    
    if check_membership(user_id):
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
        
        ref_data = db_execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        if ref_data and ref_data[0]:
            inviter_id = ref_data[0]
            db_execute("UPDATE users SET invite_count = invite_count + 1 WHERE user_id = ?", (inviter_id,), commit=True)
            try:
                bot.send_message(inviter_id, "🎉 تبریک! یک کاربر جدید با لینک شما عضو شد و ۱ امتیاز دعوت دریافت کردید.")
            except Exception:
                pass
            db_execute("UPDATE users SET referred_by = NULL WHERE user_id = ?", (user_id,), commit=True)

        process_user_entry(user_id, start_param)
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "کاربر"
    action = call.data
    
    if not check_membership(user_id):
        bot.send_message(user_id, "⚠️ شما ابتدا باید در کانال عضو شوید.", reply_markup=join_keyboard())
        return

    try:
        button_name = MENU_TITLES.get(action, action)
        bot.send_message(ADMIN_ID, f"🎯 <b>گزارش:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) روی گزینه <b>[{button_name}]</b> کلیک کرد.", parse_mode="HTML")
    except Exception:
        pass

    if action == "menu_get_config":
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        if invite_count >= 15:
            new_count = invite_count - 15
            db_execute("UPDATE users SET invite_count = ? WHERE user_id = ?", (new_count, user_id), commit=True)
            
            user_config = generate_unique_config(user_id)
            db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], user_id, "۱ گیگابایت (رفرال)", user_config), commit=True)
            bot.send_message(user_id, f"🎉 <b>تعداد دعوت‌های شما تایید شد!</b>\n\nکانفیگ شما صادر و در بخش 'کانفیگ‌های من' ذخیره شد:\n\n<code>{user_config}</code>", parse_mode="HTML", reply_markup=back_to_menu_markup())
        else:
            bot.send_message(user_id, f"❌ <b>تعداد دعوت‌های شما کافی نیست!</b>\n\nشما در حال حاضر {invite_count} دعوت فعال دارید. برای دریافت کانفیگ یک گیگابایتی تایم نامحدود به حداقل 15 دعوت نیاز دارید.", parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        invite_count = db_execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        msg = f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n🔗 لینک اختصاصی شما:\n<code>{ref_link}</code>\n\n📊 آمار دعوت‌های شما: <b>{invite_count}</b> نفر\n✨ با دعوت هر 15 نفر، می‌توانید ۱ کانفیگ یک گیگابایتی جدید دریافت کنید."
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_my_services":
        services = db_execute("SELECT plan_name, config_text, date_added FROM services WHERE user_id = ? ORDER BY date_added DESC", (user_id,), fetchall=True)
        if not services:
            bot.send_message(user_id, "❌ شما در حال حاضر هیچ کانفیگ فعال یا خریداری شده‌ای در سیستم ندارید.", reply_markup=back_to_menu_markup())
        else:
            msg = "📦 <b>لیست سرویس‌ها و کانفیگ‌های شما:</b>\n\n"
            for i, svc in enumerate(services, 1):
                msg += f"{i}. <b>{svc[0]}</b>\n📅 تاریخ: {svc[2]}\n<code>{svc[1]}</code>\n\n"
            bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=back_to_menu_markup())

    elif action == "menu_plans":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan_id, plan_info in PLANS.items():
            markup.add(types.InlineKeyboardButton(f"🛒 {plan_info['name']} ➡️ {plan_info['toman_price']:,} تومان", callback_data=f"buy_{plan_id}"))
        
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, f"💎 <b>لیست طرح‌ها و خرید اکانت اختصاصی:</b>\n\n👛 موجودی کیف پول شما: <b>{user_balance:,} تومان</b>\n\nلطفاً پلن مورد نظر را انتخاب کنید. اگر موجودی داشته باشید مستقیماً کسر می‌شود، در غیر این‌صورت می‌توانید حساب خود را شارژ کنید:", parse_mode="HTML", reply_markup=markup)

    elif action == "menu_wallet":
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        msg = f"💳 <b>بخش افزایش موجودی</b>\n\n👛 موجودی فعلی حساب شما: <b>{user_balance:,} تومان</b>\n\n💵 ارز پایه سیستم: <code>Tron (TRX)</code>\n📊 نرخ فعلی سیستم: <code>۱ ترون = {TRX_PRICE_IN_TOMAN:,} تومان</code>\n\n🌐 آدرس ولت ترون جهت واریز (TRC-20):\n<code>{TRON_WALLET}</code>\n\n⚠️ پس از واریز مبلغ دلخواه، روی دکمه زیر کلیک کنید و اسکرین‌شات رسید یا کد پیگیری (Hash) را ارسال کنید تا پس از تایید ادمین، حساب شما شارژ شود."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 تایید پرداخت و افزایش موجودی", callback_data="submit_general_deposit"))
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=markup)

    elif action == "menu_support":
        msg = bot.send_message(user_id, "✍️ <b>لطفاً پیام، سوال یا مشکل خود را به صورت متنی یا عکس بفرستید:</b>\n\nپشتیبانان ما در اسرع وقت پاسخ شما را خواهند داد.", parse_mode="HTML", reply_markup=back_to_menu_markup())
        bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    user_id = message.from_user.id
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("✍️ پاسخ به کاربر", callback_data=f"sup_reply:{user_id}"))
    
    if message.content_type == 'text':
        user_text = message.text.strip()
        admin_msg = f"📩 <b>پیام پشتیبانی جدید!</b>\n\n👤 کد کاربر: <code>{user_id}</code>\n📝 متن پیام:\n{user_text}"
        try:
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML", reply_markup=admin_markup)
            bot.send_message(user_id, "✅ پیام شما با موفقیت به پشتیبانی ارسال شد. لطفاً تا بررسی و پاسخ ادمین شکیبا باشید.", reply_markup=back_to_menu_markup())
        except Exception as e:
            print(f"Error sending text support to admin: {e}")
            bot.send_message(user_id, "❌ خطایی در ارسال پیام به پشتیبانی رخ داد.", reply_markup=back_to_menu_markup())
            
    elif message.content_type == 'photo':
        caption_text = message.caption.strip() if message.caption else "بدون متن"
        admin_msg = f"📩 <b>عکس پشتیبانی جدید!</b>\n\n👤 کد کاربر: <code>{user_id}</code>\n📝 توضیحات عکس:\n{caption_text}"
        try:
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_msg, parse_mode="HTML", reply_markup=admin_markup)
            bot.send_message(user_id, "✅ عکس شما با موفقیت به پشتیبانی ارسال شد. لطفاً تا بررسی و پاسخ ادمین شکیبا باشید.", reply_markup=back_to_menu_markup())
        except Exception as e:
            print(f"Error sending photo support to admin: {e}")
            bot.send_message(user_id, "❌ خطایی در ارسال عکس به پشتیبانی رخ داد.", reply_markup=back_to_menu_markup())
    else:
        bot.send_message(user_id, "❌ در حال حاضر فقط ارسال متن و تصویر برای پشتیبانی مقدور است. لطفاً مجدداً تلاش کنید.", reply_markup=back_to_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_purchase(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "کاربر"
    plan_id = call.data.replace("buy_", "")
    
    if plan_id in PLANS:
        plan = PLANS[plan_id]
        user_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), fetchone=True)[0]
        
        if user_balance >= plan['toman_price']:
            new_balance = user_balance - plan['toman_price']
            db_execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id), commit=True)
            
            tx_id_wallet = f"Wallet_{uuid.uuid4().hex[:10]}"
            # وضعیت تراکنش روی 'pending' می‌ماند تا ادمین کانفیگ را تحویل دهد
            db_execute("INSERT INTO transactions (tx_id, user_id, plan_name, amount_trx, status) VALUES (?, ?, ?, 0, 'pending')", (tx_id_wallet, user_id, plan['name']), commit=True)
            
            bot.send_message(user_id, f"💳 <b>خرید با موفقیت از موجودی حساب کسر شد!</b>\n\n📦 پلن: {plan['name']}\n💵 هزینه کسر شده: {plan['toman_price']:,} تومان\n👛 موجودی باقی‌مانده: {new_balance:,} تومان\n\n⏳ درخواست شما برای ادمین ارسال شد. لطفاً تا زمان بررسی و ارسال کانفیگ توسط ادمین شکیبا باشید.", parse_mode="HTML", reply_markup=back_to_menu_markup())
            
            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(
                types.InlineKeyboardButton("✅ ارسال کانفیگ و تایید خرید", callback_data=f"adm_approve:{user_id}:{tx_id_wallet}"),
                types.InlineKeyboardButton("❌ رد خرید و بازگشت وجه", callback_data=f"adm_refund:{user_id}:{tx_id_wallet}:{plan['toman_price']}")
            )
            
            try:
                bot.send_message(ADMIN_ID, f"⚡️ <b>درخواست کانفیگ (خرید با موجودی کیف پول):</b>\n\n👤 کاربر: <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>)\n📦 طرح انتخابی: {plan['name']}\n💰 مبلغ کسر شده: {plan['toman_price']:,} تومان\n\n👇 جهت تحویل کانفیگ روی دکمه زیر کلیک کنید:", parse_mode="HTML", reply_markup=admin_markup)
            except Exception:
                pass
            return

        price_in_trx = round(plan['toman_price'] / TRX_PRICE_IN_TOMAN, 2)
        
        try:
            bot.send_message(ADMIN_ID, f"🛒 <b>گزارش خرید:</b>\nکاربر <a href='tg://user?id={user_id}'>{first_name}</a> (<code>{user_id}</code>) پلن <b>[{plan['name']}]</b> را انتخاب کرد (کسری موجودی).", parse_mode="HTML")
        except Exception:
            pass

        msg = f"💳 <b>دستورالعمل افزایش موجودی و پرداخت طرح {plan['name']}:</b>\n\n💵 قیمت تومانی: <code>{plan['toman_price']:,} تومان</code>\n💰 مقدار قابل واریز به ترون: <code>{price_in_trx} TRX</code>\n🌐 آدرس ولت ترون (TRC-20):\n<code>{TRON_WALLET}</code>\n\n⚠️ پس از واریز، جهت شارژ اکانت و خرید این پلن، حتماً <b>کد پیگیری (TxID)</b> یا <b>اسکرین‌شات رسید</b> را در مرحله بعد بفرستید."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 تایید پرداخت (ارسال هش یا اسکرین‌شات)", callback_data=f"submit_payment:{plan_id}"))
        markup.add(types.InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="back_to_main"))
        bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "submit_general_deposit")
def general_deposit_proof(call):
    user_id = call.from_user.id
    msg = bot.send_message(user_id, "✍️ لطفاً <b>کد پیگیری (Hash)</b> تراکنش واریزی خود را به صورت متنی بفرستید، یا <b>اسکرین‌شات رسید</b> را آپلود کنید:", parse_mode="HTML", reply_markup=back_to_menu_markup())
    bot.register_next_step_handler(msg, save_transaction, "general_deposit")

@bot.callback_query_handler(func=lambda call: call.data.startswith("submit_payment:"))
def ask_for_payment_proof(call):
    user_id = call.from_user.id
    plan_id = call.data.split(":")[1]
    msg = bot.send_message(user_id, "✍️ لطفاً <b>کد پیگیری (Hash)</b> تراکنش خود را به صورت متنی بفرستید، یا <b>اسکرین‌شات رسید</b> را آپلود کنید:", parse_mode="HTML", reply_markup=back_to_menu_markup())
    bot.register_next_step_handler(msg, save_transaction, plan_id)

def save_transaction(message, plan_id):
    user_id = message.from_user.id
    tx_hash = ""
    
    if message.content_type == 'text':
        tx_hash = message.text.strip()
    elif message.content_type == 'photo':
        tx_hash = f"Img_{uuid.uuid4().hex[:12]}"
    else:
        bot.send_message(user_id, "❌ فرمت ارسالی نامعتبر است. لطفاً مجدداً تلاش کنید.", reply_markup=back_to_menu_markup())
        return
        
    if plan_id == "general_deposit":
        plan_name = "افزایش موجودی عمومی حساب"
        amount_trx = 0.0
    else:
        plan_name = PLANS[plan_id]['name']
        amount_trx = round(PLANS[plan_id]['toman_price'] / TRX_PRICE_IN_TOMAN, 2)
        
    try:
        db_execute("INSERT INTO transactions (tx_id, user_id, plan_name, amount_trx) VALUES (?, ?, ?, ?)", (tx_hash, user_id, plan_name, amount_trx), commit=True)
        
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ تایید و شارژ حساب/ارسال کانفیگ", callback_data=f"adm_approve:{user_id}:{tx_hash}"),
            types.InlineKeyboardButton("❌ رد تراکنش", callback_data=f"adm_reject:{user_id}:{tx_hash}")
        )
        
        bot.send_message(user_id, "⏳ رسید یا هش شما ثبت شد و برای پشتیبانی ارسال گردید. پس از بررسی و تایید ادمین، حساب یا سرویس شما فعال می‌شود.", reply_markup=back_to_menu_markup())
        admin_text = f"🔔 <b>درخواست افزایش موجودی/خرید جدید!</b>\n\n👤 کاربر: <code>{user_id}</code>\n📦 بابت: {plan_name}\n"
        if amount_trx > 0:
            admin_text += f"💰 مقدار معادل ترون: {amount_trx} TRX\n"
            
        if message.content_type == 'text':
            admin_text += f"🔗 هش تراکنش:\n<code>{tx_hash}</code>"
            bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=admin_markup)
        elif message.content_type == 'photo':
            admin_text += "🖼 رسید به صورت اسکرین‌شات در زیر ضمیمه شده است."
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_text, parse_mode="HTML", reply_markup=admin_markup)
                
    except sqlite3.IntegrityError:
        bot.send_message(user_id, "❌ این تراکنش یا رسید قبلاً در سیستم ثبت شده است.", reply_markup=back_to_menu_markup())
    except Exception as e:
        print(f"Error sending to admin: {e}")
        bot.send_message(user_id, "❌ خطایی در ارتباط با سرور رخ داد.", reply_markup=back_to_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_") or call.data.startswith("sup_"))
def handle_admin_verification(call):
    data = call.data.split(":")
    action = data[0]
    
    if action == "adm_broadcast":
        ADMIN_STATES[ADMIN_ID] = 'broadcast'
        bot.send_message(ADMIN_ID, "📢 لطفاً متن پیام همگانی خود را بفرستید:")
        bot.answer_callback_query(call.id)
        return
    elif action == "adm_change_trx":
        ADMIN_STATES[ADMIN_ID] = 'change_trx'
        bot.send_message(ADMIN_ID, "💵 قیمت جدید هر ۱ ترون را به تومان (فقط عدد انگلیسی) بفرستید:")
        bot.answer_callback_query(call.id)
        return
    elif action == "adm_close":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "پنل مدیریت بسته شد.")
        return

    target_user_id = int(data[1])
    
    if action == "sup_reply":
        msg = bot.send_message(ADMIN_ID, f"✍️ لطفاً پاسخ خود را (متن یا عکس) برای کاربر <code>{target_user_id}</code> بفرستید:")
        bot.register_next_step_handler(msg, send_support_reply_to_user, target_user_id)
        bot.answer_callback_query(call.id)
        return

    tx_hash = data[2]
    
    if action == "adm_approve":
        tx_data = db_execute("SELECT plan_name, amount_trx FROM transactions WHERE tx_id = ?", (tx_hash,), fetchone=True)
        
        if tx_data and tx_data[0] == "افزایش موجودی عمومی حساب":
            msg = bot.send_message(ADMIN_ID, f"💰 این تراکنش مربوط به افزایش موجودی عمومی است.\nلطفاً <b>مبلغ شارژ حساب به تومان</b> را ارسال کنید تا به کیف پول کاربر اضافه شود:")
            bot.register_next_step_handler(msg, complete_general_deposit, target_user_id, tx_hash, call.message.message_id, call.message.content_type)
        else:
            msg = bot.send_message(ADMIN_ID, f"✍️ لطفاً کانفیگ اختصاصی کاربر <code>{target_user_id}</code> را بفرستید تا همراه تاییدیه خرید برای او ارسال شود:")
            bot.register_next_step_handler(msg, send_custom_config, target_user_id, tx_hash, call.message.message_id, call.message.content_type, tx_data[0] if tx_data else "اکانت اختصاصی")
        bot.answer_callback_query(call.id, "در حال پردازش...")
        
    elif action == "adm_reject":
        db_execute("UPDATE transactions SET status = 'rejected' WHERE tx_id = ?", (tx_hash,), commit=True)
        bot.send_message(target_user_id, "❌ تراکنش یا رسید خرید شما توسط پشتیبانی رد شد. در صورت بروز خطا با پشتیبانی در ارتباط باشید.", reply_markup=back_to_menu_markup())
        bot.answer_callback_query(call.id, "تراکنش رد شد.")
        
        try:
            if call.message.content_type == 'text':
                bot.edit_message_text(f"❌ این تراکنش رد شد. شناسه: {tx_hash}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            else:
                bot.edit_message_caption(f"❌ این تراکنش رد شد. شناسه: {tx_hash}", chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass

    elif action == "adm_refund":
        refund_amount = int(data[3])
        current_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (target_user_id,), fetchone=True)[0]
        new_balance = current_balance + refund_amount
        
        db_execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, target_user_id), commit=True)
        db_execute("UPDATE transactions SET status = 'rejected' WHERE tx_id = ?", (tx_hash,), commit=True)
        
        bot.send_message(target_user_id, f"❌ <b>درخواست خرید شما لغو شد!</b>\n\n💰 مبلغ {refund_amount:,} تومان به کیف پول شما عودت داده شد.\n👛 موجودی فعلی: {new_balance:,} تومان\nلطفاً جهت هماهنگی با پشتیبانی در ارتباط باشید.", reply_markup=back_to_menu_markup())
        bot.answer_callback_query(call.id, "خرید رد و وجه بازگردانده شد.")
        
        try:
            bot.edit_message_text(f"❌ درخواست خرید رد شد و مبلغ {refund_amount:,} تومان به حساب کاربر عودت داده شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass

def complete_general_deposit(message, target_user_id, tx_hash, original_msg_id, original_content_type):
    if not message.text or not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ خطا: لطفاً مقدار افزایش موجودی را فقط به صورت عدد انگلیسی و به تومان وارد کنید.")
        return
        
    deposit_amount = int(message.text.strip())
    current_balance = db_execute("SELECT balance FROM users WHERE user_id = ?", (target_user_id,), fetchone=True)[0]
    new_balance = current_balance + deposit_amount
    
    db_execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, target_user_id), commit=True)
    db_execute("UPDATE transactions SET status = 'approved' WHERE tx_id = ?", (tx_hash,), commit=True)
    
    bot.send_message(target_user_id, f"🎉 <b>حساب شما شارژ شد!</b>\n\n💵 مبلغ افزوده شده: {deposit_amount:,} تومان\n👛 موجودی جدید کیف پول: {new_balance:,} تومان", parse_mode="HTML", reply_markup=back_to_menu_markup())
    bot.send_message(ADMIN_ID, f"✅ حساب کاربر {target_user_id} با موفقیت به میزان {deposit_amount:,} تومان شارژ شد.")
    
    try:
        if original_content_type == 'text':
            bot.edit_message_text(f"✅ تایید شد. حساب کاربر به مبلغ {deposit_amount:,} تومان شارژ گردید.", chat_id=ADMIN_ID, message_id=original_msg_id)
        else:
            bot.edit_message_caption(f"✅ تایید شد. حساب کاربر به مبلغ {deposit_amount:,} تومان شارژ گردید.", chat_id=ADMIN_ID, message_id=original_msg_id)
    except Exception:
        pass

def send_custom_config(message, target_user_id, tx_hash, original_msg_id, original_content_type, plan_name):
    custom_config = message.text.strip() if message.content_type == 'text' else ""
    if not custom_config:
        bot.send_message(ADMIN_ID, "❌ خطا: لطفاً کانفیگ را فقط به صورت پیام متنی ارسال کنید.")
        return
        
    db_execute("UPDATE transactions SET status = 'approved' WHERE tx_id = ?", (tx_hash,), commit=True)
    
    db_execute("INSERT INTO services (id, user_id, plan_name, config_text, date_added) VALUES (?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4())[:8], target_user_id, plan_name, custom_config), commit=True)
    
    user_msg = f"🎉 <b>خرید شما تایید شد!</b>\n\nکانفیگ اختصاصی شما صادر و در بخش 'کانفیگ‌های من' ذخیره شد:\n\n<code>{custom_config}</code>"
    bot.send_message(target_user_id, user_msg, parse_mode="HTML", reply_markup=back_to_menu_markup())
    bot.send_message(ADMIN_ID, "✅ کانفیگ با موفقیت به کاربر ارسال و در سیستم آرشیو شد.")
    
    try:
        if original_content_type == 'text':
            bot.edit_message_text(f"✅ تایید شد و کانفیگ اختصاصی ارسال گردید. شناسه: {tx_hash}", chat_id=ADMIN_ID, message_id=original_msg_id)
        else:
            bot.edit_message_caption(f"✅ تایید شد و کانفیگ اختصاصی ارسال گردید. شناسه: {tx_hash}", chat_id=ADMIN_ID, message_id=original_msg_id)
    except Exception:
        pass

def send_support_reply_to_user(message, target_user_id):
    try:
        if message.content_type == 'text':
            reply_text = message.text.strip()
            user_msg = f"🔔 <b>پاسخ پشتیبانی:</b>\n\n{reply_text}"
            bot.send_message(target_user_id, user_msg, parse_mode="HTML", reply_markup=back_to_menu_markup())
            
        elif message.content_type == 'photo':
            caption_text = message.caption.strip() if message.caption else ""
            user_msg = f"🔔 <b>پاسخ پشتیبانی:</b>\n\n{caption_text}" if caption_text else "🔔 <b>پاسخ پشتیبانی (تصویر ضمیمه شده):</b>"
            bot.send_photo(target_user_id, message.photo[-1].file_id, caption=user_msg, parse_mode="HTML", reply_markup=back_to_menu_markup())
            
        else:
            bot.send_message(ADMIN_ID, "❌ خطا: نوع پیام ارسالی توسط شما برای پاسخ پشتیبانی معتبر نیست (فقط متن یا تصویر).")
            return
            
        bot.send_message(ADMIN_ID, "✅ پاسخ شما با موفقیت برای کاربر ارسال شد.")
    except Exception as e:
        print(f"Error replying to user: {e}")
        bot.send_message(ADMIN_ID, "❌ خطایی رخ داد. ممکن است کاربر ربات را بلاک کرده باشد.")

print("َARSHYA BOT HAS BEEN STARTED")
bot.infinity_polling()
