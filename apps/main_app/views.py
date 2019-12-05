from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from . import dictionary
from apps.main_app.models import *
import bcrypt
import requests
import urllib
import json
from datetime import datetime
import sched, time
import time


# An api key is emailed to you when you sign up to a plan
api_key = '44de120d6df871b1293cd91ffb8e511a'


# First get a list of in-season sports
sports_response = requests.get('https://api.the-odds-api.com/v3/sports', params={
    'api_key': api_key
})

sports_json = json.loads(sports_response.text)

sport_key = 'americanfootball_nfl'

upcoming_odds = requests.get('https://api.the-odds-api.com/v3/odds', params={
    'api_key': api_key,
    'sport': 'upcoming',
    'region': 'us',
    'mkt': 'spreads'
})

upcoming_odds_json = json.loads(upcoming_odds.text)

nfl_scores_url='http://www.nfl.com/liveupdate/scores/scores.json'
nfl_scores_response = (urllib.request.urlopen(nfl_scores_url))
nfl_scores_data = json.load(nfl_scores_response)
for gameid, key in nfl_scores_data.items():
    game = Game.objects.filter(nfl_game_id=gameid)
    if not game:
        Game.objects.create(date=datetime(year=int(gameid[0:4]),month=int(gameid[4:6]),day=int(gameid[6:8])), nfl_date_id=gameid, nfl_game_id=gameid, home_team_abbr=key['home']['abbr'], away_team_abbr=key['away']['abbr'],home_team=dictionary.abbr_to_team[key['home']['abbr']],away_team=dictionary.abbr_to_team[key['away']['abbr']],home_score_Q1=key['home']['score']['1'],home_score_Q2=key['home']['score']['2'],home_score_Q3=key['home']['score']['3'],home_score_Q4=key['home']['score']['4'],home_score_Q5=key['home']['score']['5'],away_score_Q1=key['away']['score']['1'],away_score_Q2=key['away']['score']['2'],away_score_Q3=key['away']['score']['3'],away_score_Q4=key['away']['score']['4'],away_score_Q5=key['away']['score']['5'],final_home_score=key['home']['score']['T'],final_away_score=key['away']['score']['T'],tv_channel=key['media']['tv'],current_quarter=key['qtr'])
    if game:
        game.update(home_score_Q1=key['home']['score']['1'],home_score_Q2=key['home']['score']['2'],home_score_Q3=key['home']['score']['3'],home_score_Q4=key['home']['score']['4'],home_score_Q5=key['home']['score']['5'],away_score_Q1=key['away']['score']['1'],away_score_Q2=key['away']['score']['2'],away_score_Q3=key['away']['score']['3'],away_score_Q4=key['away']['score']['4'],away_score_Q5=key['away']['score']['5'],final_home_score=key['home']['score']['T'],final_away_score=key['away']['score']['T'],tv_channel=key['media']['tv'],current_quarter=key['qtr'])

def update_parlay_lines(odds):
    myweek=ParlayWeek.objects.first()
    weekfilter= ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),sunday__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
    current_week=weekfilter.first()
    current_lines=ParlayLine.objects.filter(week=current_week,game_id__isnull=True)
    for game in odds['data']:
        if str(datetime.fromtimestamp(game['commence_time']-14400).strftime('%Y-%m-%d')) == str(current_week.sunday):
            if ParlayLine.objects.filter(commence_time=game['commence_time'],home_team=game['home_team']).first():
                pass
            if not ParlayLine.objects.filter(commence_time=game['commence_time'],home_team=game['home_team']).first():
                if game['home_team']==game['teams'][0]:
                    ParlayLine.objects.create(commence_time=game['commence_time'],date=datetime.fromtimestamp(game['commence_time'] -14400).strftime('%Y-%m-%d'),home_team=game['home_team'],away_team=game['teams'][1],home_points=game['sites'][0]['odds']['spreads']['points'][0],away_points=game['sites'][0]['odds']['spreads']['points'][1],week=current_week)
                if game['home_team']==game['teams'][1]:
                    ParlayLine.objects.create(commence_time=game['commence_time'],date=datetime.fromtimestamp(game['commence_time'] -14400).strftime('%Y-%m-%d'),home_team=game['home_team'],away_team=game['teams'][0],home_points=game['sites'][0]['odds']['spreads']['points'][1],away_points=game['sites'][0]['odds']['spreads']['points'][0],week=current_week)
    for line in current_lines:
        game = Game.objects.filter(date=datetime.fromtimestamp(line.commence_time-14400).strftime('%Y-%m-%d'),home_team=line.home_team,away_team=line.away_team)
        if game:
            game=game.first()
            line.game=game
            line.save()

def check_parlay_lines():
    empty_lines = ParlayLine.objects.filter(result__isnull=True)
    for line in empty_lines.filter(game__isnull=False):
        if line.game.final == True:
            if line.game.final_home_score+home_points>line.game.final_away_score:
                line.result='home'
                line.save()
            if line.game.final_home_score+home_points<line.game.final_away_score:
                line.result='away'
                line.save()
            if line.game.final_home_score+home_points==line.game.final_away_score:
                line.result='push'
                line.save()

def calculate_parlay_wins():
    weekfilter= ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),sunday__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
    current_week=weekfilter.first()
    p_lines = current_week.lines.all()
    result={}
    for line in p_lines:
        result[line.id]=line.result
    current_week.winning_result=json.dumps(result)
    current_week.save()

def check_parlay_bets():
    weekfilter=ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),sunday__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
    current_week=weekfilter.first()
    parlay_bets = ParlayBet.objects.filter(week=current_week)
    json_acceptable_week=current_week.winning_result.replace("'", "\"")
    week_dict=json.loads(json_acceptable_week)
    for bet in parlay_bets:
        json_acceptable_bet=bet.parlay.replace("'", "\"")
        bet_dict=json.loads(json_acceptable_bet)
        left=0
        wins=0
        losses=0
        pushes=0
        for key in bet_dict:
            if not week_dict[key]:
                left+=1
            if week_dict[key]:
                if week_dict=='push':
                    pushes+=1
                elif bet_dict[key]==week_dict[key]:
                    wins+=1
                else:
                    losses+=1
        bet.left=left
        bet.pushes=pushes
        bet.wins=wins
        bet.losses=losses
        bet.save()

def close_bets():
    open_bets= ParlayBet.objects.filter(closed=False)
    for bet in open_bets:
        if bet.left==0:
            if bet.losses==0:
                bet.perfect==True
            bet.closed=True


def refresh_scores():
    nfl_scores_url='http://www.nfl.com/liveupdate/scores/scores.json'
    nfl_scores_response = (urllib.request.urlopen(nfl_scores_url))
    nfl_scores_data = json.load(nfl_scores_response)
    for gameid, key in nfl_scores_data.items():
        game = Game.objects.filter(nfl_game_id=gameid)
        if not game:
            Game.objects.create(date=datetime(year=int(gameid[0:4]),month=int(gameid[4:6]),day=int(gameid[6:8])), nfl_date_id=gameid, nfl_game_id=gameid, home_team_abbr=key['home']['abbr'], away_team_abbr=key['away']['abbr'],home_team=dictionary.abbr_to_team[key['home']['abbr']],away_team=dictionary.abbr_to_team[key['away']['abbr']],home_score_Q1=key['home']['score']['1'],home_score_Q2=key['home']['score']['2'],home_score_Q3=key['home']['score']['3'],home_score_Q4=key['home']['score']['4'],home_score_Q5=key['home']['score']['5'],away_score_Q1=key['away']['score']['1'],away_score_Q2=key['away']['score']['2'],away_score_Q3=key['away']['score']['3'],away_score_Q4=key['away']['score']['4'],away_score_Q5=key['away']['score']['5'],final_home_score=key['home']['score']['T'],final_away_score=key['away']['score']['T'],tv_channel=key['media']['tv'],current_quarter=key['qtr'])
        if not game.first().final:
            game.update(date=datetime(year=int(gameid[0:4]),month=int(gameid[4:6]),day=int(gameid[6:8])), nfl_date_id=gameid, nfl_game_id=gameid, home_team_abbr=key['home']['abbr'], away_team_abbr=key['away']['abbr'],home_team=dictionary.abbr_to_team[key['home']['abbr']],away_team=dictionary.abbr_to_team[key['away']['abbr']],home_score_Q1=key['home']['score']['1'],home_score_Q2=key['home']['score']['2'],home_score_Q3=key['home']['score']['3'],home_score_Q4=key['home']['score']['4'],home_score_Q5=key['home']['score']['5'],away_score_Q1=key['away']['score']['1'],away_score_Q2=key['away']['score']['2'],away_score_Q3=key['away']['score']['3'],away_score_Q4=key['away']['score']['4'],away_score_Q5=key['away']['score']['5'],final_home_score=key['home']['score']['T'],final_away_score=key['away']['score']['T'],tv_channel=key['media']['tv'],current_quarter=key['qtr'])
    return



def check_final():
    games = Game.objects.filter(final=0)
    for game in games:
        if game.final != True:
            if game.current_quarter=='Final':
                bets = game.bets.all()
                for bet in bets:
                    if bet.paid:
                        pass
                    else:
                        if bet.winning_team == bet.game.home_team:
                            with_spread=bet.points_spread+bet.game.final_home_score
                            if with_spread>bet.game.final_away_score:
                                bet.payout=bet.wager*2
                                bet.result='win'
                                bet.user.points+=bet.payout
                                bet.user.save()
                                bet.paid=1
                                bet.save()
                            if with_spread==bet.game.final_away_score:
                                bet.payout=bet.wager
                                bet.result='push'
                                bet.user.points+=bet.payout
                                bet.user.save()
                                bet.paid=1
                                bet.save()
                            if with_spread<bet.game.final_away_score:
                                bet.payout=0
                                bet.result='lose'
                                bet.paid=1
                                bet.save()
                        if bet.winning_team == bet.game.away_team:
                            with_spread=bet.points_spread+bet.game.final_away_score
                            if with_spread>bet.game.final_home_score:
                                bet.payout=bet.wager*2
                                bet.result='win'
                                bet.user.points+=bet.payout
                                bet.user.save()
                                bet.paid=1
                                bet.save()
                            if with_spread==bet.game.final_home_score:
                                bet.payout=bet.wager
                                bet.result='push'
                                bet.user.points+=bet.payout
                                bet.user.save()
                                bet.paid=1
                                bet.save()
                            if with_spread<bet.game.final_home_score:
                                bet.payout=0
                                bet.result='lose'
                                bet.paid=1
                                bet.save()
                game.final = True
                game.save()



def convert_timestamp_to_date(timestamp):
    import time
    return datetime.fromtimestamp(timestamp-14400).strftime('%Y-%m-%d')



nfl_odds = requests.get('https://api.the-odds-api.com/v3/odds', params={
    'api_key': api_key,
    'sport': 'americanfootball_nfl',
    'region': 'us',
    'mkt': 'spreads'
})

nfl_odds_json = json.loads(nfl_odds.text)

update_parlay_lines(nfl_odds_json)
check_parlay_lines()
calculate_parlay_wins()
check_parlay_bets()
close_bets()



# Create your views here.

def sportodds(request):
    if request.method == 'POST':
        if request.POST['formtype'] == 'register':
            errors = User.objects.register_validator(request.POST)
            if len(errors)>0:
                for key, value in errors.items():
                    messages.error(request,value,extra_tags=key)
                return redirect('/register')
            password=request.POST['password']
            pw_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            user = User.objects.create(name=request.POST['username'],email=request.POST['email'],password=pw_hash)
            request.session['userid'] = user.id
            return redirect('/index')
        if request.POST['formtype'] == 'login':
            errors = User.objects.login_validator(request.POST, request.session)
            if len(errors)>0:
                for key, value in errors.items():
                    messages.error(request,value,extra_tags=key)
                return redirect('/')
            else:
                user = User.objects.get(name=request.POST['username'])
                request.session['userid']=user.id
                return redirect('/index')
    if not 'userid' in request.session:
        return redirect('/')
    user=User.objects.get(id=request.session['userid'])
    unassigned_bets = Bet.objects.filter(game_id__isnull=True).values()
    for bet in unassigned_bets:
        game = (Game.objects.filter(date=bet['date']).filter(home_team=bet['home_team']).filter(away_team=bet['away_team']))
        if not game:
            pass
        else:
            checked_bet=Bet.objects.get(id=bet['id'])
            checked_bet.game=game.first()
            checked_bet.save()
    context = {
        'time': {'now':time.time()},
        'games': nfl_odds_json['data'],
        'user': user
    }
    return render(request, "main_app/newindex.html", context)

def pick(request):
    if request.method=='POST':
        for game in nfl_odds_json['data']:
            pass
    return redirect('/odds/americanfootball_nfl')

def login(request):
    if 'userid' in request.session:
        return redirect('/index')
    return render(request, "main_app/login.html")

def register(request):
    if 'userid' in request.session:
        return redirect('/index')
    return render(request, "main_app/register.html")

def scores(request):
    refresh_scores()
    check_final()
    user = User.objects.get(id=request.session['userid'])
    games = Game.objects.order_by("-date").all()
    context = {
        'games': games,
        'user': user
    }
    return render(request, "main_app/scores.html", context)

def score(request,gameid):
    if not 'userid' in request.session:
        return redirect('/')
    user = User.objects.get(id=request.session['userid'])
    refresh_scores()
    games = Game.objects.filter(nfl_game_id=gameid)
    stats_url=f'http://www.nfl.com/liveupdate/game-center/{gameid}/{gameid}_gtd.json'
    stats_response = (urllib.request.urlopen(stats_url))
    stats_data = json.load(stats_response)
    plays=stats_data[gameid]['drives']
    scoringplays=scoring_plays(plays)
    hpl={}
    hrushl={}
    hrecl={}
    hp = stats_data[gameid]['home']['stats']['passing']
    hrec = stats_data[gameid]['home']['stats']['receiving']
    hrush = stats_data[gameid]['home']['stats']['rushing']
    if hp:
        hpl = hp[leader(hp)]
    if hrec:
        hrecl = hrec[leader(hrec)]
    if hrush:
        hrushl = hrush[leader(hrush)]   
    apl={}
    arushl={}
    arecl={}
    ap = stats_data[gameid]['away']['stats']['passing']
    arec = stats_data[gameid]['away']['stats']['receiving']
    arush = stats_data[gameid]['away']['stats']['rushing']
    if ap:
        apl = ap[leader(ap)]
    if arec:
        arecl = arec[leader(arec)]
    if arush:
        arushl = arush[leader(arush)]  
    context={
        'games': games,
        'stats': stats_data,
        'hpl': hpl,
        'hrecl': hrecl,
        'hrushl': hrushl,
        'apl': apl,
        'arecl': arecl,
        'arushl': arushl,
        'user':user
    }
    return render(request, "main_app/game.html", context)

def process_bet(request):
    if not 'userid' in request.session:
        return redirect('/')
    if request.method=='POST':
        for game in nfl_odds_json['data']:
            if int(request.POST['commence_time']) == game['commence_time']:
                if len(game['sites'])>0:
                    if request.POST['site'] == game['sites'][0]['site_key']:
                        if request.POST['hometeam'] == game['home_team']:
                            if request.POST['awayteam'] in game['teams']:
                                errors = Bet.objects.validator(game, request.POST, User.objects.get(id=request.session['userid']))
                                if len(errors)>0:
                                    for key, value in errors.items():
                                        messages.error(request,value,extra_tags="failed")
                                    json_data = json.dumps({"wager":request.POST['wager'],"bet":"invalid","message":"Please place a valid bet"})
                                    return HttpResponse(json_data)                                    
                                if request.POST['winningteam'] == str(game['teams'][0]):
                                    points_spread=game['sites'][0]['odds']['spreads']['points'][0]
                                if request.POST['winningteam'] == str(game['teams'][1]):
                                    points_spread=game['sites'][0]['odds']['spreads']['points'][1]
        errors = {}
        user = User.objects.get(id=request.session['userid'])
        date = convert_timestamp_to_date(int(request.POST['commence_time'])-14400)
        Bet.objects.create(user=user,date=date,home_team=request.POST['hometeam'],away_team=request.POST['awayteam'],winning_team=request.POST['winningteam'],points_spread=points_spread,wager=request.POST['wager'])
        user.points = user.points-int(request.POST['wager'])
        user.save()
        wager = request.POST['wager']
        winningteam = request.POST['winningteam']
        messages.success(request,f"Successfully wagered {wager} coin(s) on the {winningteam}!",extra_tags="bet")
        json_data = json.dumps({"wager":request.POST['wager'],"bet":"valid","message":f"Successfully wagered {wager} coins on the {winningteam}!"})
    return HttpResponse(json_data)

def logout(request):
    request.session.clear()
    return redirect('/')

def processlogin(request):
    if request.method == 'POST':
        if request.POST['formtype'] == 'register':
            errors = User.objects.register_validator(request.POST)
            if len(errors)>0:
                failures ={}
                for key, value in errors.items():
                    failures.update({key:value})
                    failures.update({'v':'invalid'})
                    json_data = json.dumps(failures)
                    messages.error(request,value,extra_tags=key)
                return HttpResponse(json_data)
            password=request.POST['password']
            pw_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            user = User.objects.create(name=request.POST['username'],email=request.POST['email'],password=pw_hash)
            request.session['userid'] = user.id
            success={}
            success.update({'v':'valid'})
            json_data = json.dumps(success)
            return HttpResponse(json_data)
        if request.POST['formtype'] == 'login':
            errors = User.objects.login_validator(request.POST, request.session)
            if len(errors)>0:
                for key, value in errors.items():
                    messages.error(request,value,extra_tags=key)
                return HttpResponse('failed')
            else:
                user = User.objects.get(name=request.POST['username'])
                request.session['userid']=user.id
                return redirect('/index')

def leader(stats):
    max=0
    leader=0
    for key in stats:
        for value in stats[key]:
            if value=='yds':
                if (stats[key][value]) > max:
                    max=stats[key][value]
                    leader=key
    return leader

def scoring_plays(plays):
    for key in plays:
        print(key)

def user(request):
    user=User.objects.get(id=request.session['userid'])
    bets=Bet.objects.filter(user=request.session['userid'])
    active_bets=bets.filter(result__isnull=True)
    inactive_bets=bets.exclude(result__isnull=True)
    parlays=ParlayBet.objects.filter(user_id=request.session['userid'])
    active_parlays=parlays.filter(closed=0)
    active_list=[]
    for parlay in active_parlays:
        json_acceptable_parlay=parlay.parlay.replace("'", "\"")
        parlay_dict={}
        parlay_dict['games']=json.loads(json_acceptable_parlay)
        parlay_dict['wins']=parlay.wins
        parlay_dict['losses']=parlay.losses
        parlay_dict['left']=parlay.left
        if parlay.wins+parlay.losses>0:
            parlay_dict['percent']=parlay.wins/(parlay.losses+parlay.wins)
        else:
            parlay_dict['percent']=0
        parlay_dict['date']=parlay.week.sunday
        active_list.append(parlay_dict)
    inactive_parlays=parlays.filter(closed=1)
    inactive_list=[]
    for parlay in inactive_parlays:
        json_acceptable_inparlay=parlay.parlay.replace("'", "\"")
        inparlay_dict={}
        inparlay_dict['games']=json.loads(json_acceptable_inparlay)
        inparlay_dict['wins']=parlay.wins
        inparlay_dict['losses']=parlay.losses
        inparlay_dict['left']=parlay.left
        if parlay.wins+parlay.losses>0:
            inparlay_dict['percent']=parlay.wins/(parlay.losses+parlay.wins)
        else:
            inparlay_dict['percent']=0
        inparlay_dict['date']=parlay.week.sunday
        inactive_list.append(inparlay_dict)
    context={
        'active_parlays':active_list,
        'inactive_parlays':inactive_list,
        'inactive_bets': inactive_bets,
        'active_bets':active_bets,
        'user':user
    }
    return render(request, 'main_app/user.html', context)

def walkthrough(request):
    return render(request, 'main_app/walkthrough.html')

def leaderboard(request):
    updateleaderboards()
    user = User.objects.get(id=request.session['userid'])
    coin_leaders = User.objects.all().order_by("-total_coins")
    win_leaders = User.objects.all().order_by("-win_percentage")
    context = {
        'win_leaders': win_leaders,
        'coin_leaders': coin_leaders,
        'user':user
    }
    return render(request, 'main_app/leaderboard.html',context)

def updateleaderboards():
    users = User.objects.all()
    for user in users:
        wins=0
        losses=0
        extra = 0
        bets = Bet.objects.filter(user=user.id)
        unpaid_bets = bets.filter(payout__isnull=True)
        for bet in unpaid_bets:
            extra += bet.wager
        for bet in bets:
            if bet.result == 'win':
                wins +=1
            if bet.result == 'lose':
                losses+=1
        if wins>0:
            percentage = wins/(wins+losses)
            print(percentage)
            user.win_percentage = percentage
            user.save()
        user.total_coins = extra+user.points
        user.save()
        print(user.total_coins)
    
def parlay(request):
    myweek=ParlayWeek.objects.first()
    weekfilter= ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),weekend__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
    current_week=weekfilter.first()
    current_lines=ParlayLine.objects.filter(week=current_week)
    first_line=current_lines.order_by('commence_time').first()
    counter=1
    for line in current_lines:
        counter+=1
    context = {
        'current_week':current_week,
        'counter':counter,
        'current_lines':current_lines
    }
    if first_line.commence_time>time.time():
        return render(request, 'main_app/parlay.html', context)
    if first_line.commence_time<time.time():
        weekfilter= ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),sunday__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
        current_week=weekfilter.first()
        all_bets=ParlayBet.objects.filter(week=current_week)
        current_bets = all_bets.filter(losses=0)
        print(current_bets)
        bet_list=[]
        for bet in current_bets:
            json_acceptable_bet=bet.parlay.replace("'", "\"")
            bet_dict={}
            bet_dict['picks']=json.loads(json_acceptable_bet)
            bet_dict['user']=bet.user
            bet_list.append(bet_dict)
        bet_count=len(bet_list)
        all_bets_count=len(all_bets)
        percent=int(bet_count/all_bets_count*100)
        context = {
            'bets':bet_list,
            'bet_count': bet_count,
            'all_bets_count': all_bets_count,
            'percent': percent
        }
    return render(request, "main_app/parlayresults.html", context)

def processparlay(request):
    if request.method=='POST':
        errors={}
        user=User.objects.get(id=request.session['userid'])
        myweek=ParlayWeek.objects.first()
        weekfilter= ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),weekend__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
        current_week=weekfilter.first()
        current_lines=ParlayLine.objects.filter(week=current_week)
        first_line=current_lines.order_by('commence_time').first()
        picks = request.POST['json']
        picks_dict = json.loads(picks)
        for key in picks_dict:
            if not current_lines.filter(id=key).first():
                errors[key]='no matching line'
            if current_lines.filter(id=key).first():
                print('success')
        for line in current_lines:
            if line.commence_time<time.time():
                errors[line]='game already started'
            if picks[line.id]:
                print('success')
            if not picks[line.id]:
                errors[pick]='no matching game'
    if len(errors)>0:
        return HttpResponse('failure')
    if len(errors)==0:
        ParlayBet.objects.create(parlay=picks_dict,week=current_week,user=user)
        return HttpResponse('success')

def parlayresults(request):
    weekfilter= ParlayWeek.objects.filter(weekstart__lte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'),sunday__gte=datetime.fromtimestamp(time.time()-14400).strftime('%Y-%m-%d'))
    current_week=weekfilter.first()
    all_bets=ParlayBet.objects.filter(week=current_week)
    current_bets = all_bets.filter(losses=0)
    print(current_bets)
    bet_list=[]
    for bet in current_bets:
        json_acceptable_bet=bet.parlay.replace("'", "\"")
        bet_dict={}
        bet_dict['picks']=json.loads(json_acceptable_bet)
        bet_dict['user']=bet.user
        bet_list.append(bet_dict)
    bet_count=len(bet_list)
    all_bets_count=len(all_bets)
    percent=int(bet_count/all_bets_count*100)
    context = {
        'bets':bet_list,
        'bet_count': bet_count,
        'all_bets_count': all_bets_count,
        'percent': percent
    }
    return render(request, "main_app/parlayresults.html", context)
#nfl_scores_url='http://www.nfl.com/liveupdate/scores/scores.json'
#nfl_scores_response = (urllib.request.urlopen(nfl_scores_url))
#nfl_scores_data = json.load(nfl_scores_response)
#stats_jsons = {}
#for game in games:
#    stats_url= f"http://nfl.com/liveupdate/game-center/{game.nfl_game_id}/{game.nfl_game_id}_gtd.json"
#    print(stats_url)
#    stats_response=(urllib.request.urlopen(stats_url))
#    stats_data = json.load(stats_response)
#    stats_jsons[game.nfl_game_id]= stats_data