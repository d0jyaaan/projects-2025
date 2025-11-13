import random
import pprint
import copy
import math

BOLD = '\033[1m'
END = '\033[0m'

def main(): 

    # {"suits" : ["筒", "索", "萬"],
    #        "winds" : ["東", "南", "西", "北"],
    #        "dragons" : ["中", "發", "白"],
    #        "flowers": ["梅","蘭","竹","菊"],
    #        "seasons": ["春","夏","秋","冬"]}

    game = Game()

    game.players[0].player_hand = [("1筒", "suits"), ("1筒", "suits"),("1筒", "suits"),
                                   ("白", "dragons"),("白", "dragons"), ("白", "dragons"),
                                   ("發", "dragons"),("發", "dragons"), ("發", "dragons"),
                                   ("北", "winds"), ("北", "winds"), ("北", "winds"),
                                   ("中", "dragons"),("中", "dragons")]
    game.players[0].melded = []
    
    w = game.check_winning_type(0)
    for s in w:
        print(s)
    # game.run()
    

class Player():

    """
    Class handling player profile including :

        - Current hand
        - Completed sets ( Pung / Concealed or Revealed Kong / Chow)
        - Flowers / Seasons
        - Faan / Bonus faans
    """
    
    def __init__(self, i):
        
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
        
        
    def evaluate_hand(self, table):

        pass
        

    # must make a function to check for the final point when a player wins 
    # player_points is mainly used for reference of the player themselves
    

class Game():

    """
    Class handling all of the game's logic 
    """
    # player turn
    player_turn = 0

    # flag for touch from wall
    flag_wall = False

    # number of players 
    player_count = 4

    # generate list containing n(player_count) of Player() object
    players = [Player(i) for i in range(player_count)]

    # mahjong sets 
    mjset = {"suits" : ["筒", "索", "萬"],
           "winds" : ["東", "南", "西", "北"],
           "dragons" : ["中", "發", "白"],
           "flowers": ["梅","蘭","竹","菊"],
           "seasons": ["春","夏","秋","冬"]}
    
    # all the available tiles still on the board
    # each tile is a pair : (tile, type)
    tiles = []
    
    # discard pile
    discard_pile = []

    # evaluation table
    move_table = [[], [], [], []]

    # tile_table
    tile_table = []

    prevailing_wind = 0
    players_moved = []
    
    w_hand = []
    w_special = None
    prevailing_track = []

    hand_values = {
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
        "十八羅漢": 13
    }

    def run(self):

        """
        Runs the game and updates it until someone wins or the game ends
        """

        """
        initialise the game by doing the following processes:
            - generate tiles and shuffle 
            - assign players their number and their hand
            - check for flowers and seasons
            - add the bonus points for each player until each player has no flowers left
        """
        self.initialise()
        
        # main loop for game
        while True:
            
            self.print_display_h()
            
            # if first round and first player(house) must throw away a tile
            if not(self.player_turn == 0 and len(self.players_moved) == 0):

                # TODO since this app is 1 player vs 3 computer, the parameter for self.get_input will just be the human player's number
                self.evaluate_moves()

                # select which player wants to move
                p = self.player_turn
                while True:
                    
                    try:
                        
                        p = int(input("Which player wants to move? (1-4) \n")) - 1
                        
                        # cant select from previous player
                        if not(p == self.players_moved[-1]):
                            # if its not the intended player's turn and the player that cuts in has valid moves

                            self.print_display_h()
                            if (p >=0 and p <= 3):

                                if not(p == self.player_turn) and (len(self.move_table[p]) >= 1):

                                    print(f"Player {p + 1}'s turn \n" )
                                    if self.get_input(p):
                                        if not(p == self.player_turn):
                                            self.player_turn == p
                                        break

                                    else:
                                        self.print_display_h()
                                        print("Invalid move!")  

                                elif (p >=0 and p <= 3):
                                    
                                    if not(p == self.player_turn):
                                        self.print_display_h()
                                        print("No valid moves!")  
                                    else:
                                        print(f"Player {p + 1}'s turn \n" )
                                        if self.get_input(p):
                                            pass

                            else:
                                print("Invalid Player Number (1-4)")
                        else:
                            print(f"Player {p+1} cannot move this round!")
                    
                    except ValueError and TypeError:
    
                        pass

            else:
                # player 1 can choose whether they want to concealed kong or not
                # if u dont concealed kong, then dont count it as a kong even if player can win since could be pong + chow
                # otherwise player 1 can throw away a tile
                self.get_input_self_touch(self.player_turn, [])
                
            # keep track of which player has moved for this round of wind
            # if all 4 players have moved, change to the next wind
            self.players_moved.append(self.player_turn)

            # calculate the faan of the player that just moved
            self.players[self.player_turn].player_faan = self.players[self.player_turn].fs_faan + self.calc_hand_faan(self.player_turn)[0]

            if len(self.prevailing_track) == 4:
                
                self.prevailing_wind = (self.prevailing_wind + 1) % 4
                self.prevailing_track = []
                
            # how to handle throwing out tiles / taking tiles / win
            self.update_state()
            
            # if run out of tiles, game resets and follow the same order
            if len(self.tiles) == 0:
                # TODO
                # when player ends their move, update their personal eval table
                pass
            
            break

    # <Start> Evaluation functions </Start>
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


    def evaluate_table(self, n):

        """
        Evaluate a player's hand by assigning count to each tile on player hand
        """

        for tile in self.players[n].player_hand:

            if tile[1] == "suits":
                
                self.tile_table[n][tile[1]][tile[0][-1]][int(tile[0][0])-1] += 1

            elif tile[1] == "dragons" or tile[1] == "winds":

                self.tile_table[n][tile[1]][tile[0][-1]] += 1


    def evaluate_moves(self):

        """
        For each game state, evaluate each player's hand and add the legal actions (碰, 杠, 吃, 胡) into a list
        """

        self.move_table = [[], [], [], []]

        if not (len(self.discard_pile) == 0):
            d = self.discard_pile[-1]
            for index in range(0, 4):
                if self.check_pong(index, d):
                    self.move_table[index].append(2)
                if self.check_kong(index, d):
                    self.move_table[index].append(3)
                if self.check_chow(index, d) is not None:
                    self.move_table[index].append(4)
                if self.check_hu(index):
                    self.move_table[index].append(5)
            

    def calc_hand_faan(self, melded, n):

        """
        Calculate the faan of a players current hand
        1) Melded tiles
        2) Flowers in the player's hand

        Pong 碰   
            Dragon - 1 point
            own wind - 1 point, 0 otherwise
            suits - 0 point
        
        Kong 杠
        Concealed 暗杠
            1 point if suits
            1 points if not own seat wind
            2 points if dragon / own seat wind
        Revealed 明杠
            1 point if suits
            2 points


        Chow 吃 - No points (only suits)
        """
        n_dragons = 0
        n_winds = 0
        n_pongs = 0
        n_kongs = 0
        n_chow = 0
        n_suits = 0
        n_ckongs = 0

        # reset player faan before recalculating
        faan = 0

        for meld in melded:
            
            # pong
            if meld[1] == "碰":
                # winds / prevailing wind scoring
                if meld[0][1] == 'winds':

                    if meld[2]:
                        faan += 1

                    if meld[0][0] == self.mjset['winds'][n]:
                        faan += 1
                    
                    n_winds += 1
                
                elif meld[0][1] == "dragons":
                    faan += 1
                    n_dragons += 1
                
                elif meld[0][1] == "suits":
                    n_suits += 1

                n_pongs += 1

            # kong
            elif meld[1] == "暗杠" or meld[1] == "明杠":
                                    
                faan += 1

                if meld[1] == "暗杠":
                    n_ckongs += 1
                    faan += 1

                n_kongs += 1

                if meld[0][1] == "dragons":
                    faan += 1
                    n_dragons += 1

                elif meld[0][1] == "winds":

                    if meld[2]:
                        faan += 1

                    if meld[0][0] == self.mjset['winds'][n]:
                        faan += 1

                    n_winds += 1

                elif meld[0][1] == "suits":
                    n_suits += 1

            # chow
            elif meld[1] == "吃":
                n_chow += 1

        return [faan, n_pongs, n_kongs, n_chow, n_suits, n_winds, n_dragons, n_ckongs]
    

    def calc_fs_faan(self, n):
        """
        Based on the flower of a player's hand, return the number of faan the player has
        """
        faan = 0
        for tile in self.players[n].player_flowers_seasons:

            if self.mjset[tile[1]][n] == tile[0]:
                faan += 1
            
        return faan
    # <End> Evaluation functions </End>
    
    
    # <Start> check functions </Start>
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
    

    def check_c_kang(self, n):

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


    def check_hu(self, n):
        
        """
        Ensure player has enough faan to win
        Calculate the faan of the player's hand according to winning type
        """

        # function returns whether there is a winning hand or not
        b = self.check_winning_type(n)
        if b:
            pass

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
            return (None,"花糊", self.hand_values["花糊"])
        
        # 8 Flowers (八仙過海)
        elif len(self.players[n].player_flowers_seasons) == 8:

            return (None,"八仙過海", self.hand_values["八仙過海"])    
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
        if len(winning_hand) == 0 and len(self.players[n].player_hand) == 14:
            
            # Seven Pairs (七對子) - ignore 4 of the same tiles
            # hand contains 7 pairs
            pairs = 0
            for d in distinct:
                if self.players[n].player_hand.count(d) == 2:
                    pairs += 1
            
            if pairs == 7:
                # return the 7 distinct type of tiles
                return (distinct ,"七對子", self.hand_values["七對子"])
            
            # Nine Gates (九子連環)
            # eg: 1112345678999 + any of the 9 same suited tile
            self.players[n].player_hand.sort()
            temp_hand = copy.deepcopy(self.players[n].player_hand)

            for suit in self.mjset["suits"]:

                if (f'1{suit}', 'suits') in temp_hand and (f'9{suit}', 'suits') in temp_hand:

                    if (temp_hand.count((f'1{suit}', 'suits')) == 3 or temp_hand.count((f'1{suit}', 'suits')) == 4) and (temp_hand.count(f'9{suit}', 'suits') == 3 or temp_hand.count(f'9{suit}', 'suits') == 4):
                        
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
            
            # # Blessing of Heaven (天糊) - Win on the first turn as the dealer
            # # since scores limit, doesnt matter what hand the player gets as long as its valid win 
            # if len(self.players_moved) == 0:
            #     return (winning_hand[0], "天糊", self.hand_values["天糊"])
            
            # # Blessing of Earth (地糊) - Win on the dealer’s first discard
            # if len(self.players_moved) == 1:
            #     return (winning_hand[0], "地糊", self.hand_values["地糊"])
            
            # # Blessing of Man (人糊) - Win on the first turn as non-dealer
            # if n not in self.players_moved:
            #     return (winning_hand[0], "人糊", self.hand_values["人糊"])
            

            # return [0faan, 1n_pongs, 2n_kongs, 3n_chow, 4n_suits, 5n_winds, 6n_dragons, 7n_ckongs]
            
            # note: the pair of eyes will be at the last index of the w list
            hand_faan = []
            for w in winning_hand:
                
                f = self.calc_hand_faan(w, n)
                print(f)
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

                # Mixed Flush (混一色) - Only tiles of a single suit plus honor tiles 
                if n_same_suits == 3 and f[4] == 3 and (f[5] == 1 or f[6] == 1):
                    if (f[1] + f[2] == 4): 
                        hand_faan.append((w, "混一色", min(self.hand_values["混一色"] + f[0] + self.hand_values["碰碰糊"], 13))) 
                    else:
                        hand_faan.append((w, "混一色", min(self.hand_values["混一色"] + f[0], 13))) 

                # Pure Flush (清一色) - Only tiles of a single suit
                if n_same_suits == 4 and f[4] == 4:
                    if (f[1] + f[2] == 4): 
                        hand_faan.append((w, "清一色", min(self.hand_values["清一色"] + f[0] + self.hand_values["碰碰糊"], 13))) 
                    else:
                        hand_faan.append((w, "清一色", min(self.hand_values["清一色"] + f[0], 13))) 

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
                # 



                # TODO 七对子类

            return hand_faan                
    


    # <End> check functions </End>

    
    # <Start> Input functions </Start>
    def get_input(self, n):

        """
        Get input from user for a certain state on the board

        Check whether the following input is valid or not:
            
            1) Touch from wall 自摸 (no special conditions, so just return)
            2) Pong 碰 (Hand must have 2 tiles of the same 'type' as the discarded tile  on board)
            3) Kong 杠 (Hand must have 3 tiles of the same 'type' as the discarded tile on board)
            4) Chow 吃 (Hand must have 2 or more successive tiles which can be succeeded or preceeded by the discarded tile)
            5) Hu 胡 (Only valid if player has won. Refer to win_state() function for win conditions)
        
        If not valid, reprompt the user

        Return the input from user
        """
        i = 0
        
        print("1:| 自摸  2:| 碰  3:| 杠  4:| 吃  5:| 胡 ")

        while not(1 <= i <= 5):

            try:

                i = int(input("Input : "))
                # touch from wall 自摸 (only valid for the current player's turn)
                if (i == 1 and n == self.player_turn):
                    
                    wall_tile = self.tiles.pop()
                    self.players[n].player_hand.append(wall_tile)
                    self.players[n].player_hand.sort(key=lambda x: (x[0][-1:], x[0]))

                    self.flag_wall = True
                    # reprint player hand with 1 more extra tiles
                    self.print_display_h()
                    self.get_input_self_touch(n, wall_tile)

                # valid for all players (stealing tiles from discard)
                elif (2 <= i <= 4):

                    if not(len(self.discard_pile) == 0):

                        # pong 碰
                        if i==2 and i in self.move_table[n]:
                            
                            # remove the pong tiles from player hand
                            d = self.discard_pile[-1]
                            for l in range(2):
                                self.players[n].player_hand.remove(d)

                            # player can also pong if they have 3 tiles already in their hand instead of kong
                            if self.players[n].player_hand.count(d) == 3:

                                self.players[n].player_hand.append(d)

                            
                            # if the pong is wind tile, and matching the prevailing wind, + 1 faan
                            if d[1] == 'winds' and self.mjset["winds"][self.prevailing_wind] == d[0]:
                                self.players[n].melded.append((d, "碰", True))
                                
                            else:
                                self.players[n].melded.append((d, "碰", False))

                            self.discard_pile.pop()
                            self.print_display_h()
                            self.throw_tile(n)
                            self.action_history.append(i)
                            return True
                            
                        # kong 杠 
                        elif i == 3 and i in self.move_table[n]:
                            
                            d = self.discard_pile[-1]
                            # check whether is it possible to kong
                            if self.players[n].player_hand.count(d) == 3:
                                
                                # remove the kong tiles from player hand
                                list(filter((d).__ne__, self.players[n].player_hand))

                                if d[1] == 'winds' and self.mjset["winds"][self.prevailing_wind] == d[0]:
                                    self.players[n].melded.append((d, "明杠", True))
                                else:
                                    self.players[n].melded.append((d, "明杠", False))

                            # forming exposed kong from exposed pong if player draws from hand
                            elif (d, "碰", True) in self.players[n].melded:
    
                                self.players[n].melded.remove((d, "碰", True))
                                self.players[n].melded.append((d, "明杠", True))
                                

                            elif (d, "碰", False) in self.players[n].melded:
                                
                                self.players[n].melded.remove((d, "碰", False))
                                self.players[n].melded.append((d, "明杠", False))


                            self.discard_pile.pop()
                            self.print_display_h()
                            self.replace_tile(n)
                            self.throw_tile(n)
                            self.action_history.append(i)
                            return True
                            
                        # chow 吃 
                        elif  i == 4 and i in self.move_table[n]:
                            
                            d = self.discard_pile[-1]
                            r = self.check_chow(n, d)

                            if r is not None:
                            
                                straights = r
                                # choose which straight would u like to chow
                                for index_, s in enumerate(straights):
                                    
                                    print(f"{index_+1}:| ", end="")
                                    for t in s:
                                        print(t[0] + " ", end="")

                                print("\n")
                                    
                                # get input from user to determine which straight the user wants to form
                                u_input = 0
                                while not(1 <= u_input <= len(straights)):

                                    try: 
                                        u_input = int(input("Which straight to form : "))

                                    except TypeError and ValueError:
                                        pass
                                
                                # remove the chow tiles
                                for element in straights[u_input-1]: 
                                    
                                    if not(element == self.discard_pile[-1]):
                                        self.players[n].player_hand.remove(element)
                                
                                self.players[n].melded.append((straights[u_input-1], "吃"))
                                self.discard_pile.pop()
                                self.print_display_h()
                                self.throw_tile(n)
                                
                                return True
                            
                        # hu 胡
                        # TODO
                        # 
                        elif i == 5:
                            pass

                        return False

            except ValueError:
                pass
            
            i = 0


    def get_input_self_touch(self,n, wall_tile):
        
        """
        When first round and is player 1's turn or player 自摸, player has to either:

            1) Throw away tile
            2) 暗杠

        Handles the logic for 暗杠 :
            - Remove tile from player's hand and add to melded
            - Take 1 tile from wall
            - Throw out 1 tile
        """
        
        if len(self.players_moved) != 0:
            print(f"{wall_tile[0]} was obtained")

        
        u_input = 0

        while not(1 <= u_input <= 2):

            print("1:| Throw tile  2:| 暗杠  3:| 胡")
            try:
                
                u_input = int(input("Input : "))
                # throw away tile from current hand
                if u_input == 1:
                    self.throw_tile(n)
                    return 
                
                # 杠 if available
                elif u_input == 2 and self.check_c_kang(n):
                    
                    available = []
                    for tile in set(self.players[n].player_hand):
                        
                        # get all the available options for concealed 杠
                        if self.players[n].player_hand.count(tile) == 4:

                            available.append(tile)

                    # display the options available to be concealed 杠
                    print("杠 options : ", end="")
                    for kong_options_index in range(len(available)):
                        print(f"{kong_options_index + 1}:| {available[kong_options_index][0]} ", end="")
                    print("\n")

                    # choose the tile to be 杠
                    u_input_kong = -10000 
                    while not(1 <= u_input_kong <= len(available)):

                        try:
                            u_input_kong = int(input("Which tile to 杠 : "))

                        except TypeError and ValueError:
                            pass
                    
                    if available[u_input_kong-1][1] == 'winds' and self.mjset["winds"][self.prevailing_wind] == available[u_input_kong-1][0]:
                        self.players[n].melded.append((available[u_input_kong-1], "暗杠", True))
                    else:
                        self.players[n].melded.append((available[u_input_kong-1], "暗杠", False))

                    # remove 杠 tiles from hand
                    self.players[n].player_hand = list(filter((available[u_input_kong-1]).__ne__, self.players[n].player_hand))
                    self.players[n].player_hand.sort(key=lambda x: (x[0][-1:], x[0]))

                    replace_tile = self.tiles.pop()
                    self.players[n].player_hand.append(replace_tile)

                
                elif u_input == 3 and self.check_hu(n):
                    pass 

                u_input = 0
                self.print_display_h()

            except TypeError and ValueError:
                pass
    # <End> Input functions </End>


    # <Start> Display </Start>
    def print_display_h_ai(self):

        """
        Handles the GUI for user vs computer
        """
        pass
    
    
    def print_display_h(self):

        """
        Handles the GUI for player vs player mode
        Handles the GUI of the game by displaying:
            1) All player hands and their flowers/seasons
            2) What tiles have been thrown out on the board
        """

        # clear
        print(chr(27) + "[2J")
        
        for p in self.players:

            print(f"{BOLD}Player {p.player_number+1} {END}")
            for tile in p.player_hand:

                print(f"{tile[0]} ", end="")

            print("\n", end="")

            # show flower tiles
            print("Flowers |: ", end="")
            for j in p.player_flowers_seasons:
                print(f"{j[0]} ", end="")

            print("\n", end="")

            # show melded tiles
            print("Melded |: ", end="")
            for j in p.melded:

                if j[1] == "暗杠":
                    print("█ █ █ █ ", end="")
                
                elif j[1] == "碰":
                    print(f"{j[0][0]} {j[0][0]} {j[0][0]} " ,end="")
                
                elif j[1] == "明杠":
                    print(f"{j[0][0]} {j[0][0]} {j[0][0]} {j[0][0]} " ,end="")
                
                elif j[1] == "吃":

                    for k in j[0]:
                        print(f"{k} ", end="")

            print("\n")

        print(f"Number of tiles left : {len(self.tiles)} \n")
        
        print("Discard pile")

        for discarded in self.discard_pile:
            print(f"{discarded[0]} ", end="")
        print("\n")
        
        if len(self.discard_pile) != 0 and not self.flag_wall:
            print(f"{self.discard_pile[-1][0]} was discarded previously")
    # <End> Display </End>


    def throw_tile(self, n):

        """
        Get input from user to choose which tile to throw away from current hand (1 - 14)
        Reprompt if invalid 
        """
        
        i = 0
        # prompt user for input
        # reprompt if user input is not a number within 1 -> no of tiles in hand
        while not(1<= i <=len(self.players[n].player_hand)+ 1):
            try :
                i = int(input(f"Throw away a tile (1-{len(self.players[n].player_hand)}): "))

            except ValueError:
                pass
        # remove tile from hand
        removed = self.players[n].player_hand.pop(i-1)
        # add removed tile to discard pile
        self.discard_pile.append(removed)


    def update_state(self):

        """
        Update the game state after move is finished 
        given that Pong / Kong / Chow didnt occur
        If pong / kong / chow occurs, 
        player turn = player that pong / kong / chow
        """

        self.player_turn = (self.player_turn + 1 ) % 4
        

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


if __name__ == "__main__":

    main()