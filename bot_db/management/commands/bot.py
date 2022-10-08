import logging
from pathlib import Path
from bot_db.models import Diet
from django.views.decorators.csrf import csrf_exempt
from django.core.management.base import BaseCommand
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
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
    CHOOSE_FROM_ACCOUNT_MENU,
) = range(7)

# Diet types
# TODO fetch the values from Django


def start(update: Update, context: CallbackContext) -> int:
    try:
        # TODO check if user already in DB
        return main_menu(update, context)

    except ZeroDivisionError:  # TODO except user does not exist:
        # TODO add view & url to privacy policy
        message_text = bot_strings.accept_policy_message
        keyboard = [
            [
                InlineKeyboardButton(bot_strings.register_button, callback_data='register'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_chat.send_message(message_text, reply_markup=reply_markup)
        return AWAIT_REGISTRATION


def request_name(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(bot_strings.request_name)

    return AWAIT_NAME


def request_confirm_name(update: Update, context: CallbackContext) -> int:
    """Store user's name and ask user to confirm it."""
    context.chat_data['name'] = name = update.message.text

    message_text = bot_strings.confirm_name.format(name)
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.yes_button, callback_data='confirm'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    return AWAIT_CONFIRMATION


def complete_registration(update: Update, context: CallbackContext):
    name = context.chat_data['name']

    # TODO send user to Django

    return main_menu(update, context)


def main_menu(update: Update, context: CallbackContext):
    """Show buttons for branches: get a recipe, manage account, get a paid subscription."""

    query = update.callback_query
    if query:
        query.answer()

    message_text = bot_strings.main_menu

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.new_recipe_button, callback_data='new_recipe'),
        ],
        [
            InlineKeyboardButton(bot_strings.account_menu_button, callback_data='account'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


def request_diet(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    message_text = bot_strings.request_diet
    keyboard = []
    diets = Diet.objects.all()
    for i, diet in enumerate(diets):
        keyboard.append([InlineKeyboardButton(diet.title, callback_data=f'diet_{i}')])
    keyboard.append([InlineKeyboardButton(bot_strings.any_diet_button, callback_data='diet_any')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    if query:
        query.message.delete()


def show_new_recipe(update: Update, context: CallbackContext):
    # TODO check excluded recipes
    # TODO no recipes with allergy ingredients

    query = update.callback_query
    query.answer()

    selected_diet = query.data

    # TODO get a recipe from Django
    recipe_id = 123
    recipe_title = 'Replace'
    recipe_description = 'Me'
    recipe_ingredients = ('With: data\n'
                          'from: Django')
    recipe_photo = 'https://ic.pics.livejournal.com/maxim_nm/51556845/6518023/6518023_original.jpg'

    message_text = bot_strings.recipe.format(title=recipe_title,
                                             description=recipe_description,
                                             ingredients=recipe_ingredients)

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.add_to_favorites_button,
                                 callback_data=f'add_to_favorites_{recipe_id}'),
        ],
        [
            InlineKeyboardButton(bot_strings.exclude_recipe_button,
                                 callback_data=f'exclude_recipe_{recipe_id}'),
        ],
        [
            InlineKeyboardButton(bot_strings.another_recipe_same_diet, callback_data=selected_diet),
        ],
        [
            InlineKeyboardButton(bot_strings.another_recipe_diff_diet, callback_data='new_recipe'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_photo(recipe_photo, caption=message_text, reply_markup=reply_markup)
    if query:
        query.message.delete()


def add_recipe_to_favorites(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    recipe_id = int(query.data.removeprefix('add_to_favorites_'))

    # TODO Django add Recipe to User's favorites
    print(f'added recipe {recipe_id} to favorites.')

    message_text = bot_strings.recipe_added_to_favorites

    keyboard = [[
        InlineKeyboardButton(bot_strings.cancel_button, callback_data=f'cancel_favorite_{recipe_id}'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)


def exclude_recipe(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    recipe_id = int(query.data.removeprefix('exclude_recipe_'))

    # TODO Django add Recipe to User's excluded
    print(f'excluded recipe {recipe_id}.')

    message_text = bot_strings.recipe_excluded

    keyboard = [[
        InlineKeyboardButton(bot_strings.cancel_button, callback_data=f'cancel_exclude_{recipe_id}'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)


def cancel_preference_operation(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    _, operation_type, recipe_id = query.data.split('_')

    if operation_type == 'favorite':
        # TODO remove recipe_id from User.favorite_recipes
        pass

    else:
        # TODO remove recipe_id from User.excluded_recipes
        pass

    message_text = bot_strings.operation_cancelled
    query.edit_message_text(message_text)


def account_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    message_text = bot_strings.account_menu
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.favorite_recipes_button, callback_data='favorite_recipes'),
        ],
        [
            InlineKeyboardButton(bot_strings.excluded_recipes_button, callback_data='excluded_recipes'),
        ],
        [
            InlineKeyboardButton(bot_strings.allergies_button, callback_data='allergies'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)


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
            ],
            states={
                AWAIT_REGISTRATION: [CallbackQueryHandler(request_name, pattern=r'^register$')],
                AWAIT_NAME: [MessageHandler(Filters.text & ~Filters.command, request_confirm_name)],
                AWAIT_CONFIRMATION: [
                    CallbackQueryHandler(request_name, pattern=r'^back_to_name$'),
                    CallbackQueryHandler(complete_registration, pattern=r'^confirm$')
                ],
            },
            fallbacks=[
                CommandHandler('start', start),
                MessageHandler(Filters.text, help_message),
                ]
        )

        dispatcher.add_handler(CallbackQueryHandler(account_menu, pattern=r'^account$'))
        dispatcher.add_handler(CallbackQueryHandler(request_diet, pattern=r'^new_recipe$'))
        dispatcher.add_handler(CallbackQueryHandler(show_new_recipe, pattern=r'^diet_\d+$|^diet_any$'))
        dispatcher.add_handler(CallbackQueryHandler(add_recipe_to_favorites, pattern=r'^add_to_favorites_\d+$'))
        dispatcher.add_handler(CallbackQueryHandler(exclude_recipe, pattern=r'^exclude_recipe_\d+$'))
        dispatcher.add_handler(CallbackQueryHandler(cancel_preference_operation, pattern=r'^cancel_.+$'))

        dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern=r'^back_to_main$'))

        dispatcher.add_handler(conversation_handler)

        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    Command().handle()
