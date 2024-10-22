from django.contrib import admin
from .models import Match, Set, GameTiebreak, Point
from django.apps import AppConfig
from django.contrib.contenttypes.management import create_contenttypes

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        # register the model with the content types framework
        create_contenttypes(self.get_model('MyModel'))

# Register your models here.
admin.site.register(Match)
admin.site.register(Set)
admin.site.register(GameTiebreak)
admin.site.register(Point)