import discord
from discord.ext import commands

from discord.ui import Button, View

import logging
from dotenv import load_dotenv
import os

from datetime import date
import copy
import random
import asyncio
import time
import math

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix="!", intents=intents)

# Version 1.0

@bot.event
async def on_ready():
    print("Running")


TILES_UNICODE = {
    # Dragons
    "中": "🀄",   # Red Dragon
    "發": "🀅",   # Green Dragon
    "白": "🀆",   # White Dragon

    # Winds
    "東": "🀀",   # East Wind
    "南": "🀁",   # South Wind
    "西": "🀂",   # West Wind
    "北": "🀃",   # North Wind

    # Characters 萬子
    "1萬": "🀇", "2萬": "🀈", "3萬": "🀉",
    "4萬": "🀊", "5萬": "🀋", "6萬": "🀌",
    "7萬": "🀍", "8萬": "🀎", "9萬": "🀏",

    # Bamboos 索子
    "1索": "🀐", "2索": "🀑", "3索": "🀒",
    "4索": "🀓", "5索": "🀔", "6索": "🀕",
    "7索": "🀖", "8索": "🀗", "9索": "🀘",

    # Dots 筒子
    "1筒": "🀙", "2筒": "🀚", "3筒": "🀛",
    "4筒": "🀜", "5筒": "🀝", "6筒": "🀞",
    "7筒": "🀟", "8筒": "🀠", "9筒": "🀡",

    # Flowers
    "梅": "🀢",
    "蘭": "🀣",
    "竹": "🀤",
    "菊": "🀥",

    # Seasons
    "春": "🀦",
    "夏": "🀧",
    "秋": "🀨",
    "冬": "🀩",
}

MOVE_PIORITY = {
    0 : -100,
    "Pass": 0,
    "自摸": 1,
    "吃": 2,
    "碰": 3,
    "杠": 4,
    "胡": 5
}

BOLD_START = '\033[1m'
BOLD_END = '\033[0m'

active_games = {}
queueing = []
players = []

class Player():

    """
    Class containing player profile with following information:
        - Player ID
        - Player number
        - Current hand
        - Melded sets (Pung/ Concealed or Revealed Kong/ Chow)
        - Flowers/ Seasons
        - Faan/ Bonus faans
    """
    
    def __init__(self, i, id):
        
        # Player ID to identify the player
        self.player_id = id
        # Player number
        self.player_number = i
        # The faan value of the player's flower/ season  tiles
        self.fs_faan = 0
        # The actual total value of the exposed tiles + flower/season tiles
        self.player_faan = 0
        # Player hand : List containing doubles
        self.player_hand = []
        # Melded tiles: List containing all the melded tiles and meld type
        self.melded = []
        # List containg player's flowers/ seasons, used to calculate points
        self.player_flowers_seasons = []


class Game():

    def __init__(self, channel):
        
        # Game channel
        self.channel = channel 
        # player turn
        self.player_turn = 0
        # flag for touch from wall
        self.flag_wall = False
        # number of players 
        self.player_count = 4
        # generate list containing n(player_count) of Player() object
        self.players = [None, None, None, None]
        # player ids
        self.player_ids = [None, None, None, None]
        # all the available tiles still on the board
        # each tile is a pair : (tile, type)
        self.tiles = []
        # discard pile
        self.discard_pile = []
        # evaluation table
        self.move_table = [[], [], [], []]
        # tile_table
        self.tile_table = []
        # prevailing wind
        self.prevailing_wind = 0
        self.prevailing_track = []
        # move history
        self.players_moved = []
        # flags
        self.winning_hand = None
        self.kong_flag = 0
        self.rob_flag = False

        self.start_flag = False

        self.hand_values = {
            "混一色" : 3,
            "清一色" : 7,
            "小三元" : 5,
            "大三元" : 8,
            "小四喜" : 6,
            "大四喜" : 13,
            "字一色" : 10,
            "花糊" : 3,
            "八仙過海" : 8,
            "十三幺" : 13,
            "九子連環" : 13,
            "天糊" : 13,
            "地糊" : 13,
            "人糊" : 13,
            "七對子" : 3,
            "碰碰糊" : 3,
            "坎坎胡" : 8,
            "十八羅漢": 13,
            "清老頭" : 13,
            "混老头" : 4
        }

        # mahjong sets 
        self.mjset = {"suits" : ["筒", "索", "萬"],
                    "winds" : ["東", "南", "西", "北"],
                    "dragons" : ["中", "發", "白"],
                    "flowers": ["梅","蘭","竹","菊"],
                    "seasons": ["春","夏","秋","冬"]}



    def game_reset(self, b):

        """
        Reset the entire game after a player has won / no player has won when wall runs out of tiles
        """

        self.player_turn = 0
        self.flag_wall = False
        
        # reassign the players in the order of winner to player before the winner
        # [0, 1, 2, 3] to [2, 3, 0, 1]
        
        new_player_list = []
        for i in range(len(self.players)):

            if b:
                p = Player(i, self.players[(self.player_turn + i) % 4].player_id)
            else:
                p = Player(i, self.players[i].player_id)
            
            new_player_list.append(p)

        self.players = new_player_list

        self.tiles = []
        self.discard_pile = []
        self.move_table = [[], [], [], []]
        self.tile_table = []

        self.players_moved = []
        self.prevailing_track = []
        
        self.winning_hand = None
        self.kong_flag = 0
        self.rob_flag = False


    def check_pong(self, n, d):

        """
        Check for pong 碰
            - Player hand has the same type of tile as the one that was just discarded
            - Evaluation table for that tile == 2    
        """
        # check whether is it possible to pong
        
        if self.players[n].player_hand.count(d) == 2 or self.players[n].player_hand.count(d) == 3:    
    
            return True

        return False
    

    def check_kong(self, n, d):

        """
        Check for revealed kong 杠 that can only happen when a tile is discarded beforehand

        Conditions : 
            Player hand has the same type of tile as the one that was just discarded
            Evaluation table for that tile == 3    
        """

        d = self.discard_pile[-1]
        # check whether is it possible to kong
        if self.players[n].player_hand.count(d) == 3:
            return True
        
        # forming exposed kong from exposed pong if player draws from hand
        elif (d, "碰") in self.players[n].melded:
            return True
        
        return False


    def check_c_kong(self, n):

        """
        Check for a Concealed kong that can only happen when player 自摸

        Conditions:
            - In players hand, there is 4 of the same type of tile
        """

        self.players[n].player_hand.sort(key=lambda x: (x[0][-1:], x[0]))
        index = 0

        while (index < len(self.players[n].player_hand)):
            
            count = self.players[n].player_hand.count(self.players[n].player_hand[index])
            if count == 4:
                return True
            
            elif (count == 2 or count == 3):
                index += (count)

            elif (count == 1):
                index += 1
        
        return False


    def check_chow(self, n, d):
        
        """
        Check for chow 杠 that can only happen when a tile is discarded beforehand

        Conditions : 
            Player hand has the suit tiles of the same suit with arrangement (n-1, n, n+1) or (n, n+1, n+2) or (n-2, n-1, n )
            Discarded tile must be by previous player
        """
        
        
        if len(self.players_moved) == 0:
            return None
        
        # discarded tile must be by previous player
        if (n == 0 & self.players_moved[-1] == 3) or (self.players_moved[-1] == (n-1)):
            
            return self.check_straights(self.players[n].player_hand, d)
            
        return None


    def check_straights(self, hand, d):
        
        """
        Check whether the given tile can form a straight for a hand
        """
        
        if d[1] == "suits":
                                    
            copy_hand = copy.deepcopy(hand)
            copy_hand.append(d)
            copy_hand.sort(key=lambda x: (x[0][-1:], x[0]))

            # list to contain all of the tiles with the same suit as the discarded tile
            # tiles will be ordered in ascending number
            same_suits = []
            for tile in copy_hand:
                
                if tile[1] == "suits":

                    if (tile[0][-1] == d[0][-1] and tile not in same_suits):

                        same_suits.append(tile)

            
            if not(len(same_suits)) < 3:
                
                straights = []
                index = same_suits.index(d)

                if 0 <= index + 1 < len(same_suits) and 0 <= index - 1 < len(same_suits):

                    if (abs(int(same_suits[index+1][0][0]) - int(d[0][0])) == 1 and abs(int(same_suits[index-1][0][0]) - int(d[0][0])) == 1):
                        straights.append((same_suits[index-1], d, same_suits[index+1]))

                elif 0 <= index + 2 < len(same_suits):
                    
                    if (abs(int(same_suits[index+1][0][0]) - int(d[0][0])) == 1 and abs(int(same_suits[index+2][0][0]) - int(d[0][0])) == 2):
                        straights.append((d, same_suits[index+1], same_suits[index+2]))

                elif 0 <= index -2 < len(same_suits):

                    if (abs(int(same_suits[index-1][0][0]) - int(d[0][0])) == 1 and abs(int(same_suits[index-2][0][0]) - int(d[0][0])) == 2):
                        straights.append((same_suits[index-2], same_suits[index-1], d))

                if len(straights) >= 1:
                    return straights
                else:
                    return None


    def win_state(self, hand, melded, winning_hands):

        """
        Function that checks whether a player's hand can be reduced to 0 tiles or not
        If yes, it means player has a valid winning hand, return the melded hands
        If no, return None

        Only check for pong and chows as player cannot win if they have a valid kong in their current hand
        """

        # melded can be 3 of the same so set of a
        # if player has no tiles

        if len(hand) == 0 and len(melded) == 4:
            
            sorted_melded = sorted(melded, key=lambda x:(x[1], x[0]))
            if sorted_melded not in winning_hands:
                winning_hands.append(sorted_melded)
            
            return winning_hands
        
        
        for tile in list(set(hand)):
            
            z = copy.deepcopy(hand)
            z.remove(tile)

            r = self.check_straights(z, tile)
            # pong
            if hand.count(tile) == 3:
                
                copy_hand = copy.deepcopy(hand)
                
                copy_melded = copy.deepcopy(melded)
                for i in range(3):
                    copy_hand.remove(tile)

                # if the tile is wind, check for prevailing wind
                if tile[1] == "winds" and tile[0] == self.mjset["winds"][self.prevailing_wind]:
                    copy_melded.append((tile, "碰", True))
                
                else:
                    copy_melded.append((tile, "碰", False))

                winning_hands = self.win_state(copy_hand, copy_melded, winning_hands)

            # check for straights
            if r is not None:
                
                copy_hand = copy.deepcopy(hand)
                copy_melded = copy.deepcopy(melded)
                
                for straight in r:
                    for e in straight:
                        copy_hand.remove(e)
                    
                copy_melded.append((straight, "吃")) 
                winning_hands = self.win_state(copy_hand, copy_melded, winning_hands)

            else:
                return winning_hands

        return winning_hands
          

    def check_hu(self, n):
        
        """
        Ensure player has enough faan to win
        Calculate the faan of the player's hand according to winning type
        """
        
        # function returns whether there is a winning hand or not
        winning_type = self.check_winning_type(n)
        if winning_type is not None:
            self.winning_hand = winning_type
            return True

        return False


    def check_winning_type(self, n):
        
        """
        Hu is only available when got 4 melded + 2 pair 
        or Seven Pairs (七對子), Nine Gates (九子連環), Thirteen Orphans (十三幺)

        - Check for whether can meld 4 times + 2 pair by melding all the tiles in hand despite not revealed pong/kong/chow
        if can form a winning hand, send to win state function

        Note: If the player's hand faan value is the limit, return the hand immediately
            Otherwise add it to a list of all the possible hands with their scores, return the hand with greatest faan value
        """

        # 7 Flowers (花糊)
        if len(self.players[n].player_flowers_seasons) == 7:
            return (None,"花糊", min(self.hand_values["花糊"] + self.calc_hand_faan(self.players[n].melded, n, 13)))
        
        # 8 Flowers (八仙過海)
        elif len(self.players[n].player_flowers_seasons) == 8:
            return (None,"八仙過海", min(self.hand_values["八仙過海"] + self.calc_hand_faan(self.players[n].melded, n, 13)))   
        
        distinct = list(set(self.players[n].player_hand))

        winning_hand = []
        for d in distinct:
            
            # remove the pair of tiles in the player hand 
            # check for all pairs of tiles
            temp_hand = copy.deepcopy(self.players[n].player_hand)
            temp_melded = copy.deepcopy(self.players[n].melded)
            if self.players[n].player_hand.count(d) >= 2:

                temp_hand.remove(d)
                temp_hand.remove(d)
            
                # use a recursive algorithm on the player's temporary hand
                w = self.win_state(temp_hand, temp_melded, [])
                
                if w is not None:
                    for melded in w:
                        if melded not in winning_hand:
                            melded.append((d, "眼"))
                            winning_hand.append(melded)

        # if theres no winning hand from checking the hand and meld for pongs / chow
        # note that the following hands require the player's hand to be fully concealed
        # so player's hand must have 14 tiles
        if len(winning_hand) == 0:
            
            if len(self.players[n].player_hand) == 14:
                # Seven Pairs (七對子) - ignore 4 of the same tiles
                # hand contains 7 pairs
                pairs = 0
                n_terminals = 0
                for d in distinct:
                    if self.players[n].player_hand.count(d) == 2:
                        pairs += 1
                    
                    if self.players[n].player_hand.count(d) == 4:
                        pairs += 2

                    if d[1] == "suits" and (d[0][0] == "1" or d[0][0] == "9"):
                        n_terminals += 1
                
                # 七对子类 
                if pairs == 7:
                    # return the 7 distinct type of tiles
                    if n_terminals == 6:
                        return (distinct ,"清老頭", self.hand_values["清老頭"])
                    else:

                        return (distinct ,"七對子", self.hand_values["七對子"])
                
                # Nine Gates (九子連環)
                # eg: 1112345678999 + any of the 9 same suited tile
                self.players[n].player_hand.sort()
                temp_hand = copy.deepcopy(self.players[n].player_hand)

                for suit in self.mjset["suits"]:

                    if (f'1{suit}', 'suits') in temp_hand and (f'9{suit}', 'suits') in temp_hand:

                        if (temp_hand.count((f'1{suit}', 'suits')) == 3 or temp_hand.count((f'1{suit}', 'suits')) == 4) and (temp_hand.count((f'9{suit}', 'suits')) == 3 or temp_hand.count((f'9{suit}', 'suits')) == 4):
                            
                            # since 1s and 9s must be in the hand already, only count 2 to 8 (7 tiles)
                            count = 0
                            for i in range(1, 10):
                                
                                # if theres 4 of the first suit, remove
                                if i == 1 and temp_hand.count((f'1{suit}', 'suits')) == 4:
                                    temp_hand.remove((f'1{suit}', 'suits'))

                                # if theres 4 of the ninth suit, remove
                                if i == 9 and temp_hand.count((f'9{suit}', 'suits')) == 4:
                                    temp_hand.remove((f'9{suit}', 'suits'))

                                if temp_hand.count((f'{i}{suit}', 'suits')) == 2:
                                    temp_hand.remove((f'9{suit}', 'suits'))
                                
                                if not(i == 1 or i == 9):
                                    if not(temp_hand.count((f'{i}{suit}', 'suits')) == 0):
                                        count += 1

                            if len(temp_hand) == 13 and count == 7:
                                return (self.players[n].player_hand ,"九子連環", self.hand_values["九子連環"])

                # Thirteen Orphans (十三幺)
                # Player has the terminal of each suit, each honor tile + any of the tiles
                temp_hand = copy.deepcopy(self.players[n].player_hand)
                count = 0
                for tile_type in self.mjset.keys():
                    
                    if tile_type == "suits":
                        for suit in self.mjset[tile_type]:
                            
                            if temp_hand.count((f'1{suit}', 'suits')) == 2:
                                temp_hand.remove((f'1{suit}', 'suits'))
                                count += 1

                            elif temp_hand.count((f'1{suit}', 'suits')) == 1:
                                count += 1

                            if temp_hand.count((f'9{suit}', 'suits')) == 2:
                                temp_hand.remove((f'9{suit}', 'suits'))
                                count += 1

                            elif temp_hand.count((f'9{suit}', 'suits')) == 1:
                                count += 1

                    elif tile_type == "winds" or tile_type == "dragons":

                        for tile in self.mjset[tile_type]:

                            if temp_hand.count((f'{tile}', f'{tile_type}')) == 2:
                                temp_hand.remove((f'{tile}', f'{tile_type}'))
                                count += 1

                            elif temp_hand.count((f'{tile}', f'{tile_type}')) == 1:
                                count += 1

                if count == 13 and len(temp_hand) == 13:
                    return (self.players[n].player_hand ,"十三幺", self.hand_values["十三幺"])

        # means theres a winning hand, determine which hand has the greatest value
        else:
            
            # Blessing of Heaven (天糊) - Win on the first turn as the dealer
            # since scores limit, doesnt matter what hand the player gets as long as its valid win 
            if len(self.players_moved) == 0:
                return (winning_hand[0], "天糊", self.hand_values["天糊"])
            
            # Blessing of Earth (地糊) - Win on the dealer’s first discard
            if len(self.players_moved) == 1:
                return (winning_hand[0], "地糊", self.hand_values["地糊"])
            
            # Blessing of Man (人糊) - Win on the first turn as non-dealer
            if n not in self.players_moved:
                return (winning_hand[0], "人糊", self.hand_values["人糊"])
            
            # note: the pair of eyes will be at the last index of the w list
            hand_faan = []
            
            for w in winning_hand:
                
                f = self.calc_hand_faan(w, n)
                # Check for flush
                n_same_suits = 0
                if w[-1][0][1] == "suits":
                    
                    for meld in w:
                        if not(meld[1] == "眼"):
                            if meld[1] == "吃":
                                if meld[0][0][0][-1] == w[-1][0][0][-1]:        
                                    n_same_suits += 1
                            
                            else:
                                if meld[0][0][-1] == w[-1][0][0][-1]:
                                    n_same_suits += 1

                # All Sequences (平糊) - Only sequences and a pair
                pinghu = 0
                if f[3] == 4:
                    hand_faan.append((w, "平糊", self.hand_values["平糊"]))
                    pinghu = 1

                # Mixed Flush (混一色) - Only tiles of a single suit plus honor tiles 
                if n_same_suits == 3 and f[4] == 3 and (f[5] == 1 or f[6] == 1):
                    if (f[1] + f[2] == 4): 
                        hand_faan.append((w, "混一色", min(self.hand_values["混一色"] + f[0] + self.hand_values["碰碰糊"], 13))) 
                    else:
                        hand_faan.append((w, "混一色", min(self.hand_values["混一色"] + f[0] + pinghu, 13))) 

                # Pure Flush (清一色) - Only tiles of a single suit
                if n_same_suits == 4 and f[4] == 4:
                    if (f[1] + f[2] == 4): 
                        hand_faan.append((w, "清一色", min(self.hand_values["清一色"] + f[0] + self.hand_values["碰碰糊"], 13))) 
                    else:
                        hand_faan.append((w, "清一色", min(self.hand_values["清一色"] + f[0] + pinghu, 13))) 

                # Check for Honor Tile Wins
                # Small Three Dragons (小三元) - Have 2 dragon triplets and a pair of the third (do not count points for individual dragon triplets)
                if f[6] == 2 and w[-1][0][1] == "dragons":
                    hand_faan.append((w, "小三元", self.hand_values["小三元"] + f[0] - f[6]))

                # Big Three Dragons (大三元) - Have triplets of all 3 dragons (do not count points for individual dragon triplets)
                if f[6] == 3:
                    hand_faan.append((w, "大三元", self.hand_values["大三元"] + f[0] - f[6]))

                # Small Four Winds (小四喜) - Have triplets of 3 winds and a pair of the 4th (does not stack with half flush, do not count points for individual wind triplets)
                if f[5] == 3 and w[-1][0][1] == "winds":

                    if (f[1] + f[2] == 4):
                        hand_faan.append((w, "小四喜", min(self.hand_values["小四喜"] + f[0] - f[5] + self.hand_values["碰碰糊"], 13)))
                    else:
                        hand_faan.append((w, "小四喜", min(self.hand_values["小四喜"] + f[0] - f[5], 13)))

                # Big Four Winds (大四喜) - Have triplets of all 4 winds
                if (f[5] == 4):
                    return(w, "大四喜", self.hand_values["大四喜"])

                # All Honors (字一色) - Have only honor tiles
                if ((f[5] + f[6]) == 4) and (w[-1][0][1] == "winds" or w[-1][0][1] == "dragons"):
                    hand_faan.append((w, "字一色", min(self.hand_values["字一色"]) + f[2] + f[6] + f[7], 13))

                # All Triplets (碰碰糊) - hand contains pongs or kongs only
                if (f[1] + f[2] == 4):
                    hand_faan.append((w, "碰碰糊", min(self.hand_values["碰碰糊"] + f[0], 13)))

                # Four Concealed Triplets (坎坎胡) - hand contains concealed pongs or kongs only
                if (f[1] + f[2] == 4) and len(self.players[n].player_hand) == 14:
                    hand_faan.append((w, "坎坎胡", min(self.hand_values["坎坎胡"] + f[0], 13)))
                
                # Four Kongs (十八羅漢) - Hand contains 4 kongs
                if f[2] == 4:
                    return hand_faan.append((w, "十八羅漢", self.hand_values["十八羅漢"]))
                
                # Mixed Terminals (混幺九) - Hand only contains terminals (1’s and 9’s) and honors.
                # All Terminals (清老頭) - Hand only contains terminals (1’s and 9’s) 

                if (f[1] + f[2] == 4):
                    n_terminals = 0
                    n_honors = 0
                    
                    for meld in melded:
                        if meld[0][1] == "suits":
                            if meld[0][0][0] == "1" or meld[0][0][0] == "9":
                                n_terminals += 1

                        elif meld[0][1] == "winds" or meld[0][1] == "dragons":
                            n_honors += 1
                    
                    if n_terminals == 4 and (meld[-1][0][0] == "1" or meld[-1][0][0] == "9"):
                        return hand_faan.append((w, "清老頭", self.hand_values["清老頭"]))
                    
                    if (n_terminals + n_honors == 4) and (meld[-1][0][0] == "1" or meld[-1][0][0] == "9" or meld[-1][1] == "winds" or meld[-1][1] == "dragons"):
                        hand_faan.append((w, "混幺九", self.hand_values["混幺九"] + f[0]))

            # print(hand_faan)
            # return the hand with the greatest faan value
            hand_faan.sort(key=lambda x:x[2])
            return hand_faan[-1]    

        return None
    

    def evaluate_moves(self):

        """
        For each game state, evaluate each player's hand and add the legal actions (碰, 杠, 吃) into a list
        """

        self.move_table = [[], [], [], []]

        if not (len(self.discard_pile) == 0):

            d = self.discard_pile[-1]
            for index in range(0, 4):
                # the player that just moved can't move again and can only pass
                if not(index == self.players_moved[-1]):
                    if self.check_pong(index, d):
                        self.move_table[index].append(2)
                    if self.check_kong(index, d):
                        self.move_table[index].append(3)

                    if self.check_chow(index, d) is not None:
                        # only allow chow for the player that is after the player that discarded the tile
                        if (index == 0 and self.players_moved[-1] == 3) or (index == (self.players_moved[-1] + 1)):
                            self.move_table[index].append(4)

                    self.players[index].player_hand.append(d)
                    if self.check_hu(index):
                        self.move_table[index].append(5)
                    self.players[index].player_hand.remove(d)   


    def initialise(self):

        """
        Initialise game by :
            
            1) Generating the tiles and creating a wall
            2) Assigning tiles to player
            3) Check for flowers / seasons, 
                - give faan to the player if the flower / season corresponds to them 
                - give player another tile in place of the flower
                [repeat until all the tiles in players hand is a non flower / season tile]
        """

        self.generate_tiles()

        for i in range(self.player_count):

            self.assign_tiles(i)

        # check for flowers and seasons
        for n in range(self.player_count):

            while self.f_s_check_replace(n):
                pass

            self.players[n].player_hand.sort(key=lambda x: (x[0][-1:], x[0]))

        # initialise the evaluation table for the first time
        for n in range(self.player_count):
            self.evaluate_table(n)


    def assign_tiles(self, n):

        """
        Assign tiles to player at the beginning of the game
        """

        if n == 0:
            no_missing = 14

        else:
            no_missing = 13 

        for m in range(no_missing - len(self.players[n].player_hand)):
            
            self.replace_tile(n)

        
    def f_s_check_replace(self, n):

        """
        Check for flowers / season in player's hand
        Replace the flower / season tiles
        Return a bool indicating whether there is flowers/ seasons in player's hand or not
        """
        for i in reversed(range(len(self.players[n].player_hand))):

            tile = self.players[n].player_hand[i] 
            if (tile[1] == "flowers" or tile[1] == "seasons"):

                self.players[n].player_flowers_seasons.append(tile)
                self.players[n].player_hand.pop(i)

                # replace the tile (season / flower) that was removed
                self.replace_tile(n)
                # calculate the faan value of the flowers/ season of the player's hand
                self.calc_fs_faan(n)
                # return true if hand has a flower / seasons
                return True
        
        # returns false if hand does not have flowers / seasons
        return False


    def replace_tile(self, n):

        """
        Function to add a tile to player's hand 
        If the tile drawn is flower / season tile, replace it
        """

        if len(self.tiles) != 0:
            tile = self.tiles.pop(0)

            while (tile[1] == "flowers" or tile[1] == "seasons"):
                self.players[n].player_flowers_seasons.append(tile)
                # calculate the faan value of the flowers/ season of the player's hand
                self.calc_fs_faan(n)
                tile = self.tiles.pop(0)

            self.players[n].player_hand.append(tile)
        

    def generate_tiles(self):

        """
        Generate all the 144 tiles where:
        
            Each suit has tiles numbered from 1 to 9, where each number has 4 more tiles
            Each wind has 4 tiles
            Each dragon has 4 tiles

        Generate evaluation table where 

            Key : Type of Tile | Number of said tile
        """
        d = {}
        for type in self.mjset:

            if type == "suits":

                d[type] = {}
                for suit in self.mjset[type]:
                    
                    d[type][suit] = []
                    for i in range(9):
                        d[type][suit].append(0)

                        for j in range(4):
                            self.tiles.append((f"{i + 1}{suit}", type))

            elif type == "winds" or type == "dragons":
                
                d[type] = {}
                for honor in self.mjset[type]:
                    d[type][honor] = 0
                    
                    for i in range(4):
                        self.tiles.append((honor, type))

            elif type == "flowers" or type == "seasons":

                for bonus in self.mjset[type]:
                    self.tiles.append((bonus, type))

        # randomise the tiles
        random.shuffle(self.tiles)
        
        li = []
        for i in range(self.player_count):
            li.append(copy.deepcopy(d))

        self.tile_table = li


    def calc_fs_faan(self, n):
        """
        Based on the flower of a player's hand, return the number of faan the player has
        """
        faan = 0
        for tile in self.players[n].player_flowers_seasons:

            if self.mjset[tile[1]][n] == tile[0]:
                faan += 1
            
        return faan
    

    def evaluate_table(self, n):

        """
        Evaluate a player's hand by assigning count to each tile on player hand
        """

        for tile in self.players[n].player_hand:

            if tile[1] == "suits":
                
                self.tile_table[n][tile[1]][tile[0][-1]][int(tile[0][0])-1] += 1

            elif tile[1] == "dragons" or tile[1] == "winds":

                self.tile_table[n][tile[1]][tile[0][-1]] += 1


    def update_state(self):

        """
        Update the game state after move is finished 
        given that Pong / Kong / Chow didnt occur
        If pong / kong / chow occurs, 
        player turn = player that pong / kong / chow
        """

        self.player_turn = (self.player_turn + 1 ) % 4


@bot.command()
async def queue(ctx):
    user = ctx.author

    # Prevent duplicate joins
    if user in queueing:
        await ctx.send(f"{user.mention}, you are already in the queue!")
        return

    queueing.append(user)
    seconds = 0

    # Define leave button
    class LeaveQueueView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Leave Queue", style=discord.ButtonStyle.red)
        async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
            if user in queueing:
                queueing.remove(user)
                await interaction.response.send_message(f"{user.mention} left the queue.", ephemeral=True)
            self.stop()

    view = LeaveQueueView()

    # Function to create/update embed
    def update_embed():
        embed = discord.Embed(
            title=f"{user.mention} joined the queue!",
            description=f"*Queueing for {seconds} seconds*",
            color=0x00ff00
        )
        return embed

    # Send initial embed
    queue_message = await ctx.send(embed=update_embed(), view=view)

    # Timer loop
    while user in queueing:

        await asyncio.sleep(1)
        seconds += 1

        # Update embed
        await queue_message.edit(embed=update_embed(), view=view)

        # Check if enough players to start game
        if len(queueing) >= 4:

            mentions = ", ".join([u.mention for u in queueing[:4]])

            start_em = discord.Embed(title=f"Matched found!",
                                     description=f"Game starting with: {mentions}",
                                     color=0x00ff00)
            
            await ctx.send(embed=start_em)
            # remove these players from queue
            queueing[:4] = []
            break


@bot.command()
async def run(ctx):

    if ctx.channel.id in active_games.keys():
        await ctx.send("A game is already active in this channel")
        return
    
    # if there is no active game in the channel, make a new one
    active_games[ctx.channel.id] = Game(ctx.channel.id)
    game: Game = active_games[ctx.channel.id]
    seconds = 30

    def update_player_embed():
        
        """
        Update the player embed anytime a button is pressed. 
        If a player has been assigned, add their username to the player number.
        """
        
        embed = discord.Embed(
            title="Hong Kong Mahjong (4 Players)",
            description=f"{seconds} sec left",
            color=0x00ff00
        )

        for i in range(4):
            player_id = game.player_ids[i]
            if player_id is None:
                embed.add_field(name=f"Player {i+1}", value="*Waiting...*", inline=False)

            else:
                embed.add_field(name=f"Player {i+1}", value=f"<@{player_id}>", inline=False)

        return embed
        
    async def assign_player(interaction, n, button):

        if interaction.user.id in game.player_ids:
            await ctx.send(f"<@{interaction.user.id}> You have already registered as a player!")
        
        else:
            # assign the player
            game.players[n] = Player(n, interaction.user.id)
            game.player_ids[n] = interaction.user.id

            # disable the button so no other user can touch it
            button.disabled = True

            await msg.edit(embed=update_player_embed(), view=view)
            await ctx.send(f"<@{interaction.user.id}> You have registered as player {n + 1}")

        await interaction.response.defer(ephemeral=False)

    class RunView(discord.ui.View):

        # Player buttons
        @discord.ui.button(label="Player 1")
        async def p1_button(self, interaction: discord.Interaction, button):
            await assign_player(interaction, 0, button)

        @discord.ui.button(label="Player 2")
        async def p2_button(self, interaction: discord.Interaction, button):
            await assign_player(interaction, 1, button)

        @discord.ui.button(label="Player 3")
        async def p3_button(self, interaction: discord.Interaction, button):
            await assign_player(interaction, 2, button)

        @discord.ui.button(label="Player 4")
        async def p4_button(self, interaction: discord.Interaction, button):
            await assign_player(interaction, 3, button)

        # Start button
        @discord.ui.button(label="Start", style=discord.ButtonStyle.green, row=2)
        async def start_game(self, interaction, button):
            # Means there is 4 players and game can start
            # TODO for now == 3 for debug but should be == 0
            if game.player_ids.count(None) == 3:
                game.start_flag = True

            else:
                await ctx.send("Not enough players to start the game. Please wait!")

            await interaction.response.defer(ephemeral=False)

    embed = update_player_embed()
    view = RunView()
    msg = await ctx.send(embed=embed, view=view)

    # Give 1 minute for players to join. If timer runs out and theres not enough players terminate
    while seconds >= 0:
        
        # if game has alredy started, then break
        if game.start_flag:
            break

        time.sleep(1)
        seconds -= 1
        await msg.edit(embed=update_player_embed(), view=view)

    if not game.start_flag:
        if game.player_ids.count(None) != 0:
            del active_games[ctx.channel.id]
            await ctx.send(f"Number of players: {4- game.player_ids.count(None)} / 4 \nNot enough players to start game. Try again.")
            await msg.delete()

    else:
        await run_game(ctx)
        await msg.delete()


@bot.command()
async def quit(ctx):

    """
    Terminate the mahjong game in the channel that this command was sent in.
    Only allow the active players to end the game (Prevent trolling)
    """

    if ctx.channel.id not in active_games.keys():
        await ctx.send("There is no active game in this channel. To start a game type !run")
        return

    game = active_games[ctx.channel.id]

    # If literally no players joined
    if game.player_ids.count(None) == 4:
        await ctx.send("The mahjong game has been ended. Thanks for playing!")
        del active_games[ctx.channel.id]
        return

    quit_list = [None, None, None, None]
    seconds = 20

    # Holder for DM message objects + views
    dm_messages = [None, None, None, None]
    dm_views = [None, None, None, None]

    def build_quit_embed():
        embed = discord.Embed(
            title="End Game?",
            description=f"*{seconds} sec left for voting*",
            color=0x00ff00
        )

        for i in range(4):
            pid = game.player_ids[i]
            if pid is None:
                continue

            if quit_list[i] is True:
                status = f"<@{pid}> ✅"
            elif quit_list[i] is False:
                status = f"<@{pid}> ❌"
            else:
                status = f"<@{pid}> waiting..."

            embed.add_field(name=f"Player {i+1}", value=status, inline=False)

        return embed

    async def update_all():
        embed = build_quit_embed()
        for i in range(4):
            if dm_messages[i] is not None:
                await dm_messages[i].edit(embed=embed, view=dm_views[i])

    class QuitView(discord.ui.View):

        def __init__(self, index):
            super().__init__(timeout=None)
            self.index = index

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
        async def yes_button(self, interaction: discord.Interaction, button):
            if interaction.user.id == game.player_ids[self.index]:
                quit_list[self.index] = True
                await interaction.response.defer()
                await update_all()

        @discord.ui.button(label="No", style=discord.ButtonStyle.red)
        async def no_button(self, interaction: discord.Interaction, button):
            if interaction.user.id == game.player_ids[self.index]:
                quit_list[self.index] = False
                await interaction.response.defer()
                await update_all()

    # Send DM to each player
    for i in range(4):
        pid = game.player_ids[i]
        if pid is None:
            continue

        user = await bot.fetch_user(pid)

        dm_views[i] = QuitView(i)
        embed = build_quit_embed()

        dm_messages[i] = await user.send(embed=embed, view=dm_views[i])

    # Countdown timer
    while seconds > 0:
        await asyncio.sleep(1)
        seconds -= 1
        await update_all()

        # Early termination if everyone voted Yes
        if quit_list.count(True) == (4 - game.player_ids.count(None)):
            break

    # Disable all buttons
    for v in dm_views:
        if v:
            for but in v.children:
                but.disabled = True

    await update_all()

    # Count votes
    yes_votes = quit_list.count(True)
    needed = math.floor((4 - game.player_ids.count(None)) / 2) + 1

    if yes_votes >= needed:
        del active_games[ctx.channel.id]

        # Send DM end message
        end_embed = discord.Embed(
            title="The game has ended. Thanks for playing!",
            color=0x00ff00
        )
        for pid in game.player_ids:
            if pid:
                user = await bot.fetch_user(pid)
                await user.send(embed=end_embed)

    else:
        # Continue game
        continue_embed = discord.Embed(
            title=f"Vote Results: {yes_votes}/{4 - game.player_ids.count(None)} voted YES",
            description="The game will continue.",
            color=0xffd000
        )
        for pid in game.player_ids:
            if pid:
                user = await bot.fetch_user(pid)
                await user.send(embed=continue_embed)


@bot.command()
async def h(ctx):

    """
    Send into the channel a list of the available commands
    """
    em = discord.Embed(title="Commands for MjCord", color=0x00ff00)
    em.add_field(name="!run - Start the mahjong game", value="", inline=False)
    em.add_field(name="!quit - Quit the mahjong game", value="", inline=False)

    await ctx.send(embed=em)


# @bot.command()
# run game
async def run_game(ctx):

    """
    Function that handles all of mahjong gameplay loop
    """

    game = Game(ctx.channel.id)
    active_games[ctx.channel.id] = game

    # temporary
    game.player_ids = [512192531220398090, 512192531220398090, 512192531220398090, 512192531220398090]
    game.players = [Player(0, 512192531220398090), Player(1, 512192531220398090),Player(2, 512192531220398090),Player(3, 512192531220398090)]
    
    # loading bar
    await loading_bar(ctx)

    while True:

        # game.players[0].player_hand = [
        #     ("9筒", "suits")
        # ]

        # game.players[0].player_hand = [
        #     ("1筒", "suits"), ("1筒", "suits"), ("1筒", "suits"), 
        #     ("2筒", "suits"), ("2筒", "suits"), ("2筒", "suits"), 
        #     ("3筒", "suits"), ("3筒", "suits"), ("3筒", "suits"), 
        #     ("6筒", "suits"), ("6筒", "suits"), ("9筒", "suits"),
        #     ("9筒", "suits"),  ("9筒", "suits") 
        #     ]   

        if game.channel not in active_games.keys():
            return
        
        # initialise the game
        game.initialise()

        while True:
            
            # check whether game is still existing if not break the loop
            if game.channel not in active_games.keys():
               return

            # if the wall runs out of tiles, end the game
            if len(game.tiles) == 0:
                
                em = discord.Embed(title="Draw", description="The wall has run out of tiles")
                for id in game.player_ids:
                    user = bot.fetch_user(id)
                    user.send(embed=em)
                
                await handle_go_next(game, False)
                break

            # send each player the current game state and the discard pile (constant and wont change even if got user input)
            discard_string = discard_pile(game)
            
            # list of player's hand, meld and flower/ season information
            hand_list, melded_list, fs_list = game_info(game)
            
            # list of the sent messages so that it can be edited afterwards
            game_info_list = [None, None, None, None]
           
            # if its the very first move of the game, first player must throw out a tile while other players cant do anything
            if (game.player_turn == 0 and len(game.players_moved) == 0):
                
                task = []
                for n in range(4):
                    
                    # Get user
                    user = await bot.fetch_user(game.player_ids[n])

                    # game info
                    game_info_msg = await display_game_info(game, n, user, hand_list, melded_list, fs_list)
                    game_info_list[n] = game_info_msg

                    # discard pile
                    discard_embed = discord.Embed(title="Discard Pile", description=f"{discard_string}", color=0x00ff00)
                    await user.send(embed=discard_embed)

                    # player info
                    player_embed = discord.Embed(title="Your Hand", 
                                    description=f"{hand_list[n]} \nMelded: {melded_list[n]} \nFlowers: {fs_list[n]}", 
                                    color=0x00ff00)
                    
                    await user.send(embed=player_embed)
                    
                    # Player 1 can kong / throw out tile on the first move / hu
                    # Other players just wait
                    if n == 0:
                        # while true, let the player choose until he throws a tile
                        task.append(asyncio.create_task(
                            handle_self_touch(game, user, n)
                        ))
                
                await asyncio.gather(*task)
                
            else:
                
                # other than the first move, every player can either pong, kong, chow, hu or pass
                # the active player can also self touch
                # piority is given in the order of: pass, self touch, chow, pong, kong, hu

                # evaluate for each player what valid moves they have
                game.evaluate_moves()
                tasks = []

                for n in range(4):
                    
                    # get user
                    user = await bot.fetch_user(game.player_ids[n])

                    # game info
                    game_info_msg = await display_game_info(game, n, user, hand_list, melded_list, fs_list)
                    game_info_list[n] = game_info_msg

                    # discard pile
                    discard_embed = discord.Embed(title="Discard Pile", description=f"{discard_string}", color=0x00ff00)
                    await user.send(embed=discard_embed)
                    
                    # prompt each user to put in a move
                    # queue the player input task
                    tasks.append(asyncio.create_task(
                        display_player_info(game, user, n, hand_list, melded_list, fs_list, game.move_table)
                    ))
                
                # wait for all 4 players to respond
                player_info_list = await asyncio.gather(*tasks)
                
                # The player with the highest move piority will move in this round
                piority = (None, 0, None)
                for info in player_info_list:
                    if MOVE_PIORITY[info[1]] == 5:
                        piority = info
                        break

                    if MOVE_PIORITY[info[1]] >= MOVE_PIORITY[piority[1]]:
                        piority = info
                
                # update current player turn
                game.player_turn = piority[2]

                await handle_normal(game, user, n, piority)

            # there is a winner (hu)
            if game.winning_hand is not None:
                
                # Show each player the winning hand and winning player
                await display_hu(game)
                # players vote to go next game or choose to end session
                await handle_go_next(game, True)

                break

            # update prevailing wind
            if len(game.prevailing_track) == 4:
                        
                game.prevailing_wind = (game.prevailing_wind + 1) % 4
                game.prevailing_track = []
                
            # add the previous players number to history
            game.players_moved.append(game.player_turn)

            game.update_state()
            
            # reset flags for next move
            game.flag_wall = False
            game.kong_flag = 0
            game.rob_flag = False


async def handle_go_next(game:Game, b):
        
    go_next = await vote_go_next(game)
    # Prompt each user whether they want to continue to new game or not

    if go_next:
        
        end_embed = discord.Embed(title="Game is resetting....")
        for user_id in game.player_ids:
            user = await bot.fetch_user(user_id)
            await user.send(embed=end_embed)

        game.game_reset(b)

    # terminate the session
    elif not go_next:
        
        end_embed = discord.Embed(title="The session has ended. Thanks for playing")
        for user_id in game.player_ids:
            user = await bot.fetch_user(user_id)
            await user.send(embed=end_embed)
        
        del active_games[game.channel]


async def vote_go_next(game:Game):

    next_list = [None, None, None, None]
    messages = [None, None, None, None]
    views = [None, None, None, None]
    seconds = 30

    def build_vote_embed():
        embed = discord.Embed(
            title="Start a New Game?",
            description=f"**{seconds} seconds** remaining to vote.",
            color=0x00ff00
        )

        for i, player_id in enumerate(game.player_ids):
            vote = next_list[i]

            if vote is True:
                text = f"<@{player_id}> ✅ Yes"
            elif vote is False:
                text = f"<@{player_id}> ❌ No"
            else:
                text = f"<@{player_id}> waiting..."

            embed.add_field(name=f"Player {i + 1}", value=text, inline=False)

        return embed
    
    class VoteView(discord.ui.View):

        def __init__(self, player_index):
            super().__init__(timeout=None)
            self.index = player_index

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
        async def yes_button(self, interaction: discord.Interaction, button):
            next_list[self.index] = True
            await interaction.response.defer()
            await update_all_voting_messages()

        @discord.ui.button(label="No", style=discord.ButtonStyle.red)
        async def no_button(self, interaction: discord.Interaction, button):
            next_list[self.index] = False
            await interaction.response.defer()
            await update_all_voting_messages()

    async def update_all_voting_messages():
        embed = build_vote_embed()

        for i in range(4):
            msg = messages[i]
            if msg is None:
                continue
            
            await msg.edit(embed=embed, view=views[i])   

    # Send all players the initial DM
    for i, player_id in enumerate(game.player_ids):
        user = await bot.fetch_user(player_id)

        views[i] = VoteView(i)
        embed = build_vote_embed()

        messages[i] = await user.send(embed=embed, view=views[i])

    # Countdown loop
    while seconds > 0:

        # End early if all four players have voted
        if all(v is not None for v in next_list):
            break

        await asyncio.sleep(1)
        seconds -= 1

        await update_all_voting_messages()

    # Final update (disable buttons)
    for view in views:
        if view:
            for child in view.children:
                child.disabled = True

    await update_all_voting_messages()

    if next_list.count(True) == 4:
        return True
    
    else:
        return False
        

async def display_hu(game: Game):

    """
    Show each player the following information when a player was won
    - Which player has won
    - Winner's hand, flower/ seasons, winning type and faan

    Prompt each user on whether they want to restart the game or not
    """

    # GUI 
    win_embed = discord.Embed(title=f"Player {game.player_turn + 1} has won", color=0x00ff00)

    win_string = ""
    fs_string = ""

    for meld in game.winning_hand[0]:
        if meld[1] == "碰":
            for z in range(3):
                win_string += f"{meld[0][0]} "
        
        elif meld[1][-1] == "杠":
            for z in range(4):
                win_string += f"{meld[0][0]} "
        
        elif meld[1] == "吃":
            for t in meld[0]:
                win_string += f"{t[0]} "

        elif meld[1] == "眼":
            for z in range(2):
                win_string += f"{meld[0][0]} "

    for fs in game.players[game.player_turn].player_flowers_seasons:
        fs_string += f"{fs[0]} "

    win_embed.add_field(name="Winning Hand", value=f"{win_string}\n {fs_string}", inline=False)
    win_embed.add_field(name=f"Winning type", value=f"{game.winning_hand[1]} with {game.winning_hand[2]} faan", inline=False)
    
    # send the winning hand to each user
    for player_id in game.player_ids:

        u = await bot.fetch_user(player_id)
        await u.send(embed=win_embed)


async def handle_normal(game:Game, user, n, move):

    """
    If self touch
    - user draws a tile and then has the option to either throw, concealed kong or hu

    If pong/ chow
    - user takes the tile from discard and add to meld, throw a tile

    If revealed kong
    - user takes the tile from discard, draws a tile then throws it back

    If hu
    - end game
    """

    d = game.discard_pile[-1]
    # self touch
    if move[1] == "自摸":
        
        await draw_tiles(game, user, n)
        await handle_self_touch(game, user, n)

    # pong
    elif move[1] == "碰":
        await handle_pong(game, user, n, d)

    # revealed kong
    elif move[1] == "杠":
        await handle_rkong(game, user, n ,d)
    
    # Chow
    elif move[1] == "吃":
        await handle_chow(game, user, n, d)

    elif move[1] == "胡":
        pass


async def handle_rkong(game, user, n ,d):

    if game.players[n].player_hand.count(d) == 3:
        # Remove the kong tiles from player hand
        for l in range(3):
            game.players[n].player_hand.remove(d)
        
        if d[1] == 'winds' and game.mjset["winds"][game.prevailing_wind] == d[0]:
            game.players[n].melded.append((d, "明杠", True))
        else:
            game.players[n].melded.append((d, "明杠", False))

    # forming exposed kong from exposed pong if player draws from hand
    elif (d, "碰", True) in game.players[n].melded:

        game.players[n].melded.remove((d, "碰", True))
        game.players[n].melded.append((d, "明杠", True))
        

    elif (d, "碰", False) in game.players[n].melded:
        
        game.players[n].melded.remove((d, "碰", False))
        game.players[n].melded.append((d, "明杠", False))

    game.discard_pile.pop()
    # replace tile
    await draw_tiles(game, user, n)

    # handle self touch
    await handle_self_touch(game, user, n)
    game.rob_flag = True


async def handle_pong(game, user, n, d):

    for l in range(2):
        game.players[n].player_hand.remove(d)
    
    if d[1] == 'winds' and game.mjset["winds"][game.prevailing_wind] == d[0]:
        game.players[n].melded.append((d, "碰", True))
        
    else:
        game.players[n].melded.append((d, "碰", False))

    game.discard_pile.pop()
    await throw_tile(game, user, n)
    
    
async def handle_chow(game:Game, user, n, d):

    class s_view(discord.ui.View):
        
        def __init__(self):

            super().__init__()

            # get the list of available straights
            r = game.check_chow(n, d)

            if r is not None:

                straights = r
                for index, s in enumerate(straights):

                    straight_str = ""
                    for tile in s:

                        straight_str += f"{tile[0]} "
                    
                    button = discord.ui.Button(
                        label=f"{straight_str}",
                        custom_id=f"{index}",
                    )

                    async def callback(interaction: discord.Interaction):
                        await self.button_callback(interaction, s)

                    button.callback = callback
                    self.add_item(button)
            
        async def button_callback(self, interaction: discord.Interaction, s):
            
            # remove the tiles that form the straight from player hand
            for t in s:
                game.players[n].player_hand.remove(t)

            game.players[n].melded.append((s, "吃"))
            game.discard_pile.pop()

            await throw_tile(game, user, n) 

            await self.disable_all()
            await interaction.response.defer()
            self.stop()

        async def disable_all(self):

            for item in self.children:
                if not item.disabled:
                    item.disabled = True
            
            await msg.edit(view=self)


    view = s_view()

    msg = await user.send(view=view)


async def handle_self_touch(game:Game, user, n):

    """
    Handle the logic for 打牌, 暗杠 and 胡 when player has inputed through button
    The function only returns once the player puts in 打牌
    If 暗杠, player redo the loop as need to redraw tile and throw again
    If 胡, end game
    """

    while True:

        move = await display_self_touch(game, user, n)

        # Throw a tile
        if move[1] == "打牌":

            await throw_tile(game, user, n)
            break
        
        # Concealed Kong
        elif move[1] == "暗杠":
            
            await concealed_kong(game, user, n)

        # Hu (End Game)
        elif move[1] == "胡":

            break
        
    return


async def concealed_kong(game:Game, user, n):
    
    """
    Prompt a user for which tile they would like to concealed kong
    Remove 4 of the tiles from player hand then draw a replacement tile
    """
    
    class ck_view(discord.ui.View):

        def __init__(self):

            super().__init__()

            self.tile_to_kong = None

            distinct = sorted(list(set(game.players[n].player_hand)))

            for d in distinct:

                if game.players[n].player_hand.count(d) == 4:

                    button = discord.ui.Button(
                        label=f"{d[0]}",
                        custom_id=f"{d[0]}",
                    )

                    # Correct: wrap callback to pass tile
                    async def callback(interaction: discord.Interaction, tile=d):
                        await self.button_callback(interaction, tile)

                    button.callback = callback
                    self.add_item(button)

        async def button_callback(self, interaction: discord.Interaction, tile):

            self.tile_to_kong = tile
            await self.disable_all()
            await interaction.response.defer()
            self.stop()

        async def disable_all(self):

            for item in self.children:
                if not item.disabled:
                    item.disabled = True
            
            await msg.edit(view=self)

    view = ck_view()
    await user.send("Choose a tile to 暗杠")
    msg = await user.send(view=view)

    await view.wait()

    # remove 杠 tiles from hand
    for i in range(4):
        game.players[n].player_hand.remove(view.tile_to_kong)

    # sort the hand
    game.players[n].player_hand.sort(key=lambda x: (x[0][-1:], x[0]))

    # prevailing wind
    if view.tile_to_kong[1] == 'winds' and game.mjset["winds"][game.prevailing_wind] == view.tile_to_kong[0]:
        game.players[n].melded.append((view.tile_to_kong, "暗杠", True))
    else:
        game.players[n].melded.append((view.tile_to_kong, "暗杠", False))
        
    # replace tile
    await draw_tiles(game, user, n)

    game.kong_flag += 1


async def draw_tiles(game:Game, user, n):

    """
    Draw a tile from the wall and show the respective player the tile 
    """

    if len(game.tiles) != 0:

        tile = game.tiles.pop()

        while (tile[1] == "flowers" or tile[1] == "seasons"):

            game.players[n].player_flowers_seasons.append(tile)
            # calculate the faan value of the flowers/ season of the player's hand
            game.calc_fs_faan(n)

            tile = game.tiles.pop(0)
        
        game.players[n].player_hand.append(tile)

        em = discord.Embed(title=f"{tile[0]} was drawn", color=0x00ff00)
        await user.send(embed=em)

    hand_string = ""
    for tile in game.players[n].player_hand:
        hand_string += f"{tile[0]} " 

    phand_embed = discord.Embed(title="Your updated Hand", description=hand_string, color=0x00ff00)
    await user.send(embed=phand_embed)


async def display_self_touch(game:Game, user, n):

    """
    Display the buttons for 打牌, 暗杠 and 胡 when player 自摸 
    Display also for first player on first move
    """
    
    class SelfTouchView(discord.ui.View):

        def __init__(self):
            super().__init__()
            self.result = None

        # Throw a tile 
        @discord.ui.button(label="打牌 Throw tile", custom_id="1")
        async def self_touch_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "打牌", n)
            await self.disable_all()
            await interaction.response.defer()
            self.stop()
        
        # Concealed Kong 暗杠
        @discord.ui.button(label="暗杠 Concealed Kong", custom_id="2")
        async def kong_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "暗杠", n)
            await self.disable_all()
            await interaction.response.defer()
            self.stop()
        
        # Hu 胡 (Only valid if player has won. Refer to win_state() function for win conditions)
        @discord.ui.button(label="胡 Hu", custom_id="3")
        async def hu_button(self, interaction: discord.Interaction, button):
            
            self.result = (msg, "胡", n)
            await self.disable_all()
            await interaction.response.defer()
            self.stop()

        # disable other buttons once 1 has been clicked
        async def disable_all(self):

            for item in self.children:
                if not item.disabled:
                    item.disabled = True

            await msg.edit(view=self)

    t_view=SelfTouchView()

    for item in t_view.children:

        # check whether can concealed kong
        if (item.custom_id == "2" and game.check_c_kong(n)) or (item.custom_id == "3" and game.check_hu(n)) or (item.custom_id == "1"):
            pass
            
        else:
            item.disabled = True

    await user.send("Choose an action:")
    msg = await user.send(view=t_view)
    await t_view.wait()

    return t_view.result


async def throw_tile(game:Game, user, n):

    """
    Prompt the user to choose a tile from their hand
    Remove the tile from their hand
    Add the chosen tile to discard
    """

    class t_view(discord.ui.View):

        def __init__(self):
            super().__init__()
            self.tile_to_throw = None

            distinct = list(set(game.players[n].player_hand))

            for d in distinct:
                button = discord.ui.Button(
                    label=f"{d[0]}",
                    custom_id=f"{d[0]}",
                )

                async def callback(interaction: discord.Interaction, tile=d):
                    await self.button_callback(interaction, tile)

                button.callback = callback
                self.add_item(button)

        async def button_callback(self, interaction: discord.Interaction, tile):
            self.tile_to_throw = tile
            await self.disable_all()
            await interaction.response.defer()
            self.stop()

        async def disable_all(self):

            for item in self.children:
                if not item.disabled:
                    item.disabled = True
            
            await msg.edit(view=self)

    view = t_view()
    await user.send("Choose a tile to throw")
    msg = await user.send(view=view)
    await view.wait()

    # remove tile from player hand
    game.players[n].player_hand.remove(view.tile_to_throw)
    # add the discarded tile into discard pile
    game.discard_pile.append(view.tile_to_throw)
    

async def display_player_info(game:Game, user, n , hand_list, melded_list, fs_list, move_table):

    # # return the move number and the message so that can be edited
    player_embed = discord.Embed(title="Your Hand", 
                                 description=f"{hand_list[n]} \nMelded: {melded_list[n]} \nFlowers: {fs_list[n]}", 
                                 color=0x00ff00)
    
    class PlayerView(discord.ui.View):

        def __init__(self):
            super().__init__()
            self.result = None

        # Touch from wall (Only available for the player with active turn)
        @discord.ui.button(label="自摸 Self touch", custom_id="1")
        async def self_touch_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "自摸", n)
            await disable_all()
            await interaction.response.defer()
            self.stop()

        # Pong 碰 (Hand must have 2 tiles of the same 'type' as the discarded tile  on board)
        @discord.ui.button(label="碰 Pong", custom_id="2")
        async def pong_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "碰", n)
            await disable_all()
            await interaction.response.defer()
            self.stop()
        
        # Kong 杠 (Hand must have 3 tiles of the same 'type' as the discarded tile on board)
        @discord.ui.button(label="杠 Kong", custom_id="3")
        async def kong_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "杠", n)
            await disable_all()
            await interaction.response.defer()
            self.stop()

        # Chow 吃 (Hand must have 2 or more successive tiles which can be succeeded or preceeded by the discarded tile)
        @discord.ui.button(label="吃 Chow", custom_id="4")
        async def chow_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "吃", n)
            await disable_all()
            await interaction.response.defer()
            self.stop()
        
        # Hu 胡 (Only valid if player has won. Refer to win_state() function for win conditions)
        @discord.ui.button(label="胡 Hu", custom_id="5")
        async def hu_button(self, interaction: discord.Interaction, button):
            
            self.result = (msg, "胡", n)
            await disable_all()
            await interaction.response.defer()
            self.stop()
        
        # Pass if player doesnt want to make any move
        @discord.ui.button(label="Pass", custom_id="6")
        async def pass_button(self, interaction: discord.Interaction, button):

            self.result = (msg, "Pass", n)
            await disable_all()
            await interaction.response.defer()
            self.stop()

        
    async def disable_all():

        """
        When one of the valid buttons is pressed, disable all other buttons so the player cannot double input
        """

        for item in p_view.children:
            if not item.disabled:
                item.disabled = True

        await msg.edit(embed=player_embed, view=p_view)

    p_view = PlayerView()
    
    for item in p_view.children:

        # Touch from wall (Only available for the player with active turn)
        if item.custom_id == "1":
            if not(game.player_turn == n):
                item.disabled = True

        # if its the active player's turn, they cant pass
        elif item.custom_id == "6":
            if game.player_turn == n:
                item.disabled = True

        # for each player, if move not available, disable the corresponding buttons
        else:
            if int(item.custom_id) not in move_table[n]:
                item.disabled = True  

    msg = await user.send(embed=player_embed, view=p_view)
    # wait until button is pressed
    await p_view.wait()

    return p_view.result


async def loading_bar(ctx):

    """
    Displays an animated loading bar in the channel.
    """
    
    # Loading bar
    message = await ctx.send("Loading...")
    total_steps = 20
    for i in range(total_steps + 1):
        progress = i / total_steps
        filled_blocks = int(progress * 10) # 10 blocks for the bar
        empty_blocks = 10 - filled_blocks
        
        # Using solid block character (U+2588) for filled part
        # and a lighter shade (U+2591) for empty part, or simple space
        bar = '█' * filled_blocks + '░' * empty_blocks
        percentage = int(progress * 100)
        
        await message.edit(content=f"Loading: [{bar}] {percentage}%")
        await asyncio.sleep(0.2) # Simulate work being done

    await message.edit(content="Let's Play Mahjong!")
    message.delete()


async def display_game_info(game:Game, i, user, hand_list, melded_list, fs_list):

    """
    Privately message the player the current state of the board
    Show the corresponding user their own tiles while hiding other user's tiles,
    show flower/ seasons and melded tiles to all players
    """
        
    embed = discord.Embed(title="Current game state",
                            description=f"Turn {len(game.players_moved)+1} \nPrevailing wind: {game.mjset['winds'][game.prevailing_wind]} \nTiles: {len(game.tiles)}", 
                            color=0x00ff00)
                            
    p: Player = game.players[i]

    # Add a table of prevailing wind etc
    for j in range(4):
        
        hand_string = ""
        # if the player is the messaged player, show their tiles
        if i == j:
            embed.add_field(name=f"{game.mjset['winds'][j]} *{user.name}*", value=f'> Hand: {hand_list[j]}\n> Melded: {melded_list[j]}\n> Flowers: {fs_list[j]}',inline=False)

        else:
            for n in range(len(p.player_hand)):
                hand_string += "█ "

            embed.add_field(name=f"{game.mjset['winds'][j]} {user.name}", value=f'> Hand: {hand_string}\n> Melded: {melded_list[j]}\n> Flowers: {fs_list[j]}',inline=False)
        
    # game info
    msg = await user.send(embed=embed)
    return msg


def generate_id():

    """
    Generate ID for games that do not take place in a channel
    """

    while True:

        random_int = str(random.randint(1, 9999))
        id = date.today().strftime("%Y%m%d") + random_int

        if id not in active_games.keys():
            return id


def discard_pile(game:Game):

    """
    Display all the discarded tiles 
    Indicate the previously discarded tile
    """
    discard_string = ""
    
    if len(game.discard_pile) == 0:

        discard_string = "There are no discarded tiles"
    else:

        for d in game.discard_pile:

            discard_string += f"{d[0]} "

    return discard_string


def game_info(game:Game):

    """
    Get the string of the melded tiles, flower/ seasons tiles and tiles in player hand
    """
    
    fs_list = []
    melded_list = []
    hand_list = []

    for n in range(4):
        
        # melded
        melded_string = ""
        p:Player = game.players[n]
        for meld in p.melded:

            if meld[1] == "暗杠":
                melded_string += "█ █ █ █ "
            
            elif meld[1] == "碰":
                for k in range(3):
                    melded_string += f"{meld[0][0]} "
            
            elif meld[1] == "明杠":
                for k in range(4):
                    melded_string += f"{meld[0][0]} "
            
            elif meld[1] == "吃":
                for tile in meld[0]:
                    melded_string += f"{tile[0]} "  
        
        melded_list.append(melded_string)   
        
        # flower/ seasons
        fs_string = ""
        p:Player = game.players[n]
        for f in p.player_flowers_seasons:
            fs_string += f"{f[0]} "

        fs_list.append(fs_string)
        
        # player hand
        hand_string = ""
        for tile in p.player_hand:
            hand_string += f"{tile[0]} "
        
        hand_list.append(hand_string)
        
    return hand_list, melded_list, fs_list


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
