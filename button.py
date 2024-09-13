from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters
from telegram_bot import remove_voice_from_video, add_voice_to_video, remove_add_voice_to_video, clean_noise_from_audio, clean_noise_from_video, handle_file, handle_user_state
from config import TOKEN


# بيانات المستخدم المحفوظة
user_data = {}

# رسائل متعددة اللغات
MESSAGES = {
    'en': {
        'send_video': 'Please send the video.',
        'remove_voice_from_video': 'Remove voice from video',
        'add_voice_to_video': 'Add voice to video',
        'remove_add_voice_video': 'Remove and add voice to video',
        'clean_noise_audio': 'Clean noise from audio',
        'clean_noise_video': 'Clean noise from video',
        'start': 'Welcome! Choose an option below:',
        'language_set': 'Language has been set.',
    },
    'ar': {
        'send_video': 'يرجى إرسال الفيديو.',
        'remove_voice_from_video': 'إزالة الصوت من الفيديو',
        'add_voice_to_video': 'إضافة صوت إلى الفيديو',
        'remove_add_voice_video': 'إزالة وإضافة صوت إلى الفيديو',
        'clean_noise_audio': 'تنظيف الضوضاء من الصوت',
        'clean_noise_video': 'تنظيف الضوضاء من الفيديو',
        'start': 'مرحبا! اختر خيارا أدناه:',
        'language_set': 'تم تعيين اللغة.',
    }
}

async def handle_non_command_message(update: Update, context: CallbackContext):
    if update.message.text and not update.message.text.startswith('/'):  
        keyboard = [[InlineKeyboardButton("Start", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Click start to begin', reply_markup=reply_markup)

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    keyboard = [
        [InlineKeyboardButton("Choose Language", callback_data='choose_language')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_message(user_id, 'send_video'), reply_markup=reply_markup)

def get_message(user_id, key):
    language = user_data.get(user_id, {}).get('language', 'en')
    return MESSAGES.get(language, {}).get(key, 'Message not found')

async def set_language(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("English", callback_data='en')],
        [InlineKeyboardButton("العربية", callback_data='ar')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose your language / اختر لغتك:', reply_markup=reply_markup)

async def show_command_buttons(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'en')
    keyboard = [
        [InlineKeyboardButton(MESSAGES[language]['remove_voice_from_video'], callback_data='remove_voice_from_video')],
        [InlineKeyboardButton(MESSAGES[language]['add_voice_to_video'], callback_data='add_voice_to_video')],
        [InlineKeyboardButton(MESSAGES[language]['remove_add_voice_video'], callback_data='remove_add_voice_video')],
        [InlineKeyboardButton(MESSAGES[language]['clean_noise_audio'], callback_data='clean_noise_audio')],
        [InlineKeyboardButton(MESSAGES[language]['clean_noise_video'], callback_data='clean_noise_video')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text=MESSAGES[language]['start'], reply_markup=reply_markup)

async def handle_command_button(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    command_map = {
        'remove_voice_from_video': remove_voice_from_video,
        'add_voice_to_video': add_voice_to_video,
        'remove_add_voice_video': remove_add_voice_to_video,
        'clean_noise_audio': clean_noise_from_audio,
        'clean_noise_video': clean_noise_from_video
    }

    handler = command_map.get(data, start)
    await handler(update, context)

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    if callback_data == 'start':
        await start(update, context)
    elif callback_data == 'choose_language':
        await set_language(update, context)
    else:
        await handle_command_button(update, context)

    user_data[user_id] = {'language': callback_data}
    await query.answer()
    await query.edit_message_text(get_message(user_id, 'language_set'))

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.text & ~filters.command, handle_non_command_message))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_command_message))
    app.add_handler(CallbackQueryHandler(button))

    # Message handlers
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    app.add_handler(MessageHandler(filters.VIDEO, handle_user_state))
    app.add_handler(MessageHandler(filters.AUDIO, handle_user_state))    

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
