import os
import logging
import sys

# استيراد العناصر الضرورية من مكتبة python-telegram-bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# === إعدادات البيئة ===
# يتم تعيين PORT تلقائياً على Render
PORT = int(os.environ.get('PORT', 8080))
# اسم النطاق الخارجي (مثل: your-service-name.onrender.com)
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
# توكن البوت
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_EMAIL = "kaderezakariaa@gmail.com"

# === إعدادات التسجيل (Logging) ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

if not TOKEN:
    logger.error("خطأ فادح: لم يتم العثور على توكن البوت في متغيرات البيئة.")
    sys.exit(1)

# === البيانات والقيم الثابتة ===
# للتخزين المؤقت، (هذه البيانات ستُمسح عند إعادة تشغيل الخادم، يفضل استخدام قاعدة بيانات)
user_balances = {}
PRICES = {'watch_video': 50, 'browse_web': 30, 'play_games': 20}
MIN_WITHDRAWAL = 500

# === الدوال المساعدة ===
def get_main_keyboard() -> InlineKeyboardMarkup:
    """بناء لوحة المفاتيح الرئيسية للخدمات."""
    keyboard = [
        [InlineKeyboardButton("📺 مشاهدة الفيديوهات (50 د.ج)", callback_data='service_watch_video')],
        [InlineKeyboardButton("🌐 تصفح المواقع (30 د.ج)", callback_data='service_browse_web')],
        [InlineKeyboardButton("🎮 ألعاب وتاريخ الجزائر (20 د.ج)", callback_data='service_play_games')],
        [InlineKeyboardButton("💰 رصيدي/سحب", callback_data='show_balance')],
        [InlineKeyboardButton("✉️ دعم العملاء", callback_data='support_contact')]
    ]
    return InlineKeyboardMarkup(keyboard)

# === معالجات الأوامر والردود التلقائية ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start."""
    chat = update.message or update.callback_query.message
    user_id = chat.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    balance = user_balances[user_id]
    
    message_text = f"""مرحباً بك! رصيدك الحالي هو: **{balance} د.ج**.
اختر الخدمة التي تريدها:"""
    
    await chat.reply_text(message_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج ضغطات الأزرار (Callback Queries)."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith('service_'):
        service_key = data.replace('service_', '')
        price = PRICES.get(service_key, 0)
        user_balances[user_id] = user_balances.get(user_id, 0) + price
        new_balance = user_balances[user_id]
        
        messages = {
            'watch_video': f"تمت إضافة **{price} د.ج** إلى رصيدك. ابدأ مشاهدة الفيديو الآن.",
            'browse_web': f"تمت إضافة **{price} د.ج** إلى رصيدك. تفضل برابط تصفح المواقع.",
            'play_games': f"تمت إضافة **{price} د.ج** إلى رصيدك. إليك رابط الألعاب المصغرة."
        }
        
        message = f"""✅ تم تفعيل الخدمة بنجاح!
{messages.get(service_key, '')}
رصيدك الجديد: **{new_balance} د.ج**."""
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard()) # تم التعديل لإعادة لوحة المفاتيح
        
    elif data == 'show_balance':
        balance = user_balances.get(user_id, 0)
        keyboard = [[InlineKeyboardButton("🔄 العودة للقائمة", callback_data='return_to_menu')]]
        
        if balance >= MIN_WITHDRAWAL:
            keyboard.insert(0, [InlineKeyboardButton("💸 طلب سحب الرصيد", callback_data='request_withdrawal')])
            message = f"""💰 رصيدك الحالي: **{balance} د.ج**.
تهانينا! يمكنك الآن طلب السحب."""
        else:
            needed = MIN_WITHDRAWAL - balance
            message = f"""💰 رصيدك الحالي: **{balance} د.ج**.
⚠️ الحد الأدنى للسحب هو {MIN_WITHDRAWAL} د.ج. ما زلت بحاجة إلى **{needed} د.ج**."""
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
    elif data == 'request_withdrawal':
        # في تطبيق واقعي، يجب هنا تسجيل الطلب في قاعدة بيانات
        await query.edit_message_text("✅ تم تسجيل طلب السحب! سيتم التواصل معك قريباً على حسابك في تيليجرام لإتمام عملية الدفع.")
        
    elif data == 'support_contact':
        message = f"""📧 **دعم العملاء**:
إذا واجهتك أي مشكلة، يرجى إرسال رسالة إلينا عبر البريد الإلكتروني:
`{SUPPORT_EMAIL}`
وسنقوم بالرد عليك في أقرب وقت ممكن. شكراً لك."""
        keyboard = [[InlineKeyboardButton("🔄 العودة للقائمة", callback_data='return_to_menu')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
    elif data == 'return_to_menu':
        balance = user_balances.get(user_id, 0)
        message_text = f"""مرحباً بك! رصيدك الحالي هو: **{balance} د.ج**.
اختر الخدمة التي تريدها:"""
        await query.edit_message_text(message_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)

# === بناء التطبيق ===
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_callback))

# === دالة التشغيل الرئيسية ===
def main() -> None:
    """يبدأ تشغيل البوت باستخدام الـ Webhook ويضمن استخدام HTTPS."""
    if not RENDER_EXTERNAL_HOSTNAME:
        logger.error("خطأ: لم يتم العثور على RENDER_EXTERNAL_HOSTNAME. الرجاء تعيينه في إعدادات Render.")
        sys.exit(1)
        
    # بناء رابط الـ Webhook الصحيح والآمن (HTTPS)
    # المكتبة ستقوم بدمج هذا الرابط مع المسار السري (TOKEN) وتعيينه تلقائياً.
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}"

    logger.info(f"بدء تشغيل البوت على Webhook: {webhook_url}/{TOKEN}")
    
    # استخدام run_webhook لتشغيل الخادم وتعيين الـ Webhook في تليجرام تلقائياً
    application.run_webhook(
        listen='0.0.0.0',
        port=PORT,
        url_path=TOKEN,        # المسار السري (endpoint) الذي يستقبل الرسائل
        webhook_url=webhook_url  # الرابط الأساسي الذي يتم إرساله لتليجرام (يجب أن يكون HTTPS)
    )

if __name__ == '__main__':
    main()
