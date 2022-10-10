import logging
import random

import django.db

from bot_db.models import Diet, Recipe, Customer
from django.views.decorators.csrf import csrf_exempt
from django.core.management.base import BaseCommand
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram import PreCheckoutQuery
from telegram import error as telegram_error
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
    PreCheckoutQueryHandler,
)

import bot_strings

env = Env()
env.read_env()
payments_token = env('PAYMENTS_TOKEN')

# Conversation states
(
    AWAIT_REGISTRATION,
    AWAIT_NAME,
    AWAIT_CONFIRMATION,
) = range(3)


# TODO
def format_recipe_message(recipe: Recipe):
    return bot_strings.recipe.format(title=recipe.title,
                                     description=recipe.description,
                                     ingredients=recipe.ingredients,
                                     )


def start(update: Update, context: CallbackContext) -> int or None:
    try:
        Customer.objects.get(user_id=update.effective_user.id)
        return main_menu(update, context)

    except Customer.DoesNotExist:
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
    if query:
        query.answer()
        query.edit_message_text(bot_strings.request_name)
    else:
        update.effective_chat.send_message(bot_strings.request_name)

    return AWAIT_NAME


def request_confirm_name(update: Update, context: CallbackContext) -> int:
    """Store user's name and ask user to confirm it."""
    context.chat_data['name'] = name = update.message.text

    message_text = bot_strings.confirm_name.format(name)
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.yes_button, callback_data='confirm'),
            InlineKeyboardButton(bot_strings.no_button, callback_data='back_to_name'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    return AWAIT_CONFIRMATION


def complete_registration(update: Update, context: CallbackContext):
    name = context.chat_data['name']

    try:
        Customer.objects.create(user_id=update.effective_user.id, full_name=name)
        message_text = bot_strings.registration_successful
    except django.db.Error:
        message_text = bot_strings.db_error_message

    update.effective_chat.send_message(message_text)
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

        # [
        #     InlineKeyboardButton(bot_strings.subscribe, callback_data='subscribe'),
        # ],

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
    for diet in diets:
        keyboard.append([InlineKeyboardButton(diet.title, callback_data=f'diet_{diet.id}')])
    keyboard.append([InlineKeyboardButton(bot_strings.any_diet_button, callback_data='diet_any')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    if query:
        query.message.delete()


def show_new_recipe(update: Update, context: CallbackContext):
    # TODO no recipes with allergy ingredients

    query = update.callback_query
    query.answer()

    selected_diet_id = query.data.removeprefix('diet_')
    if selected_diet_id != 'any':
        recipes = Recipe.objects.filter(diet=selected_diet_id)\
            .exclude(excluded_by__user_id=update.effective_user.id)

    else:
        recipes = Recipe.objects.exclude(excluded_by__user_id=update.effective_user.id)

    recipe = random.choice(recipes)

    message_text = format_recipe_message(recipe)
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.add_to_favorites_button,
                                 callback_data=f'add_to_favorites_{recipe.id}'),
        ],
        [
            InlineKeyboardButton(bot_strings.exclude_recipe_button,
                                 callback_data=f'exclude_recipe_{recipe.id}'),
        ],
        [
            InlineKeyboardButton(bot_strings.another_recipe_same_diet, callback_data=query.data),
        ],
        [
            InlineKeyboardButton(bot_strings.another_recipe_diff_diet, callback_data='new_recipe'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # if recipe.image is not None:
    #     recipe_image = recipe.image
    # else:
    recipe_image = recipe.image or 'https://semantic-ui.com/images/wireframe/image.png'
    update.effective_chat.send_photo(recipe_image, caption=message_text, reply_markup=reply_markup)
    
    if query:
        query.message.delete()    


# TODO move into its own branch
def test_payment(update, context):
    price = LabeledPrice(label='Подписка на 1 месяц', amount=50000)
    message_text = 'Тестовый платеж!'
    update.effective_chat.send_message(message_text)
    update.effective_chat.send_invoice(
        title='Подписка на бота',
        description='активация подписки на бота на 1 месяц',
        provider_token=payments_token,
        currency='rub',
        is_flexible=False,
        prices=[price],
        payload='test-invoice-payload'
         )
    

def precheckout_callback(update: Update, context: CallbackContext):    
    query = update.pre_checkout_query
    query.answer(ok=True)
    
    
def add_recipe_to_favorites(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    recipe_id = query.data.removeprefix('add_to_favorites_')

    recipe = Recipe.objects.get(id=recipe_id)
    customer = Customer.objects.get(user_id=update.effective_user.id)
    customer.favorite_recipes.add(recipe)

    message_text = bot_strings.recipe_added_to_favorites

    keyboard = [[
        InlineKeyboardButton(bot_strings.cancel_button, callback_data=f'cancel_favorite_{recipe_id}'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)


def exclude_recipe(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    recipe_id = query.data.removeprefix('exclude_recipe_')

    recipe = Recipe.objects.get(id=recipe_id)
    customer = Customer.objects.get(user_id=update.effective_user.id)
    customer.excluded_recipes.add(recipe)

    message_text = bot_strings.recipe_excluded

    keyboard = [[
        InlineKeyboardButton(bot_strings.cancel_button, callback_data=f'cancel_exclude_{recipe_id}'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)


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
        # TODO allergy button
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    if query:
        query.message.delete()


def show_favorite_recipes_list(update: Update, context: CallbackContext):
    """Fetch saved recipes from DB and show them to user as buttons.
    """
    query = update.callback_query
    query.answer()
    # TODO: Break up into pages, 5 per page.

    try:
        favorite_recipes = Recipe.objects.filter(favorited_by__user_id=update.effective_user.id)
    except django.db.Error:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    if favorite_recipes:
        message_text = bot_strings.favorite_recipes
    else:
        message_text = bot_strings.favorite_recipes_none

    keyboard = []
    for recipe in favorite_recipes:
        keyboard.append([InlineKeyboardButton(recipe.title, callback_data=f'show_favorite_{recipe.id}')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_account')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    if query:
        query.message.delete()


def show_favorite_recipe(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    recipe_id = query.data.removeprefix('show_favorite_')
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except django.db.Error:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    message_text = format_recipe_message(recipe)

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.remove_from_favorites_button,
                                 callback_data=f'cancel_favorite_{recipe.id}'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button,
                                 callback_data=f'back_to_favorites'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    recipe_image = recipe.image or 'https://semantic-ui.com/images/wireframe/image.png'
    update.effective_chat.send_photo(recipe_image, caption=message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


def show_excluded_recipes_list(update: Update, context: CallbackContext):
    """Fetch excluded recipes from DB and show them to user as buttons.
        """
    query = update.callback_query
    query.answer()
    # TODO: Break up into pages, 5 per page.

    try:
        excluded_recipes = Recipe.objects.filter(excluded_by__user_id=update.effective_user.id)
    except django.db.Error:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    if excluded_recipes:
        message_text = bot_strings.excluded_recipes
    else:
        message_text = bot_strings.excluded_recipes_none

    keyboard = []
    for recipe in excluded_recipes:
        keyboard.append([InlineKeyboardButton(recipe.title, callback_data=f'show_excluded_{recipe.id}')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_account')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    if query:
        query.message.delete()


def show_excluded_recipe(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    recipe_id = query.data.removeprefix('show_excluded_')
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except django.db.Error:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    message_text = format_recipe_message(recipe)

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.remove_from_excluded_button,
                                 callback_data=f'cancel_exclude_{recipe.id}'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button,
                                 callback_data=f'back_to_excluded'),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    recipe_image = recipe.image or 'https://semantic-ui.com/images/wireframe/image.png'
    update.effective_chat.send_photo(recipe_image, caption=message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


def remove_recipe_from_favorites(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    recipe_id = query.data.removeprefix('cancel_favorite_')

    recipe = Recipe.objects.get(id=recipe_id)
    customer = Customer.objects.get(user_id=update.effective_user.id)
    customer.favorite_recipes.remove(recipe)

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.back_to_favorites_button,
                                 callback_data=f'back_to_favorites'),
        ],
        [
            InlineKeyboardButton(bot_strings.main_menu_button,
                                 callback_data=f'main_menu'),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = bot_strings.removed_from_favorites
    update.effective_user.send_message(message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


def remove_recipe_from_excluded(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    recipe_id = query.data.removeprefix('cancel_exclude_')

    recipe = Recipe.objects.get(id=recipe_id)
    customer = Customer.objects.get(user_id=update.effective_user.id)
    customer.excluded_recipes.remove(recipe)

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.back_to_excluded_button,
                                 callback_data=f'back_to_excluded'),
        ],
        [
            InlineKeyboardButton(bot_strings.main_menu_button,
                                 callback_data=f'main_menu'),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = bot_strings.removed_from_excluded
    update.effective_user.send_message(message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


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
                CallbackQueryHandler(request_name, pattern=r'^back_to_name$|^register$')
            ],
            states={
                AWAIT_REGISTRATION: [CallbackQueryHandler(request_name, pattern=r'^register$')],
                AWAIT_NAME: [CallbackQueryHandler(request_name, pattern=r'^back_to_name$'),
                             MessageHandler(Filters.text & ~Filters.command, request_confirm_name)],
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
        dispatcher.add_handler(CallbackQueryHandler(remove_recipe_from_favorites, pattern=r'^cancel_favorite_\d+$'))
        dispatcher.add_handler(CallbackQueryHandler(remove_recipe_from_excluded, pattern=r'^cancel_exclude_\d+$'))
        dispatcher.add_handler(CallbackQueryHandler(show_favorite_recipes_list, pattern=r'^favorite_recipes$'))
        dispatcher.add_handler(CallbackQueryHandler(show_excluded_recipes_list, pattern=r'^excluded_recipes$'))
        dispatcher.add_handler(CallbackQueryHandler(show_favorite_recipe, pattern=r'^show_favorite_\d+$'))
        dispatcher.add_handler(CallbackQueryHandler(show_excluded_recipe, pattern=r'^show_excluded_\d+$'))

        dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern=r'^main_menu$|^back_to_main$'))
        dispatcher.add_handler(CallbackQueryHandler(account_menu, pattern=r'^back_to_account$'))
        dispatcher.add_handler(CallbackQueryHandler(show_favorite_recipes_list, pattern=r'^back_to_favorites'))
        dispatcher.add_handler(CallbackQueryHandler(show_excluded_recipes_list, pattern=r'^back_to_excluded'))

        dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        dispatcher.add_handler(CallbackQueryHandler(test_payment, pattern=r'^subscribe$'))
        dispatcher.add_handler(conversation_handler)

        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    Command().handle()
