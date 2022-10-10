import requests
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from bot_db.models import Diet, Recipe


def get_recipes_links(url, pages):
    urls_list = []

    for page in range(1, pages):
        page_url = f"{url}/{page}"
        response = requests.get(page_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        links_soup = soup.find_all("div", class_="header")

        for link in links_soup:
            urls_list.append(link.find("a").get("href"))

    return urls_list


def get_recipe_details(urls_list, diet):
    recipes = []
    base_url = "https://www.iamcook.ru"

    for url in urls_list:
        response = requests.get(urljoin(base_url, url))
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("h1", itemprop="name").text

        try:
            description = soup.find("span", itemprop="description").text.replace(
                "\n", " "
            )
        except AttributeError:
            description = title
        base_image_url = "http://img.iamcook.ru/"
        image_url = urljoin(base_image_url, soup.find("img", class_="resultphoto").get("src"))

        ingredients = []
        ingredients_soup = soup.find_all("p", itemprop="recipeIngredient")

        for ingredient_entity in ingredients_soup:
            ingredients.append(ingredient_entity.text)

        recipe = {}
        recipe["title"] = title
        recipe["diet"] = diet
        recipe["description"] = description
        recipe["image_url"] = image_url[2:]
        recipe["ingredients"] = ingredients
        recipes.append(recipe)

        diet_entry = Diet.objects.get_or_create(title=diet)

        recipe = Recipe(
            title=title,
            diet=Diet.objects.get(title=diet),
            ingredients=ingredients,
            image=image_url,
            description=description,
        )
        recipe.save()

    with open("recipes.json", "a+") as file:
        json.dump(recipes, file, ensure_ascii=False, indent=4)


class Command(BaseCommand):

    def handle(self, *args, **options):
        pages = 3
        vegetarian_url = "https://www.iamcook.ru/event/everyday/everyday-vegetarian"
        non_gluten_url = "https://www.iamcook.ru/event/baking/gluten-free-baking"
        abstinence_url = "https://www.iamcook.ru/event/abstinence"
        everyday_url = "https://www.iamcook.ru/event/everyday"
        get_recipe_details(get_recipes_links(
            vegetarian_url, pages), diet="Вегетарианская")
        get_recipe_details(get_recipes_links(
            non_gluten_url, pages), diet="Безглютеновая")
        get_recipe_details(get_recipes_links(
            abstinence_url, pages), diet="Постная")
        get_recipe_details(get_recipes_links(
            everyday_url, pages), diet="На каждый день")


if __name__ == "__main__":
    Command().handle()
