from django.http import HttpResponse
from django.template import loader

from searchengine.models import Recipe


def index(request):
  recipes = Recipe.objects.filter(score__isnull=False).order_by('-score')[:10]

  template = loader.get_template('searchengine/index.html')
  context = {
    'recipes': recipes
  }

  return HttpResponse(template.render(context, request))
