from time import time
import random

import cards

class Game:
    '''
    A whole game of how many outs
    '''

    ''' if the guess value represents >=X '''
    GUESS_VALUE_GREATER = 15 

    ''' Number of outs a player can be off in either direction and still get points '''
    GUESS_MARGIN = 2

    ''' Percentage of points you get if you are within the margin '''
    POINT_PERCENT_MARGIN = .50

    ''' Number of rounds in a game '''
    ROUND_COUNT = 10

    ''' Starting max number of points you can get in a round before bonus '''
    ROUND_POINTS_START = 10000

    ''' Starting amount of time you get in seconds in a round '''
    ROUND_TIME_START = 75

    def __init__(self, id = 0):

        self._round_count = Game.ROUND_COUNT
        self._rounds = []

        self._score = 0
        self._multiplier = 1
        self._id = id

    def get_cur_round(self):
        '''
        @return current round being played
        '''

        a_round = None
        length = len(self._rounds)

        if (0 < length):
            a_round = self._rounds[length - 1]

        return a_round

    def end_round(self, guess):
        '''
        Ends the current round by registering the player's guess and adjusting
        the score and multiplier appropriately
        @param guess player's guess to the number of outs in the round
        '''
        a_round = self.get_cur_round()
        if (None != a_round):

            time_allowed = Game.ROUND_TIME_START
            points_possible = Game.ROUND_POINTS_START

            # adjust the players guess to the correct answer if they fit in the
            # >X territory
            if (guess == Game.GUESS_VALUE_GREATER and len(a_round.outs) >= Game.GUESS_VALUE_GREATER):
                guess = len(a_round.outs)
            
            # end the round.  if the player was perfect with the guess, give him
            # lots of points and increase the multiplier.  if the player was only slightly off, give him 
            # points but no additional multiplier.  if the player was way off, sad face
            a_round.end(guess)
            dist = a_round.guess_distance

            # calculate time passed for the round giving a little room for latency.
            # past the first round, more points are given the faster the guess
            # comes in
            time_passed = ((a_round.time_ended - .5) - a_round.time_started)
            time_passed = max(min(time_allowed, time_passed), 0)

            time_percent = 1
            if (1 < len(self._rounds)):
                time_percent = (time_allowed - time_passed) / time_allowed
            
            if (time_percent < 0):
                time_percent = 0 
       
            # perfect
            elif (0 == dist):
                
                a_round.points = int(round(points_possible * time_percent * self._multiplier))
                self._score += a_round.points
                self._multiplier += 1

            # within margin
            elif abs(dist) <= Game.GUESS_MARGIN:

                a_round.points = int(round(points_possible * time_percent * self._multiplier * .5))
                self._score += a_round.points

            # sad guess 
            else:

                a_round.points = 0
                self._multiplier = 1

            # if there are not any rounds remaining, end the game by putting an empty
            # round at the end
            if (0 >= self.rounds_remaining()):
                self._rounds.append(None)

                
    def new_round(self):
        '''
        Create a new hand/round in the game
        @return newly created round
        '''

        a_round = None

        if (0 < self.rounds_remaining()):

            # certain out scenarios (0,3,6) come up way more frequently when randomly 
            # generating a hand.  to achieve a slightly more  distributed number of outs for each round, 
            # if we hit when of the common cases, generate again
            iterations = 0
            again = True

            while (again):

                a_round = Round(len(self._rounds) + 1)

                # deal the player and number of opponents based on the multiplier
                opponents = 1
                if (6 <= self._multiplier):
                    opponents = 3
                elif (3 <= self._multiplier):
                    opponents = 2

                a_round.deal(opponents)

                # determine if we should try again 
                again = False
                iterations +=1                 
                if ((1 == opponents and len(a_round.outs) in [3, 6]  and iterations < 2)\
                 or (0 == len(a_round.outs) and iterations < 3)):
                    again = True

            self._rounds.append(a_round)
            
        return a_round

    def rounds_remaining(self):
        ''' Number of rounds remaining in the game '''
        return self._round_count - len(self._rounds)


    def get_points_possible(self):
        ''' Max number of points possible in the current round '''
        return int(Game.ROUND_POINTS_START * self._multiplier)

    def get_time_allowed(self):
        ''' Max amount of time in current round '''
        time_allowed = -1
        if (1 < len(self._rounds)):
            time_allowed = Game.ROUND_TIME_START

        return time_allowed 
        

    # PROPERTIES
    @property
    def id(self):
        return self._id

    @property
    def score(self):
        return self._score

    @property
    def multiplier(self):
        return self._multiplier

class Round:
    '''
    A round is a single hand with 1 player hand and X opponents hands. 
    '''

    def __init__(self, id):

        self._id = id

        self._deck = cards.Deck()
        self._board = None

        self._time_started = time()
        self._time_ended = None

        self._hand_player = None
        self._hand_opponents = None
        
        self._complete = False
        self._dealt = False

        self._outs = None
        self._draws = None
        self._ahead = None

        self._guess = None
        self._guess_distance = None

        self._points = None

    def deal(self, opponents):
        '''
        Deals hole cards to the player and to X opponents and 4 cards
        to the board.  Figures out if the player is ahead or behin:
        1) if the player is ahead, finds the outs the player has to lose
        2) if the player is behind, finds the outs the player has to win
        @param opponents number of opponent hands to deal
        '''

        # we can't deal twice
        if False != self._dealt:
            return

        # shuffle it up!
        self._dealt = True
        self._deck.shuffle()

        # deal out the player hand
        self._hand_player = cards.Hand(self._deck.deal(), self._deck.deal())

        # now for each opponent
        self._hand_opponents = []
        for i in range(0, opponents):
            hand = cards.Hand(self._deck.deal(), self._deck.deal())
            self._hand_opponents.append(hand)

        # now the four cards on the board
        self._board = []
        for i in range(0, 4):
            self._board.append(self._deck.deal())

        # figure out if the player is ahead or not after the turn
        self._ahead = self._calc_ahead()

        # calculate the number of outs the player or opponents have
        self._calc_outs()


    def end(self, guess):
        '''
        Ends the round with the player's guess to the number of outs he or his
        opponents have
        @param guess the player's guess to the number of outs he has to win/lose
        the hand
        '''

        # we can't end twice
        if False != self._complete:
            return

        self._guess = guess
        self._complete = True
        self._time_ended = time()

        # the number of outs compared to the guess
        self._guess_distance = self._guess - len(self._outs)


    def get_board(self):
        '''
        @return board of the round
        '''
        return self._board

    def get_hands(self):
        '''
        @return all the hands in the round in a list, with the players hand being the first element
        '''
        hands = [self._hand_player]
        hands.extend(self._hand_opponents)

        return hands


    #PROPERTIES
    @property
    def outs(self):
        return self._outs

    @property
    def ahead(self):
        return self._ahead
    
    @property
    def draws(self):
        return self._draws        

    @property
    def guess(self):
        return self._guess

    @property
    def guess_distance(self):
        return self._guess_distance

    @property
    def id(self):
        return self._id

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        self._points = value

    @property
    def time_started(self):
        return self._time_started

    @property
    def time_ended(self):
        return self._time_ended

    #PRIVATE

    def _calc_ahead(self):
        '''
        calc if the player is ahead/tied/behind in the hand compared to
        the opponents
        @return <0 if behind, 0 on tie, 1 if ahead
        '''
        comp = False
        self._hand_player.make(self._board)
        for hand in self._hand_opponents:

            hand.make(self._board)

            # as soon as the player's hand loses against an opponent we be out
            temp = self._hand_player.compare(hand)
            hand.reset()

            if (False == comp or temp < comp):
                comp = temp

        if (1 < comp):
            comp = 1
        elif (-1 > comp):
            comp = -1        

        self._hand_player.reset()

        return comp

    def _calc_outs(self):
        '''
        calc the number of outs the player has to win/lose the hand
        '''

        self._outs = []
        self._draws = self._deck.remaining()

        # go through each remaining card in the deck:
        # 1) add the card to the board
        # 2) make all hands with the full board
        # 3) compare all hands, add an out appropriately
        # 4) remove the card from the board
        while(None != self._deck.deal()):

            # 1
            self._board.append(self._deck.last)

            # 2, # 3
            ahead = self._calc_ahead()
            if ((0 <= self._ahead and 0 > ahead) 
             or (0 > self._ahead and  0 <= ahead)):
                self._outs.append(self._deck.last)

            # 4
            self._board.pop()

        self._outs.sort(cards.compare_card_all)



if __name__ == "__main__":

    '''
    A console verison of how many outs!
    '''

    game = Game()
    while (0 < game.rounds_remaining()):

        # start a new round
        game.new_round()
        round = game.get_cur_round()

        # output the game state
        print '\nT' + str(game.rounds_remaining()) + ' S' + str(game.score) + ' R' + str(game.multiplier)

        # output each of the hands
        hands = round.get_hands()

        print '\nYour hand:'
        print hands[0].to_string()

        combined = ''
        for hand in hands[1:]:
            combined += hand.to_string() + ' '

        print '\nOpponents:'
        print combined

        # output the board

        combined = ''
        for card in round.get_board():
             combined += card.to_string() + ' '

        print '\nThe board:'
        print combined

        print '\nTemp:'
        print 'O?' + str(len(round.outs)) + ' A?' + str(round.ahead)
        combined = ''
        for card in round.outs:
            combined += card.to_string() + ' '
        print combined

        # get the player's guess
        print '\n'
        guess = raw_input(">")

        try:
            guess = int(guess)
        except:
            guess = 0

        # end the round!
        game.end_round(guess)






