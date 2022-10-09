import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json


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

        image_url = soup.find("img", class_="resultphoto").get("src")

        ingredients = {}
        ingredients_soup = soup.find_all("p", itemprop="recipeIngredient")

        for ingredient_entity in ingredients_soup:
            if " – " in ingredient_entity.text:
                ingredient_details = ingredient_entity.text.split(" – ")
            elif " - " in ingredient_entity.text:
                ingredient_details = ingredient_entity.text.split(" - ")
            else:
                ingredient_details = ingredient_entity.text.split(" — ")

            ingredient = ingredient_details[0]
            try:
                amount = ingredient_details[1]
            except IndexError:
                amount = ""

            ingredients[ingredient] = amount

        recipe = {}
        recipe["title"] = title
        recipe["diet"] = diet
        recipe["description"] = description
        recipe["image_url"] = image_url
        recipe["ingredients"] = ingredients
        recipes.append(recipe)
    with open("recipes.json", "a+") as file:
        json.dump(recipes, file, ensure_ascii=False, indent=4)


def main():
    pages = 3
    vegetarian_url = "https://www.iamcook.ru/event/everyday/everyday-vegetarian"
    non_gluten_url = "https://www.iamcook.ru/event/baking/gluten-free-baking"
    abstinence_url = "https://www.iamcook.ru/event/abstinence"
    everyday_url = "https://www.iamcook.ru/event/everyday"
    get_recipe_details(get_recipes_links(vegetarian_url, pages), diet="Вегетарианская")
    get_recipe_details(get_recipes_links(non_gluten_url, pages), diet="Безглютеновая")
    get_recipe_details(get_recipes_links(abstinence_url, pages), diet="Постная")
    get_recipe_details(get_recipes_links(everyday_url, pages), diet="На каждый день")


if __name__ == "__main__":
    main()
