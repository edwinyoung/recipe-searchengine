# encoding=utf8
import os
import time
import codecs
from math import log10

from django.conf import settings
from django.core.management.base import BaseCommand
from searchengine.models import Recipe, DirectionsIndex, StemScore


class Command(BaseCommand):
  help = 'Assigns tf.idf scores to each stem'

  def handle(self, *args, **options):

    # Just delete all the recipes for which we have no instructions
    # because it messes with the tf.idf scoring algorithm
    Recipe.objects.filter(directions__iexact='no directions found.').delete()
    Recipe.objects.filter(directions__isnull=True).delete()
    Recipe.objects.filter(directions__exact='').delete()

    # Only want to play around with recipes that I haven't yet calculated the score for
    stems = DirectionsIndex.objects.all().values_list('stem', flat=True).distinct()
    stems = [i for i in stems if i not in StemScore.objects.all().values_list('stem', flat=True)]

    logfile_name = os.path.join(settings.BASE_DIR, time.strftime('searchengine/data/%Y%m%d-%H%M%S-stem-scoring.log'))

    n = Recipe.objects.all().count()

    with codecs.open(logfile_name, 'w', 'utf-8') as logfile:
      for stem in stems:
        df = DirectionsIndex.objects.filter(stem__iexact=stem).values_list('recipe_id').distinct().count()
        idf = 0 if df <= 0 else log10(n / float(df))
        StemScore.objects.create(stem=stem, idf=idf)
        logfile.write(u'{0} {1}\n'.format(stem, idf))

