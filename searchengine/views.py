# coding=utf-8
from math import ceil
from time import time
from random import randint
from operator import itemgetter

from django.http import HttpResponse
from django.template import loader

from searchengine.models import Recipe, Ingredient
from searchengine.utils.text.processor import TextProcessor


def index(request):
  template = loader.get_template('searchengine/index.html')
  context = {
    'home': True,
    'random_number': randint(1, 5),
  }

  return HttpResponse(template.render(context, request))

def search(request):
  start_time = time()

  processor = TextProcessor()

  querydict = request.GET

  # Check to make sure we have a query
  if 'q' not in querydict:
    return no_results(request)

  # Get the strings to search for ingredients
  query_ingredients = querydict['q']
  query_ingredients = map(unicode.strip, query_ingredients.split(u','))
  query_ingredients = [u' '.join([processor.stem(token) for token in name.split() if len(token) > 0]) for name in query_ingredients]
  query_ingredients = map(unicode.lower, query_ingredients)

  # Check to make sure the query has valid ingredient names
  if len(query_ingredients) < 1:
    return no_results(request)

  # Check to see if we should be excluding broths from our query
  ingredient_string = u','.join(query_ingredients)
  broth_types = [u'chicken', u'beef', u'pork']
  broth_keywords = [u'broth', u'base', u'soup', u'bouillon', u'stock']

  exclude_broths = len([i for i in broth_types if i in ingredient_string]) > 0
  if exclude_broths:
    exclude_broths = not len([i for i in broth_keywords if i in ingredient_string]) > 0

  # Retrieve ingredients that contain the search names
  ingredients = Ingredient.objects.filter(search_name__contains=query_ingredients[0])
  for i in range(1, len(query_ingredients)):
    ingredients |= Ingredient.objects.filter(search_name__contains=query_ingredients[i])
  if exclude_broths:
    for i in broth_keywords:
      ingredients = ingredients.exclude(search_name__contains=i)
  ingredients = ingredients.distinct().values_list('search_name', flat=True)

  # Check to make sure that we have ingredients that match the search terms before moving forward
  if ingredients.count() < 1:
    return no_results(request)

  # First pass on recipe retrieval does strict filtering
  recipes = Recipe.objects.filter(ingredients__search_name__contains=query_ingredients[0])
  for i in range(1, len(query_ingredients)):
    recipes &= Recipe.objects.filter(ingredients__search_name__contains=query_ingredients[i])
  if exclude_broths:
    for i in broth_keywords:
      recipes = recipes.exclude(ingredients__search_name__contains=i)
  recipes = recipes.distinct()
  full_match_recipes = [i for i in recipes]

  # Relax the search parameters if we get < 10 recipes for our search
  if recipes.count() < 10:
    search_relaxed = True
    recipes = Recipe.objects.filter(ingredients__search_name__contains=query_ingredients[0])
    for i in range(1, len(query_ingredients)):
      recipes |= Recipe.objects.filter(ingredients__search_name__contains=query_ingredients[i])
    if exclude_broths:
      for i in broth_keywords:
        recipes = recipes.exclude(ingredients__search_name__contains=i)
    recipes = recipes.distinct()
    recipes = [i for i in recipes]
  else:
    search_relaxed = False
    recipes = full_match_recipes

  if len(recipes) < 1:
    return no_results(request)

  scores = {}
  for recipe in recipes:
    recipe_ingredients = recipe.ingredients.all().values_list('search_name', flat=True)
    matches = [i for i in recipe_ingredients if i in ingredients]
    scores[recipe] = recipe.score + 0.5 * len(matches) * ((len(query_ingredients) + recipe_ingredients.count()) /
                                                          (len(query_ingredients) * recipe_ingredients.count()))
    # Super-score/rank recipes that have all ingredients if we had to relax our search
    if search_relaxed and recipe in full_match_recipes:
      scores[recipe] += 10

    # Score adjustments based on source
    # BigOven composes the majority of the collection and has a good deal of low-quality results
    # Epicurious, however, is only a small part of the collection and has high-quality results
    if 'bigoven' in recipe.source_url:
      scores[recipe] *= 0.9
    elif 'epicurious' in recipe.source_url:
      scores[recipe] *= 1.5

    # Penalize recipes which have overly long ingredient lists relative to the recipe directions
    # Significantly slows down our ranking system (increases processing time by >200%) but gives us more relevant results
    ingredients_len = len(u' '.join([i for i in recipe_ingredients]).split())
    directions_len = len(recipe.directions.split())
    if directions_len < ingredients_len * 2:
      scores[recipe] *= 0.1

  scores = sorted(scores.items(), key=itemgetter(1), reverse=True)
  recipes = [i[0] for i in scores]

  # Check to see what slice of 10 results we should be returning
  if 'pg' in querydict:
    try:
      pg = int(querydict['pg'])
      pg = pg if pg >= 1 else 1
    except ValueError:
      pg = 1
  else:
    pg = 1

  if (pg - 1) * 10 > len(recipes):
    pg = 1

  template = loader.get_template('searchengine/search.html')
  context = {
    'results': True,
    'query': querydict['q'].replace(u',', u', '),
    'recipes': recipes[10 * (pg - 1):10 * (pg - 1) + 10],
    'recipe_start': 10 * (pg - 1) + 1,
    'recipe_count': len(recipes),
    'time': "{:.3f}".format(time() - start_time),
    'current_page': pg,
    'base_url': request.path + '?q=' + querydict['q'],
  }
  context['recipe_end'] = context['recipe_start'] + len(recipes)

  total_pages = int(ceil(len(recipes) / 10.))
  context['only_page'] = total_pages == 1
  if total_pages >= 10:
    start_page = pg - 5 if pg - 5 >= 1 else 1
    end_page = start_page + 10
    context['pages'] = [i for i in range(start_page, end_page)]
  else:
    context['pages'] = [i for i in range(1, total_pages + 1)]

  return HttpResponse(template.render(context, request))


def no_results(request):
  empty_query = 'q' not in request.GET

  template = loader.get_template('searchengine/search.html')
  context = dict(
    results=False,
    empty_query=empty_query,
    random_number=randint(1, 5)
  )
  if not empty_query:
    context['query'] = request.GET['q']

  return HttpResponse(template.render(context, request))
