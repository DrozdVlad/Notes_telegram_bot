import random
import json
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, \
    CommandHandler, Filters
from telegram.utils.request import Request

from settings import TOKEN

FULL_NAME = 1
PHONE = 2
OTP = 3
WORK_WITH_NOTES = 4
WRITE_NOTE = 5
READ_NOTE = 6
WRITE_NOTE_HANDLER = 7


def start_buttons_handler(update: Update, context: CallbackContext):
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Да', callback_data='true'),
                InlineKeyboardButton(text='Нет', callback_data='false')
            ],
        ],
    )
    update.message.reply_text(
        'Хотите начать сейчас?',
        reply_markup=inline_buttons,
    )
    return FULL_NAME


def name_handler(update: Update, context: CallbackContext):
    init = update.callback_query.data
    chat_id = update.callback_query.message.chat.id
    if init == 'true':
        update.callback_query.bot.send_message(
            chat_id=chat_id,
            text='Введи ФИО',
        )
        return PHONE
    else:
        update.callback_query.bot.send_message(
            chat_id=chat_id,
            text='Ну тогда в другой раз',
        )
        return ConversationHandler.END


def phone_handler(update: Update, context: CallbackContext):
    full_name = context.user_data[FULL_NAME] = update.message.text

    update.message.reply_text(
        text='Введите ваш номер телефона',
    )
    return OTP


def otp_handler(update: Update, context: CallbackContext):
    phone = context.user_data[PHONE] = update.message.text
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Написать заметку', callback_data='write_note'),
                InlineKeyboardButton(text='Просмотреть заметки', callback_data='read_note')
            ],
        ],
    )
    otp = random.randrange(10000000, 99999999)
    try:
        with open('notes.json', 'r') as f:
            notes = json.load(f)
    except FileNotFoundError:
        notes = {}

    notes[f'person{phone}'] = {
        'full_name': context.user_data[FULL_NAME],
        'phone': context.user_data[PHONE],
        'otp': otp,
        'notes': []
    }

    with open('notes.json', 'w') as f:
        json.dump(notes, f)
    update.message.reply_text(
        text=f'Вот ваш персональный код: {otp}',
        reply_markup=inline_buttons
    )
    return WORK_WITH_NOTES


def work_with_notes(update: Update, context: CallbackContext):
    button_request = update.callback_query.data
    chat_id = update.callback_query.message.chat.id
    context.user_data[WORK_WITH_NOTES] = button_request
    if button_request == 'write_note':
        update.callback_query.bot.send_message(
            chat_id=chat_id,
            text='Введи OTP',
        )
        return WRITE_NOTE
    else:
        update.callback_query.bot.send_message(
            chat_id=chat_id,
            text='Введи OTP',
        )
        return READ_NOTE


def write_note(update: Update, context: CallbackContext):
    context.user_data[WRITE_NOTE] = update.message.text
    update.message.reply_text(
        text=f'Жду вашу заметку',
    )
    return WRITE_NOTE_HANDLER


def read_notes(update: Update, context: CallbackContext):
    otp_check = update.message.text
    data = {}
    with open('notes.json', 'r') as f:
        notes = json.load(f)
    for k, v in notes.items():
        if int(v['otp']) == int(otp_check):
            data['notes'] = v['notes']
    update.message.reply_text(
        text=f'ваши заметки: {data["notes"]}'
    )
    return ConversationHandler.END


def write_note_handler(update: Update, context: CallbackContext):
    otp_check = context.user_data[WRITE_NOTE]
    note = update.message.text
    with open('notes.json', 'r') as f:
        notes = json.load(f)

    for k, v in notes.items():
        if int(v['otp']) == int(otp_check):
            v['notes'].append(note)
    with open('notes.json', 'w') as f:
        json.dump(notes, f)
    return ConversationHandler.END


def cancel_handler(update: Update, context: CallbackContext):
    update.message.reply_text('Отмена. Для начала с нуля нажмите /start')
    return ConversationHandler.END


def main():
    req = Request(
        connect_timeout=0.5,
        read_timeout=1.0,
    )
    bot = Bot(
        token=TOKEN,
        request=req,
    )
    updater = Updater(
        bot=bot,
        use_context=True,
    )

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_buttons_handler, pass_user_data=True),
        ],
        states={
            FULL_NAME: [
                CallbackQueryHandler(name_handler, pass_user_data=True),
            ],
            PHONE: [
                MessageHandler(Filters.all, phone_handler, pass_user_data=True),
            ],
            OTP: [
                MessageHandler(Filters.all, otp_handler, pass_user_data=True),
            ],
            WORK_WITH_NOTES: [
                CallbackQueryHandler(work_with_notes, pass_user_data=True)
            ],
            WRITE_NOTE: [
                MessageHandler(Filters.all, write_note, pass_user_data=True)
            ],
            READ_NOTE: [
                MessageHandler(Filters.all, read_notes, pass_user_data=True)
            ],
            WRITE_NOTE_HANDLER: [
                MessageHandler(Filters.all, write_note_handler, pass_user_data=True)
            ]

        },
        fallbacks=[
            CommandHandler('cancel', cancel_handler),
        ],
    )
    updater.dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
