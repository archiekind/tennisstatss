from django.shortcuts import render
from .models import Match, Set, GameTiebreak, Point
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib.contenttypes.models import ContentType

# Create your views here.
def homepage(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('matches'))
    else:
        return HttpResponseRedirect(reverse('login'))
    
def about(request):
    return render(request, 'interface/about.html')

class Matches(LoginRequiredMixin, ListView):
    model = Match
    def get_queryset(self):
        return Match.objects.filter(user=self.request.user)
    template_name = 'interface/matches.html'

def thismatch(request, pk):
    sets = Set.objects.filter(match=pk).order_by('set_number')
    matchtiebreaks = GameTiebreak.objects.filter(object_id=pk)
    match = Match.objects.get(id=pk)
    context = {
        'matchtiebreaks': matchtiebreaks,
        'sets': sets,
        'match': match,
    }
    return render(request, 'interface/thismatch.html', context)

def makematch(request):
    return render(request, 'interface/makematch.html')

def deletematch(request, pk):
    match = Match.objects.get(id=pk)
    match.delete()
    return HttpResponseRedirect(reverse('matches'))

def creatematch(request):
    player1 = request.POST.get('player1')
    player2 = request.POST.get('player2')
    user = request.user
    date = datetime.datetime.now()
    date = date.strftime("%x")
    match = Match(user = user, player1 = player1, player2 = player2, date=date)
    match.save()
    return HttpResponseRedirect(reverse('createsets', args=[match.pk]))

def createsets(request, pk):
    match = Match.objects.get(pk=pk)
    match.number_of_sets += 1
    set = Set(set_number=match.number_of_sets, player1_score=0, player2_score=0, match = get_object_or_404(Match, pk=pk), starting_server=match.player1)
    match.save()
    set.save()
    return HttpResponseRedirect(reverse('thisset', args=[set.pk]))

def thisset(request, pk):
    set = Set.objects.get(id=pk)
    match = Match.objects.get(id=set.match.id)
    games = GameTiebreak.objects.filter(content_type=ContentType.objects.get_for_model(set), object_id=set.id).order_by('game_number')
    context = {
        'set': set,
        'match': match,
        'games': games,
    }
    return render(request, 'interface/thisset.html', context)

def deleteset(request, pk):
    set = Set.objects.get(id=pk)
    set.delete()
    return HttpResponseRedirect(reverse('thismatch', args=[set.match.pk]))


def creategame(request, pk, type):
    if type == "mtiebreak":
        match = Match.objects.get(id=pk)
        game = GameTiebreak(type=type.capitalize(), player1_score='0', player2_score='0', object_id=pk, content_type=ContentType.objects.get_for_model(match), game_number=0, server=match.player1, match=match)
        game.save()
        return HttpResponseRedirect(reverse('thisgame', args=[game.pk]))
    else:
        set = Set.objects.get(id=pk)
        match = set.match
        server = None
        if set.number_of_games == 0:
            server = set.match.player1
        else:
            prev_game = GameTiebreak.objects.get(game_number=set.number_of_games, content_type=ContentType.objects.get_for_model(set), object_id=set.id)
            if prev_game.server == set.match.player1:
                server = set.match.player2
            else:
                server = set.match.player1
        game = GameTiebreak(type=type.capitalize(), player1_score='0', player2_score='0', object_id=pk, content_type=ContentType.objects.get_for_model(set), game_number=set.number_of_games+1, server=server, match=match)
        game.save()
        set.number_of_games = set.number_of_games + 1
        set.save()
        return HttpResponseRedirect(reverse('thisgame', args=[game.pk]))

#content_type=ContentType.objects.get_for_model(game), object_id=game.id

def thisgame(request, pk):
    gametiebreak = GameTiebreak.objects.get(id=pk)
    match = None
    if gametiebreak.type == "Mtiebreak":
        match = Match.objects.get(id=gametiebreak.object_id)
    else:
        set = Set.objects.get(id=gametiebreak.object_id)
        match = set.match
    points = Point.objects.filter(gametiebreak=gametiebreak).order_by('point_number')
    server = gametiebreak.server
    if gametiebreak.type != "game":
        if (gametiebreak.number_of_points % 4 == 0 or (gametiebreak.number_of_points+1) % 4 == 0):
            server = gametiebreak.server 
        elif match.player1 == server:
            server = match.player2
        else:
            server = match.player1
    context = {
        'points' : points,
        'game' : gametiebreak,
        'server': server,
        'match': match,
        'type': gametiebreak.type,
        }
    return render(request, 'interface/thisgame.html', context)

def deletegame(request, pk):
    game_in_question = GameTiebreak.objects.get(id=pk)
    set = Set.objects.get(id=game_in_question.object_id)
    if game_in_question.player1_score == 'game':
        set.player1_score = set.player1_score - 1
    elif game_in_question.player2_score == 'game':
        set.player2_score = set.player2_score - 1
    gameiq_number = game_in_question.game_number
    game_in_question.delete()
    games = GameTiebreak.objects.filter(content_type=ContentType.objects.get_for_model(set), object_id=set.id)
    for game in games:
        if game.game_number > gameiq_number:
            game.game_number = game.game_number - 1
            if game.server == set.match.player1:
                game.server = set.match.player2
            else:
                game.server = set.match.player1
            game.save()
    set.number_of_games = set.number_of_games - 1
    set.save()
    return HttpResponseRedirect(reverse('thisset', args=[set.pk]))

def createpoint(request, pk):
    gametiebreak = GameTiebreak.objects.get(id=pk)
    type = gametiebreak.type
    match = None
    if type == "Mtiebreak":
        match = Match.objects.get(id=gametiebreak.object_id)
    else:
        set = Set.objects.get(id=gametiebreak.object_id)
        match = set.match
    winner = request.POST.get('winner')
    gamescores = ['0', '15', '30', '40', 'ad', 'game']
    player1_score = gametiebreak.player1_score
    player2_score = gametiebreak.player2_score
    gametiebreak.number_of_points = gametiebreak.number_of_points + 1
    server = gametiebreak.server
    if type == 'Game':
        server = gametiebreak.server
    else:
        if (gametiebreak.number_of_points % 4 == 0 or (gametiebreak.number_of_points-1) % 4 == 0):
            server = gametiebreak.server 
        elif match.player1 == server:
            server = match.player2
        else:
            server = match.player1
    serve1 = request.POST.get('serve1')
    serve2 = request.POST.get('serve2')
    retrn = request.POST.get('retrn')
    winmethod = request.POST.get('winmethod')
    side = request.POST.get('side')
    ballwent = request.POST.get('ballwent')
    playerwinner = match.player1
    if (serve1 == 'net' or serve1 == 'out') and (serve2 == 'net' or serve2 == 'out'):
        if server == match.player1:
            winner = 'player2'
            playerwinner = match.player2
        else:
            winner = 'player1'
            playerwinner = match.player1
    elif retrn == 'net' or retrn == 'out':
        if server == match.player1:
            winner = 'player1'
            playerwinner = match.player1
        else:
            winner = 'player2'
            playerwinner = match.player2

    invalid = False

    if serve1 != 'in' and serve2 == None:
        invalid = True

    if (serve1 == 'in' or serve2 == 'in') and retrn == None:
        invalid = True
 
    if serve1 == 'in' and serve2 == 'in':
        invalid = True

    if serve1 == 'in' and serve2 != None:
        invalid = True

    if (server == playerwinner) and (serve1 == 'net' or serve1 == 'out') and (serve2 == 'net' or serve2 == 'out'):
        invalid = True

    if (winmethod == 'for') and  (ballwent == 'net' or ballwent == 'out'):
        invalid = True
    
    if (winmethod == 'unf') and (ballwent == 'line' or ballwent == 'cross-court'):
        invalid = True

    if ((serve1 == 'net' or serve1 == 'out') and (serve2 == 'net' or serve2 == 'out')) and (retrn != None or playerwinner == server or winmethod != None or side != None or ballwent != None):
        invalid = True
    
    if (retrn == 'net' or retrn == 'out') and (serve2 == 'net' or serve2 == 'out' or playerwinner != server or winmethod != None or side != None or ballwent != None):
        invalid = True

    if (serve1 == 'in' or serve2 == 'in') and retrn == 'in':
        if winmethod == None or side == None or ballwent == None:
            invalid = True

    if invalid == True:
        return HttpResponseRedirect(reverse('invalid', args=[gametiebreak.pk]))
    finished = False
    if type == "Game":
        set = Set.objects.get(id=gametiebreak.object_id)
        if player1_score == 'game' or player2_score == 'game':
            pass
        elif winner == 'player1':
            if player2_score == 'ad':
                gametiebreak.player2_score = '40'
            elif player1_score == '40' and (player2_score != '40' and player2_score != 'ad'):
                gametiebreak.player1_score = 'game'
                set.player1_score = set.player1_score + 1
            elif player1_score == '40' and player2_score == '40':
                gametiebreak.player1_score = 'ad'
            elif player1_score == 'ad':
                gametiebreak.player1_score = 'game'
                set.player1_score = set.player1_score + 1
            else:
                for i in range(len(gamescores) - 2):
                    if player1_score == gamescores[i]:
                        gametiebreak.player1_score = gamescores[i+1]
        else:
            if player1_score == 'ad':
                gametiebreak.player1_score = '40'
            elif player2_score == '40' and (player1_score != '40' and player1_score != 'ad'):
                gametiebreak.player2_score = 'game'
                set.player2_score = set.player2_score + 1
            elif player1_score == '40' and player2_score == '40':
                gametiebreak.player2_score = 'ad'
            elif player2_score == 'ad':
                gametiebreak.player2_score = 'game'
                set.player2_score = set.player2_score + 1
            else:
                for i in range(len(gamescores) - 2):
                    if player2_score == gamescores[i]:
                        gametiebreak.player2_score = gamescores[i+1]
        set.save()
    elif type == "Tiebreak":
        set = Set.objects.get(id=gametiebreak.object_id)
        p1_score = int(gametiebreak.player1_score)
        p2_score = int(gametiebreak.player2_score)
        if (p1_score > 5 and winner == 'player1') or (p2_score > 5 and winner == 'player2'):
            if (winner == 'player1') and (p1_score > p2_score):
                gametiebreak.player1_score = str(p1_score + 1)
                set.player1_score += 1
                finished = True
            elif (winner == 'player2') and (p2_score > p1_score):
                gametiebreak.player2_score = str(p2_score + 1)
                set.player2_score += 1
                finished = True
            elif winner == 'player1':
                gametiebreak.player1_score = str(p1_score + 1)
            else:
                gametiebreak.player2_score = str(p2_score + 1)
        elif winner == 'player1':
            gametiebreak.player1_score = str(p1_score + 1)
        else:
            gametiebreak.player2_score = str(p2_score + 1)
        set.save()
    else:
        p1_score = int(gametiebreak.player1_score)
        p2_score = int(gametiebreak.player2_score)
        if (p1_score > 8 and winner == 'player1') or (p2_score > 8 and winner == 'player2'):
            if (winner == 'player1') and (p1_score > p2_score):
                gametiebreak.player1_score = str(p1_score + 1)
                finished = True
            elif (winner == 'player2') and (p2_score > p1_score):
                gametiebreak.player2_score = str(p2_score + 1)
                finished = True
            elif winner == 'player1':
                gametiebreak.player1_score = str(p1_score + 1)
            else:
                gametiebreak.player2_score = str(p2_score + 1)
        elif winner == 'player1':
            gametiebreak.player1_score = str(p1_score + 1)
        else:
            gametiebreak.player2_score = str(p2_score + 1)
        

    if serve2 == None:
        serve2 = "-"
    if retrn == None:
        retrn = '-'
    if winmethod == None:
        winmethod = '-'
    if side == None:
        side = '-'
    if ballwent == None:
        ballwent = '-'

    point = Point(
        gametiebreak=gametiebreak,
        winner=winner, 
        player1_score=gametiebreak.player1_score, 
        player2_score=gametiebreak.player2_score, 
        point_number=gametiebreak.number_of_points, 
        server=server, 
        serve1=serve1, 
        serve2=serve2,
        retrn=retrn,
        winmethod=winmethod,
        side=side,
        ballwent=ballwent,
        match=gametiebreak.match)
    point.save()
    gametiebreak.save()
    if (gametiebreak.player1_score == 'game' or gametiebreak.player2_score == 'game') or (type == "Tiebreak" and finished == True):
        return HttpResponseRedirect(reverse('thisset', args=[set.pk]))
    elif finished == True:
        return HttpResponseRedirect(reverse('thismatch', args=[match.pk]))
    return HttpResponseRedirect(reverse('thisgame', args=[gametiebreak.pk]))


def invalid(request, pk):
    game = GameTiebreak.objects.get(id=pk)
    context = {
        'game': game,
        }
    return render(request, 'interface/invalid.html', context=context)

def deletematchtiebreak(request, pk):
    matchtiebreak = GameTiebreak.objects.get(id=pk)
    match = Match.objects.get(id=matchtiebreak.object_id)
    matchtiebreak.delete()
    return HttpResponseRedirect(reverse('thismatch', args=[match.pk]))

def changeserver(request, pk):
    game = GameTiebreak.objects.get(id=pk)
    match = None
    if game.type == "Mtiebreak":
        match = Match.objects.get(id=game.object_id)
    else:
        set = Set.objects.get(id=game.object_id)
        match = set.match
    points = Point.objects.filter(gametiebreak=game)
    player1 = match.player1
    player2 = match.player2
    temp = game.player1_score
    game.player1_score = game.player2_score
    game.player2_score = temp
    if game.server == match.player1:
        game.server = match.player2
    else:
        game.server = match.player1
    for point in points:
        if point.server == player1:
            point.server = player2
        else:
            point.server = player1
        temp = point.player1_score
        point.player1_score = point.player2_score
        point.player2_score = temp
        point.save()
    game.save()
    return HttpResponseRedirect(reverse('thisgame', args=[game.pk]))

def changeallservers(request, pk):
    game_in_question = GameTiebreak.objects.get(id=pk)
    games = None
    match = None
    if game_in_question.type == "Mtiebreak":
        games = [game_in_question]
        match = Match.objects.get(id=game_in_question.object_id)
    else:
        set = Set.objects.get(id=game_in_question.object_id)
        games = GameTiebreak.objects.filter(object_id=set.id)
        match = set.match
    player1 = match.player1
    player2 = match.player2
    for game in games:
        points = Point.objects.filter(gametiebreak=game)
        temp = game.player1_score
        game.player1_score = game.player2_score
        game.player2_score = temp
        if game.server == match.player1:
            game.server = match.player2
        else:
            game.server = match.player1
        for point in points:
            if point.server == player1:
                point.server = player2
            else:
                point.server = player1
            temp = point.player1_score
            point.player1_score = point.player2_score
            point.player2_score = temp
            point.save()
        game.save()
    return HttpResponseRedirect(reverse('thisgame', args=[game_in_question.pk]))

def swappoints(request, pk):
    game = GameTiebreak.objects.get(id=pk)
    temp = game.player1_score
    game.player1_score = game.player2_score
    game.player2_score = temp
    points = Point.objects.filter(gametiebreak=game)
    for point in points:
        temp = point.player1_score
        point.player1_score = point.player2_score
        point.player2_score = temp
        point.save()
    game.save()
    return HttpResponseRedirect(reverse('thisgame', args=[game.pk]))

def viewstats(request, pk):
    match = Match.objects.get(id=pk)
    num_points = 0
    player1_w = 0
    player1_for = 0
    player1_unf = 0
    player2_w = 0
    player2_for = 0
    player2_unf = 0
    player1_numserves = 0
    player1_in = 0
    player1_net = 0
    player1_out = 0
    player2_numserves = 0
    player2_in = 0
    player2_net = 0
    player2_out = 0
    player1_numserves2 = 0
    player1_in2 = 0
    player1_net2 = 0
    player1_out2 = 0
    player2_numserves2 = 0
    player2_in2 = 0
    player2_net2 = 0
    player2_out2 = 0
    player1_rin = 0
    player1_rnet = 0
    player1_rout = 0
    player2_rin = 0
    player2_rnet = 0
    player2_rout = 0
    player1_fue = 0
    player1_bue = 0
    player2_fue = 0
    player2_bue = 0
    player1_nue = 0
    player1_oue = 0
    player2_nue = 0
    player2_oue = 0
    player1_ffe = 0
    player1_bfe = 0
    player2_ffe = 0
    player2_bfe = 0
    player1_cfe = 0
    player1_lfe = 0
    player2_cfe = 0
    player2_lfe = 0

    points = Point.objects.filter(match=match)
    for point in points:
        num_points += 1
        if point.winner == 'player1':
            player1_w += 1
            if point.winmethod == 'for':
                player2_for += 1
                if point.side == 'forehand':
                    player1_ffe += 1
                else:
                    player1_bfe += 1
                if point.ballwent == 'line':
                    player1_lfe += 1
                else:
                    player1_cfe += 1
            elif point.winmethod == 'unf':
                player2_unf += 1
                if point.side == 'forehand':
                    player2_fue += 1
                else:
                    player2_bue += 1
                if point.ballwent == 'net':
                    player2_nue += 1
                else:
                    player2_oue += 1
                
        else:
            player2_w += 1
            if point.winmethod == 'for':
                player1_for += 1
                if point.side == 'forehand':
                    player2_ffe += 1
                else:
                    player2_bfe += 1
                if point.ballwent == 'line':
                    player2_lfe += 1
                else:
                    player2_cfe += 1
            elif point.winmethod == 'unf':
                player1_unf += 1
                if point.side == 'forehand':
                    player1_fue += 1
                else:
                    player1_bue += 1
                if point.ballwent == 'net':
                    player1_nue += 1
                else:
                    player1_oue += 1
        if point.server == match.player1:
            if point.serve1 == 'in':
                player1_numserves += 1
                player1_in += 1
            elif point.serve1 == 'net':
                player1_numserves += 1
                player1_net +=1
            elif point.serve1 == 'out':
                player1_numserves += 1
                player1_out += 1
            
            if point.serve2 == 'in':
                player1_numserves2 += 1
                player1_in2 += 1
            elif point.serve2 == 'net':
                player1_numserves2 += 1
                player1_net2 += 1
            elif point.serve2 == 'out':
                player1_numserves2 += 1
                player1_out2 += 1

            if point.retrn == 'in':
                player2_rin += 1
            elif point.retrn == 'net':
                player2_rnet += 1
            elif point.retrn == 'out':
                player2_rout += 1

        else:
            if point.serve1 == 'in':
                player2_numserves += 1
                player2_in += 1
            elif point.serve1 == 'net':
                player2_numserves += 1
                player2_net += 1
            elif point.serve1 == 'out':
                player2_numserves += 1
                player2_out += 1
            
            if point.serve2 == 'in':
                player2_numserves2 += 1
                player2_in2 += 1
            elif point.serve2 == 'net':
                player2_numserves2 += 1
                player2_net2 += 1
            elif point.serve2 == 'out':
                player2_numserves2 += 1
                player2_out2 += 1

            if point.retrn == 'in':
                player1_rin += 1
            elif point.retrn == 'net':
                player1_rnet += 1
            elif point.retrn == 'out':
                player1_rout += 1

    player1_percentpointswon = (player1_w / num_points) * 100 if num_points != 0 else 0
    player1_percentforced = (player1_for / (player1_for + player1_unf)) * 100 if (player1_unf + player1_for) != 0 else 0
    player1_percentunforced = 100 - player1_percentforced if (player1_unf + player1_for) != 0 else 0
    player2_percentpointswon = (player2_w / num_points) * 100 if num_points != 0 else 0
    player2_percentforced = (player2_for / (player2_for + player2_unf)) * 100 if (player2_unf + player2_for) != 0 else 0
    player2_percentunforced = 100 - player2_percentforced if (player2_unf + player2_for) != 0 else 0

    player1_percentfirstserves = (player1_in/player1_numserves) * 100 if player1_numserves != 0 else 0
    player1_percentnet = ((player1_net / (player1_net + player1_out)) * 100) if (player1_net + player1_out) != 0 else 0
    player1_percentout = (player1_out / (player1_out + player1_net)) * 100 if (player1_net + player1_out) != 0 else 0
    player2_percentfirstserves = (player2_in/player2_numserves) * 100 if player2_numserves != 0 else 0
    player2_percentnet = (player2_net / (player2_net + player2_out)) * 100 if (player2_net + player2_out) != 0 else 0
    player2_percentout = (player2_out / (player2_out + player2_net)) * 100 if (player2_net + player2_out) != 0 else 0
    
    player1_percentsecondserves = (player1_in2/player1_numserves2) * 100 if player1_numserves2 != 0 else 0
    player1_percentnet2 = (player1_net2 / (player1_net2 + player1_out2)) * 100 if (player1_net2 + player1_out2) != 0 else 0
    player1_percentout2 = (player1_out2 / (player1_out2 + player1_net2)) * 100 if (player1_net2 + player1_out2) != 0 else 0
    player2_percentsecondserves = (player2_in2/player2_numserves2) * 100 if player2_numserves2 != 0 else 0
    player2_percentnet2 = (player2_net2 / (player2_net2 + player2_out2)) * 100 if (player2_net2 + player2_out2) != 0 else 0
    player2_percentout2 = (player2_out2 / (player2_out2 + player2_net2)) * 100 if (player2_net2 + player2_out2) != 0 else 0

    player1_percentrin = (player1_rin / (player1_rin + player1_rnet + player1_rout)) * 100 if (player1_rin + player1_rnet + player1_rout) != 0 else 0
    player1_percentrnet = (player1_rnet / (player1_rnet + player1_rout)) * 100 if (player1_rout + player1_rnet) != 0 else 0
    player1_percentrout = (player1_rout / (player1_rout + player1_rnet)) * 100 if (player1_rout + player1_rnet) != 0 else 0
    player2_percentrin = (player2_rin / (player2_rin + player2_rnet + player2_rout)) * 100 if (player2_rin + player2_rnet + player2_rout) != 0 else 0
    player2_percentrnet = (player2_rnet / (player2_rnet + player2_rout)) * 100 if (player2_rout + player2_rnet) != 0 else 0
    player2_percentrout = (player2_rout / (player2_rout + player2_rnet)) * 100 if (player2_rout + player2_rnet) != 0 else 0

    player1_percentfue = (player1_fue / (player1_fue + player1_bue)) * 100 if (player1_fue + player1_bue) != 0 else 0
    player1_percentbue = (player1_bue / (player1_fue + player1_bue)) * 100 if (player1_fue + player1_bue) != 0 else 0
    player2_percentfue = (player2_fue / (player2_fue + player2_bue)) * 100 if (player2_fue + player2_bue) != 0 else 0
    player2_percentbue = (player2_bue / (player2_fue + player2_bue)) * 100 if (player2_fue + player2_bue) != 0 else 0

    player1_percentoue = (player1_oue / (player1_oue + player1_nue)) * 100 if (player1_nue + player1_bue) != 0 else 0
    player1_percentnue = (player1_nue / (player1_oue + player1_nue)) * 100 if (player1_nue + player1_bue) != 0 else 0
    player2_percentoue = (player2_oue / (player2_oue + player2_nue)) * 100 if (player2_nue + player2_bue) != 0 else 0
    player2_percentnue = (player2_nue / (player2_oue + player2_nue)) * 100 if (player2_nue + player2_bue) != 0 else 0

    player1_percentffe = (player1_ffe / (player1_ffe + player1_bfe)) * 100 if (player1_ffe + player1_bfe) != 0 else 0
    player1_percentbfe = (player1_bfe / (player1_ffe + player1_bfe)) * 100 if (player1_ffe + player1_bfe) != 0 else 0
    player2_percentffe = (player2_ffe / (player2_ffe + player2_bfe)) * 100 if (player2_ffe + player2_bfe) != 0 else 0
    player2_percentbfe = (player2_bfe / (player2_ffe + player2_bfe)) * 100 if (player2_ffe + player2_bfe) != 0 else 0

    player1_percentlfe = (player1_lfe / (player1_lfe + player1_cfe)) * 100 if (player1_lfe + player1_cfe) != 0 else 0
    player1_percentcfe = (player1_cfe / (player1_lfe + player1_cfe)) * 100 if (player1_lfe + player1_cfe) != 0 else 0
    player2_percentlfe = (player2_lfe / (player2_lfe + player2_cfe)) * 100 if (player2_lfe + player2_cfe) != 0 else 0
    player2_percentcfe = (player2_cfe / (player2_lfe + player2_cfe)) * 100 if (player2_lfe + player2_cfe) != 0 else 0

    context = {
        'match': match,
        'player1_percentpointswon': round(player1_percentpointswon, 1),
        'player1_percentforced': round(player1_percentforced, 1),
        'player1_percentunforced': round(player1_percentunforced, 1),
        'player2_percentpointswon': round(player2_percentpointswon, 1),
        'player2_percentforced': round(player2_percentforced, 1),
        'player2_percentunforced': round(player2_percentunforced, 1),
        'player1_percentfirstserves': round(player1_percentfirstserves, 1),
        'player1_percentnet': round(player1_percentnet, 1),
        'player1_percentout': round(player1_percentout, 1),
        'player2_percentfirstserves': round(player2_percentfirstserves, 1),
        'player2_percentnet': round(player2_percentnet, 1),
        'player2_percentout': round(player2_percentout, 1),
        'player1_percentsecondserves': round(player1_percentsecondserves, 1),
        'player1_percentnet2': round(player1_percentnet2, 1),
        'player1_percentout2': round(player1_percentout2, 1),
        'player2_percentsecondserves': round(player2_percentsecondserves, 1),
        'player2_percentnet2': round(player2_percentnet2, 1),
        'player2_percentout2': round(player2_percentout2, 1),
        'player1_percentrin': round(player1_percentrin, 1),
        'player1_percentrnet': round(player1_percentrnet, 1),
        'player1_percentrout': round(player1_percentrout, 1),
        'player2_percentrin': round(player2_percentrin, 1),
        'player2_percentrnet': round(player2_percentrnet, 1),
        'player2_percentrout': round(player2_percentrout, 1),
        'player1_percentfue': round(player1_percentfue, 1),
        'player1_percentbue': round(player1_percentbue, 1),
        'player2_percentfue': round(player2_percentfue, 1),
        'player2_percentbue': round(player2_percentbue, 1),
        'player1_percentoue': round(player1_percentoue, 1),
        'player1_percentnue': round(player1_percentnue, 1),
        'player2_percentoue': round(player2_percentoue, 1),
        'player2_percentnue': round(player2_percentnue, 1),
        'player1_percentffe': round(player1_percentffe, 1),
        'player1_percentbfe': round(player1_percentbfe, 1),
        'player2_percentbfe': round(player2_percentbfe, 1),
        'player2_percentffe': round(player2_percentffe, 1),
        'player1_percentlfe': round(player1_percentlfe, 1),
        'player1_percentcfe': round(player1_percentcfe, 1),
        'player2_percentlfe': round(player2_percentlfe, 1),
        'player2_percentcfe': round(player2_percentcfe, 1),
    }
    return render(request, 'interface/viewstats.html', context=context)