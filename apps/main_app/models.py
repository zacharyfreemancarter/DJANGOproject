from __future__ import unicode_literals
from django.db import models
import re
import bcrypt
import datetime
import time


class UserManager(models.Manager):
    def register_validator(self,postData):
        errors={}
        name_match=User.objects.filter(name=postData['username'])
        email_match=User.objects.filter(email=postData['email'])
        EMAIL_REGEX = re.compile((r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$'))
        if name_match:
            errors['name_match']= 'Username is already taken'
        if email_match:
            errors['email_match']= 'Email is already in system'
        if len(postData['username'])<2:
            errors['username'] = 'Name must be at least 2 characters'
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = 'Invalid Email Address'
        if len(postData['password'])<8:
            errors['password'] = 'Password must be at least 8 characters'
        if postData['confirm'] != postData['password']:
            errors['confirm'] = 'Password confirmation does not match Password'
        return errors
    def login_validator(self,postData,sessionData):
        errors={}
        user = User.objects.filter(name=postData['username'])
        if user:
            logged_user = user[0]
            if bcrypt.checkpw(postData['password'].encode(), logged_user.password.encode()):
                sessionData['userid'] = logged_user.id
                return errors
            else:
                errors['password'] = 'Incorrect Password'
                return errors
        else:
            errors['email'] = 'Email not in system'
        return errors

class BetManager(models.Manager):
    def validator(self, gameData, postData, userData):
        errors = {}
        WAGER_REGEX = re.compile(r'^[0-9]+$')
        print(gameData['commence_time'])
        print(time.time())
        if gameData['commence_time']<time.time():
            errors['past'] = 'Event has already started'
        if not WAGER_REGEX.match(postData['wager']):
            errors['stringwager'] = 'You wagered a string!'
            print(errors)
            return errors
        if int(postData['wager'])<=0:
            errors['zerowager'] = "You must wager at least one pickem coin!"
        if int(postData['wager'])>userData.points:
            errors['bigwager'] = "You don't have enough pickem coins to make that wager!"
        print(errors)
        return errors

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    points= models.IntegerField(default=100)
    objects = UserManager()
    win_percentage = models.FloatField(default=0)
    total_coins = models.IntegerField(blank=True,null=True)
# Create your models here.

class Game(models.Model):
    date = models.DateField()
    nfl_date_id = models.IntegerField()
    nfl_game_id = models.IntegerField()
    home_team_abbr = models.CharField(max_length=255)
    away_team_abbr = models.CharField(max_length=255)
    home_team = models.CharField(max_length=255)
    away_team = models.CharField(max_length=255)
    home_score_Q1 = models.IntegerField(blank=True,null=True)
    home_score_Q2 = models.IntegerField(blank=True,null=True)
    home_score_Q3 = models.IntegerField(blank=True,null=True)
    home_score_Q4 = models.IntegerField(blank=True,null=True)
    home_score_Q5 = models.IntegerField(blank=True,null=True)
    away_score_Q1 = models.IntegerField(blank=True,null=True)
    away_score_Q2 = models.IntegerField(blank=True,null=True)
    away_score_Q3 = models.IntegerField(blank=True,null=True)
    away_score_Q4 = models.IntegerField(blank=True,null=True)
    away_score_Q5 = models.IntegerField(blank=True,null=True)
    current_quarter = models.CharField(max_length=255,blank=True, null=True)
    final_home_score = models.IntegerField(default=0,blank=True,null=True)
    final_away_score = models.IntegerField(default=0,blank=True,null=True)
    tv_channel = models.CharField(max_length=20,blank=True,default=None)
    final = models.BooleanField(default=False)

class Bet(models.Model):
    user = models.ForeignKey(User,related_name='bets')
    date = models.DateField()
    nfl_game_id = models.IntegerField(blank=True, null=True)
    home_team = models.CharField(max_length=255)
    away_team = models.CharField(max_length=255)
    winning_team = models.CharField(max_length=255)
    wager = models.IntegerField()
    points_spread = models.FloatField()
    payout = models.IntegerField(blank=True, null=True)
    result = models.CharField(max_length=10, blank=True, null=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    game = models.ForeignKey(Game,related_name='bets',blank=True,null=True)
    objects = BetManager()

class ParlayWeek(models.Model):
    weekstart = models.DateField()
    sunday = models.DateField()
    weekend = models.DateField()
    closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    winning_result = models.CharField(max_length=1000,blank=True,null=True)

class ParlayBet(models.Model):
    parlay = models.CharField(max_length=1000)
    user = models.ForeignKey(User, related_name='parlays')
    week = models.ForeignKey(ParlayWeek, related_name='parlays')
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    pushes = models.IntegerField(default=0)
    left = models.IntegerField(default=0)
    closed = models.BooleanField(default=False)
    perfect = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ParlayLine(models.Model):
    commence_time=models.IntegerField()
    date=models.DateField()
    home_team=models.CharField(max_length=255)
    away_team=models.CharField(max_length=255)
    home_points=models.FloatField()
    away_points=models.FloatField()
    closed = models.BooleanField(default=False)
    week = models.ForeignKey(ParlayWeek, related_name='lines', blank=True,null=True)
    result = models.CharField(max_length=255,blank=True,null=True)
    game = models.ForeignKey(Game,related_name='parlayline',blank=True,null=True)
