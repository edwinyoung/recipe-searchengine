# encoding=utf8
from django.core.management.base import BaseCommand

from searchengine.models import Ingredient, IngredientIndex


class Command(BaseCommand):
  help = ''

  def handle(self, *args, **options):
    ingredients = Ingredient.objects.all().distinct()

    if IngredientIndex.objects.all().count() > 0:
      IngredientIndex.objects.all().delete()

    ingredient_tokens = u' '.join([ingredient.search_name for ingredient in ingredients]).split()
    ingredient_tokens = list(set(ingredient_tokens))

    for ingredient in ingredients:
      search_values = ingredient.search_name.split()
      for token in search_values:
        if token in ingredient_tokens:
          IngredientIndex.objects.create(ingredient=ingredient, stem=token)
