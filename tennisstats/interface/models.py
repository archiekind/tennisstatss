from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

# Create your models here.
set_score_choices = (
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6'),
    (7, '7'),
)
"""
game_score_choices = (
    ('0', '0'),
    ('15', '15'),
    ('30', '30'),
    ('40', '40'),
    ('ad', 'ad'),
    ('game', 'game'),
)
"""
class Match(models.Model):
    id = models.UUIDField(
        primary_key = True,
        default = uuid.uuid4,
        editable = False,
    )
    user = models.ForeignKey(get_user_model(), null=True, on_delete=models.PROTECT)
    player1 = models.CharField(max_length = 20, default = 'Player1')
    player2 = models.CharField(max_length = 20, default = 'Player2')
    number_of_sets = models.IntegerField(default=0)
    date = models.CharField(max_length=100, default="none")

class Set(models.Model):
    id = models.UUIDField(
        primary_key = True,
        default = uuid.uuid4,
        editable = False,
    )
    set_number = models.IntegerField(choices = ((1, '1'), (2, '2'), (3, '3')), default = 1)
    number_of_games = models.IntegerField(default=0)
    player1_score = models.IntegerField(choices = set_score_choices, default = 0)
    player2_score = models.IntegerField(choices = set_score_choices, default = 0)
    match = models.ForeignKey(Match, null=True, on_delete=models.CASCADE)
    starting_server = models.CharField(max_length=30, default='none')

    def __int__(self):
        return self.set_number

point_winner_choices = (
    ('player_1', 'player 1'),
    ('player_2', 'player 2'),
)

class GameTiebreak(models.Model):
    id = models.UUIDField(
        primary_key = True,
        default = uuid.uuid4,
        editable = False,
    )
    object_id = models.UUIDField(
        primary_key=False,
        default=uuid.uuid4,
        editable=False,
    )
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, default=1)
    type = models.CharField(max_length=10, default="Game")
    setmatch = GenericForeignKey('content_type', 'object_id')
    game_number = models.IntegerField(default=1)
    player1_score = models.CharField(max_length=100, default='0')
    player2_score = models.CharField(max_length=100, default='0')
    number_of_points = models.IntegerField(default=0)
    server = models.CharField(max_length=30, default="none")

class Point(models.Model):
    id = models.UUIDField(
        primary_key = True,
        default = uuid.uuid4,
        editable = False,
    )
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True)
    winner = models.CharField(max_length=20, default='-')
    gametiebreak = models.ForeignKey(GameTiebreak, null=True, on_delete=models.CASCADE)
    point_number = models.IntegerField(default=1)
    player1_score = models.CharField(max_length = 100, default='0')
    player2_score = models.CharField(max_length = 100, default='0')
    server = models.CharField(max_length=30, default="none")
    serve1 = models.CharField(max_length=20, default='in')
    serve2 = models.CharField(max_length=20, default='in')
    retrn = models.CharField(max_length=20, default='-')
    winmethod = models.CharField(max_length=40, default='-')
    side = models.CharField(max_length=20, default='-')
    ballwent = models.CharField(max_length=20, default='-')
