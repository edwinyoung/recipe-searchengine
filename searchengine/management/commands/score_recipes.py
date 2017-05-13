# encoding=utf8
from math import log10

from django.core.management.base import BaseCommand
from searchengine.models import Recipe, DirectionsIndex, StemScore


class Command(BaseCommand):
  help = 'Assigns tf.idf scores to each recipe'

  def handle(self, *args, **options):

    # Just delete all the recipes for which we have no instructions
    # because it messes with the tf.idf scoring algorithm
    Recipe.objects.filter(directions__iexact='no directions found.').delete()
    Recipe.objects.filter(directions__isnull=True).delete()
    Recipe.objects.filter(directions__exact='').delete()

    # Only want to play around with recipes that I haven't yet calculated the score for
    recipes = Recipe.objects.filter(score__isnull=True).distinct()

    n = Recipe.objects.all().count()

    for recipe in recipes:
      terms = DirectionsIndex.objects.filter(recipe=recipe).values_list('stem', flat=True).distinct()
      for term in terms:
        tf = DirectionsIndex.objects.filter(recipe=recipe).filter(stem__iexact=term).count()
        tf = 1 + log10(tf)

        if StemScore.objects.filter(stem__iexact=term).count() > 0:
          idf = StemScore.objects.get(pk=term).idf
        else:
          df = DirectionsIndex.objects.filter(stem__iexact=term).values_list('recipe_id').distinct().count()
          idf = 0 if df <= 0 else log10(n / float(df))
          StemScore.objects.create(stem=term, idf=idf)

        if recipe.score is not None or recipe.score <= 0:
          recipe.score = tf * idf
        else:
          recipe.score += tf * idf

      recipe.save()
