import logging


from django.views.decorators.csrf import csrf_exempt
from django.core.management.base import BaseCommand
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import error as telegram_error
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

import bot_strings

# Conversation states
(
    AWAIT_REGISTRATION,
    AWAIT_NAME,
    AWAIT_CONFIRMATION,
    CHOOSE_FROM_MAIN_MENU,
    AWAIT_DIET,
    SHOW_NEW_RECIPE,
) = range(6)

# Diet types
# TODO fetch the values from Django
DIETS = (
    'VEGAN',
    'VEGETARIAN',
    'SEAFOOD',
    'GLUTEN_FREE',
)


def start(update: Update, context: CallbackContext) -> int:
    message_text = bot_strings.accept_privacy_message

    try:
        # TODO check if user already in DB
        return main_menu(update, context)

    except ZeroDivisionError:  # TODO except user does not exist:
        keyboard = [
            [
                InlineKeyboardButton('TEXT: SHOW PRIVACY POLICY', callback_data='show_policy'),
            ],
            [
                InlineKeyboardButton('TEXT: ACCEPT & REGISTER BUTTON', callback_data='register'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(message_text, reply_markup=reply_markup)
        return AWAIT_REGISTRATION


def show_privacy_policy(update: Update, context: CallbackContext) -> int:
    # TODO send privacy policy

    keyboard = [
        [
            InlineKeyboardButton('TEXT: ACCEPT & REGISTER BUTTON', callback_data='register'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('TEXT: accept_privacy_message', reply_markup=reply_markup)
    return AWAIT_REGISTRATION


def request_name(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text('TEXT: request_name')

    # store this message to delete it in the next step
    context.chat_data['message_to_delete'] = query.message.message_id

    return AWAIT_NAME


def confirm_name(update: Update, context: CallbackContext) -> int:
    # TODO confirm or go back to reenter name

    if 'message_to_delete' in context.chat_data:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.chat_data['message_to_delete']
        )
        del context.chat_data['message_to_delete']

    return AWAIT_CONFIRMATION


def complete_registration(update: Update, context: CallbackContext):
    if update.message:
        user_name = update.message.text

    if 'message_to_delete' in context.chat_data:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.chat_data['message_to_delete']
        )
        del context.chat_data['message_to_delete']

    # TODO send user to Django

    return main_menu(update, context)


def main_menu(update: Update, context: CallbackContext):
    """Show buttons for branches: get a recipe, manage account, get a paid subscription."""

    query = update.callback_query
    if query:
        query.answer()

    message_text = 'TEXT: main menu'

    keyboard = [
        [
            InlineKeyboardButton('TEXT: GIVE ME A RECIPE', callback_data='new_recipe'),
        ],
        [
            InlineKeyboardButton('TEXT: ACCOUNT SETTINGS', callback_data='account'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    return CHOOSE_FROM_MAIN_MENU


def request_diet(update: Update, context: CallbackContext):
    # TODO diet buttons with callback_query data
    query = update.callback_query
    query.answer()

    message_text = 'TEXT: request diet \n CONVERSATION STAGE: AWAIT_DIET'
    keyboard = []

    for i, diet in enumerate(DIETS):
        keyboard.append([InlineKeyboardButton(diet, callback_data=f'diet_{i}')])
        print(diet, f'diet_{i}')

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    return AWAIT_DIET


def show_new_recipe(update: Update, context: CallbackContext):
    # TODO check excluded recipes
    # TODO no recipes with allergy ingredients
    query = update.callback_query
    query.answer()

    message_text = f'option selected: {query.data} \n CONTENT: RECIPE WITH PHOTO \n CONVERSATION STAGE: SHOW_NEW_RECIPE'
    query.edit_message_text(message_text)


def add_recipe_to_favorites(update: Update, context: CallbackContext):
    pass


def exclude_recipe(update: Update, context: CallbackContext):
    pass


def cancel_preference_operation(update: Update, context: CallbackContext):
    pass


def account_menu(update: Update, context: CallbackContext):
    pass


def favorite_recipes(update: Update, context: CallbackContext):
    """Fetch saved recipes from DB and show them to user as buttons.
    Break up into pages, 5 per page.
    """
    pass


def show_favorite_recipe(update: Update, context: CallbackContext):
    pass


def remove_recipe_from_favorites(update: Update, context: CallbackContext):
    pass


def excluded_recipes(update: Update, context: CallbackContext):
    pass


def show_excluded_recipe(update: Update, context: CallbackContext):
    pass


def remove_recipe_from_excluded(update: Update, context: CallbackContext):
    pass


def allergies(update: Update, context: CallbackContext):
    """Show user saved allergies as buttons (pressing the button deletes the allergy).
    Another button shows the menu for adding a new allergy.
    """
    pass


def remove_allergy(update: Update, context: CallbackContext):
    pass


def show_ingredient_groups(update: Update, context: CallbackContext):
    pass


def show_ingredients_in_group(update: Update, context: CallbackContext):
    pass


def add_allergy_to_single_ingredient(update: Update, context: CallbackContext):
    pass


def add_allergy_to_ingredient_group(update: Update, context: CallbackContext):
    pass


def back_to_main(update: Update, context: CallbackContext):
    """A command that can be selected at any time to abandon an incomplete branch and go to main menu"""
    pass


def help_message(update: Update, context: CallbackContext):
    """Send help text"""
    update.effective_chat.send_message('TEXT: HELP')


class Command(BaseCommand):
    help = 'Запуск чат-бота'

    def handle(self, *args, **options):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        logger = logging.getLogger(__name__)

        env = Env()
        env.read_env()
        tg_token = env('TG_TOKEN')
        updater = Updater(tg_token)
        dispatcher = updater.dispatcher

        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CallbackQueryHandler(..., pattern=r'^...$'),
                MessageHandler(Filters.text, help_message),
            ],
            states={
                AWAIT_REGISTRATION: [CallbackQueryHandler(request_name, pattern=r'^register$')],
                AWAIT_NAME: [MessageHandler(Filters.text & ~Filters.command, confirm_name)],
                AWAIT_CONFIRMATION: [
                    CallbackQueryHandler(request_name, pattern=r'^back_to_name$'),
                    CallbackQueryHandler(complete_registration, pattern=r'^confirm$')
                ],
                CHOOSE_FROM_MAIN_MENU: [
                    CallbackQueryHandler(request_diet, pattern=r'^new_recipe$'),
                    CallbackQueryHandler(account_menu, pattern=r'^account$'),
                ],
                AWAIT_DIET: [
                    CallbackQueryHandler(show_new_recipe, pattern=r'^diet_\d+$'),
                ],
                SHOW_NEW_RECIPE: [
                    CallbackQueryHandler(add_recipe_to_favorites, pattern=r'^...$'),
                    CallbackQueryHandler(exclude_recipe, pattern=r'^...$')
                ],

                # ...: ...,
            },
            fallbacks=[
                CallbackQueryHandler(back_to_main, pattern=r'^back_to_main$'),
                CommandHandler('back_to_main', back_to_main),
                MessageHandler(Filters.text, help_message),
                ]
        )

        dispatcher.add_handler(conversation_handler)

        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    Command().handle()
