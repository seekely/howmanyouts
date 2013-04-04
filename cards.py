import random

'''
Compares two cards by rank
@param card1
@param card2
@return >= 1 if card1 is greater, <= -1 if card2 is greater, 0 if equal
'''
def compare_card_rank(card1, card2):
    return card1.rank - card2.rank

'''
Compares two cards first by suit then by rank
@param card1
@param card2
@return >= 1 if card1 is greater, <= -1 if card2 is greater, 0 if equal
'''
def compare_card_suit(card1, card2):

    comp = card1.suit - card2.suit
    if (0 == comp):
        comp = compare_card_rank(card1, card2)

    return comp

''' 
Compares two cards first by rank then by suit
@param card1
@param card2
@return >=1 if card1 is greater, <= -1 if card2 is greater, 0 if equal
'''
def compare_card_all(card1, card2):

    comp = card1.rank - card2.rank    
    if (0 == comp):
        comp = card1.suit - card2.suit

    return comp


'''
Compares two hands by rank
@param hand1
@param hand2
@return >= 1 if hand1 is greater, <= -1 if hand2 is greater, 0 if equal
'''
def compare_hand_rank(hand1, hand2):
    return hand1.compare(hand2)


class Card:
    '''Individual card in a deck'''

    '''Ranks for cards higher than 10'''
    RANK_ACE        = 14
    RANK_KING       = 13
    RANK_QUEEN      = 12
    RANK_JACK       = 11

    '''Suits for each card'''
    SUIT_HEART      = 0
    SUIT_SPADE      = 1
    SUIT_DIAMOND    = 2
    SUIT_CLUB       = 3

    '''Creates a new card given a value between 0:52'''
    def __init__(self, value, rank = None, suit = None):

        if (None != rank and None != suit):
            self._rank = rank
            self._suit = suit
        else:
            self._rank = ((value % Deck.CARD_COUNT) % Deck.RANK_COUNT) + 2
            self._suit = value % Deck.SUIT_COUNT


    def to_string(self):

        map_rank = {Card.RANK_ACE   : 'A'
                  , Card.RANK_KING  : 'K'
                  , Card.RANK_QUEEN : 'Q'
                  , Card.RANK_JACK  : 'J'}

        map_suit = {Card.SUIT_HEART     : 'h'
                  , Card.SUIT_DIAMOND   : 'd'
                  , Card.SUIT_SPADE     : 's'
                  , Card.SUIT_CLUB      : 'c'}

        ret = ''
        if (self.rank < Card.RANK_JACK):
            ret += str(self.rank)
        else:
            ret += map_rank[self.rank]

        ret += map_suit[self.suit]

        return ret


    @property
    def rank(self):
        return self._rank

    @property
    def suit(self):
        return self._suit



class Deck:
    '''
    Standard deck of cards
    '''

    ''' number of suits in a deck of cards'''
    SUIT_COUNT = 4

    ''' number of cards in a deck'''
    CARD_COUNT = 52

    ''' number of cards in a suit'''
    RANK_COUNT = 13


    def __init__(self):
        '''
        Constructs a new unshuffled deck of cards
        '''
        self._cards = []
        self._next = 0
        self._last = None

        for i in range(0, Deck.CARD_COUNT):
            self._cards.append(Card(i))

    '''
    Randomly shuffles the deck
    '''
    def shuffle(self):
        self._next = 0
        random.shuffle(self._cards)

    '''
    Deals a card off the top of the deck
    @return a card from the deck or None if no cards remain
    '''
    def deal(self):

        to_deal = None
        if (self._next < Deck.CARD_COUNT):
            to_deal = self._cards[self._next]
            self._next += 1

        self._last = to_deal
        return to_deal

    def remaining(self):
        '''
        @return number of cards remaining in the deck
        '''
        return Deck.CARD_COUNT - self._next

    @property
    def last(self):
        return self._last

class Hand:
    '''
    A poker hand consisting made up of hole cards
    '''
    
    ''' Hand rankings constants, from highest to lowest '''
    RANKING_5_OF_A_KIND     = 10
    RANKING_ROYAL_FLUSH     = 9
    RANKING_STRAIGHT_FLUSH  = 8
    RANKING_4_OF_A_KIND     = 7
    RANKING_FULL_HOUSE      = 6
    RANKING_FLUSH           = 5
    RANKING_STRAIGHT        = 4
    RANKING_3_OF_A_KIND     = 3
    RANKING_2_PAIR          = 2
    RANKING_PAIR            = 1
    RANKING_HIGH_CARD       = 0


    def __init__(self, hole_card1, hole_card2):
        '''
        Constructs a new hand with two hole cards
        @param hole_card1 first hold card
        @param hole_card2 second hole card
        '''
        self._hole = [hole_card1, hole_card2]
        self._made = None
        self._rank = None



    def compare(self, hand):
        '''
        Compares the rank of this hand against the passed in hand.

        @param hand passed hand to compare to this hand
        @return >= 1 if this hand is higher, 0 if they are equal, and <= -1
        if the passed hand is higher
        '''

        # compare the rank, if the ranks match, compare individual
        # cards until one is greater than the other
        if (None == hand or None == hand._rank ):
            comp = 1
        elif (None == self._rank):
            comp = -1
        else:
            comp = self._rank - hand.rank
            if (0 == comp):
                for i in range(0, 5):
                    comp = compare_card_rank(self._made[i], hand.made[i])
                    if (0 != comp):
                        break

        return comp


    def make(self, board):
        '''
        Adds the board cards to the hole cards and then constructs the best
        five card hand possible.  Stores the made hand and rank.
        @param board list of community/board cards (i.e. the flop/turn/river)
        '''
        combined = self._hole[:]
        combined.extend(board)
        combined.sort(compare_card_rank, reverse=True)
        made = self._make_royal_flush(combined[:])     \
            or self._make_straight_flush(combined[:])  \
            or self._make_kind(4, combined[:])         \
            or self._make_full_house(combined[:])      \
            or self._make_flush(combined[:])           \
            or self._make_straight(combined[:])        \
            or self._make_kind(3, combined[:])         \
            or self._make_two_pair(combined[:])        \
            or self._make_kind(2, combined[:])         \
            or self._make_kind(1, combined[:])

        self._rank = made[0]
        self._made = made[1]

    def reset(self):
        '''
        Sets any made hand and rank back to empty, restoring the hand to just
        hole cards
        '''
        self._rank = None
        self._made = None

    def to_string(self):

        ret = ''
        comma = False
        if (None != self._made):
            for card in self._made:
                if (comma):
                    ret += ','

                ret += card.to_string()
                comma = True
        else:
            for card in self._hole:
                if (comma):
                    ret += ','
                
                ret += card.to_string()
                comma = True


        return ret

    # PROPERTIES

    @property
    def hole(self):
        return self._hole

    @property
    def made(self):
        return self._made

    @property
    def rank(self):
        return self._rank


    # PRIVATE METHODS


    def _make_royal_flush(self, combined):
        '''
        Looks for a royal flush amongst a list of cards
        @param combined list of combined hole cards and board cards
        @return rank of hand and list of the cards making a royal flush if found, False otherwise
        '''
        found = self._make_straight_flush(combined)
        if (False == found or Card.RANK_ACE != found[1][0].rank):
            found = False
        else:
            found = [Hand.RANKING_ROYAL_FLUSH, found[1]]

        return found

    def _make_straight_flush(self, combined):
        '''
        Looks for a straight flush amongst a list of cards
        @param combined ordered list of combined hole cards and board cards
        @return rank of hand and list of the cards making a straight flush if found, False otherwise
        '''
        found = self._make_straight(combined, True)
        return False if False == found else [Hand.RANKING_STRAIGHT_FLUSH, found[1]]

    def _make_full_house(self, combined):
        '''
        Looks for a full house amongst a list of cards
        @param combined ordered list of combined hole cards and board cards
        @return rank of hand and list of the cards making a full house if found, False otherwise
        '''
        found = self._make_two_pair(combined, True)
        return False if False == found else [Hand.RANKING_FULL_HOUSE, found[1]]

    def _make_flush(self, combined):
        '''
        Looks for a flush amongst a list of cards
        @param combined ordered list of combined hole cards and board cards
        @return rank of hand and list of the cards making a flush if found, False otherwise
        '''

        # order cards by suit first before finding matching kinds
        combined.sort(compare_card_suit,reverse=True)

        found = self._make_kind(5, combined, True)
        return False if False == found else [Hand.RANKING_FLUSH, found[1]]

    def _make_straight(self, combined, check_flush = False):
        '''
        Looks for a straight amongst a list of cards
        @param combined ordered list of combined hole cards and board cards
        @param check_flush optional parameter to check for a flush with the straight, defaults to false
        @return rank of hand and list of the cards making a straight if found, False otherwise
        '''
        found = False

        # pick each card in the combined list as a starting point
        for i in range(0, len(combined)):

            # dupe and append all Aces to the end of the combined card list since they can be
            # at the top or bottom of a straight
            if (Card.RANK_ACE == combined[i].rank):
                combined.append(combined[i])

            placed = 0
            looking = [combined[i]]

            # look at the remaining cards
            for j in range(i + 1, len(combined)):
                last = looking[placed]
                new = combined[j]

                # if this is the next card in the straight sequence (or straight flush when true == check_flush)
                # note we make an exception for aces following 2s since an ace can
                # be at the bottom of a straight
                if ((False == check_flush or last.suit == new.suit)
                and ((1 == last.rank - new.rank)
                  or (2 == last.rank and Card.RANK_ACE == new.rank))):
                    looking.append(new)
                    placed += 1

                # if we have 5 cards, then we have a straight!
                if (5 == len(looking)):
                    found = looking[:]
                    break
            
            if (False != found):
                break

        return False if False == found else [Hand.RANKING_STRAIGHT, found]

    def _make_kind(self, count, combined, check_flush = False):
        '''
        Looks for <count> number of cards of the same rank or suit amongst a list of cards
        @param count look for <count> of a kind
        @param combined ordered list of combined hole cards and board cards
        @return rank of hand and list of the cards making a <count> of kind if found, False otherwise
        '''
        found = False
        rankings = {1 : Hand.RANKING_HIGH_CARD
                  , 2 : Hand.RANKING_PAIR
                  , 3 : Hand.RANKING_3_OF_A_KIND
                  , 4 : Hand.RANKING_4_OF_A_KIND
                  , 5 : Hand.RANKING_5_OF_A_KIND}

        looking = []
        leftovers = []
        for card in combined:

            if (False == found):

                # append cards to a looking list as long as it matches the previous
                # card
                if (0 == len(looking)
                or (False == check_flush and card.rank == looking[0].rank)
                or (False != check_flush and card.suit == looking[0].suit)):
                    looking.append(card)
                else:
                    leftovers.extend(looking)
                    looking = [card]

                # if cur matches count, we have X kind
                if (len(looking) == count):
                    found = looking[:]

            else:
                leftovers.append(card)

        # append cards from the leftover until we have 5 cards
        if (False != found):
            found.extend(leftovers)
            found = found[0:5]

        return False if False == found else [rankings[count], found]

    def _make_two_pair(self, combined, check_full = False):
        '''
        Looks for two pair amongst a list of cards
        @param combined ordered list of combined hole cards and board cards
        @param check_full optional parameter to check for full house instead of 2 pair
        @return rank of hand and list of the cards making two pair if found, False otherwise
        '''
        found = False

        count_kind1 = 2
        count_kind2 = 2
        if (check_full):
            count_kind1 = 3

        # first try to make higher of a kind
        kind1 = self._make_kind(count_kind1, combined[:])

        # if we have a kind, remove anything matching the rank of the kind
        # then look for the second of a kind
        if (False != kind1):

            remove_rank = kind1[1][0].rank
            for card in combined[:]:
                if (remove_rank == card.rank):
                    combined.remove(card)

            kind2 = self._make_kind(count_kind2, combined[:])

            # if we have both kinds, combine it up!
            if (False != kind2):
                total = 5 - count_kind1
                found = kind1[1][0:count_kind1]
                found.extend(kind2[1][0:total])

        return False if False == found else [Hand.RANKING_2_PAIR, found]


if __name__ == "__main__":

    # make sure the deck is coooolio
    deck = Deck()
    deck.shuffle()

    count = 0
    while (None != deck.deal()):
        count += 1

    print '0 ' + str(count == Deck.CARD_COUNT)

    # testing royal flush
    hole1 = Card(0, 14, 1)
    hole2 = Card(0, 13, 1)
    combined = [Card(0, 12, 0), Card(0, 12, 1), Card(0, 11, 1), Card(0, 5, 0), Card(0, 10, 1)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '1 ' + str(Hand.RANKING_ROYAL_FLUSH == hand.rank) + ' ' + str(Card.RANK_ACE == hand.made[0].rank)

    # testing for a straight forward straight flush
    hole1 = Card(0, 2, 0)
    hole2 = Card(0, 3, 0)
    combined = [Card(0, 4, 0), Card(0, 5, 0), Card(0, 6, 0)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '2 ' + str(Hand.RANKING_STRAIGHT_FLUSH == hand.rank) + ' ' + str(6 == hand.made[0].rank)

    # testing slighty hidden straight straight flush
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 6, 0)
    combined = [Card(0, 4, 0), Card(0, 7, 1), Card(0, 7, 0), Card(0, 10, 0), Card(0, 8, 0)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '3 ' + str(Hand.RANKING_STRAIGHT_FLUSH == hand.rank) + ' ' + str(8 == hand.made[0].rank)

    # testing straight flush with A on the bottom
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 8, 0)
    combined = [Card(0, 14, 0), Card(0, 4, 1), Card(0, 4, 0), Card(0, 3, 0), Card(0, 2, 0)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '4 ' + str(Hand.RANKING_STRAIGHT_FLUSH == hand.rank) + ' ' + str(5 == hand.made[0].rank)

    # testing for 4 of a kind
    hole1 = Card(0, 14, 0)
    hole2 = Card(0, 14, 1)
    combined = [Card(0, 11, 1), Card(0, 7, 3), Card(0, 2, 3), Card(0, 14, 2), Card(0, 14, 3)]

    hand1 = Hand(hole1, hole2)
    hand1.make(combined)
    print '5 ' + str(Hand.RANKING_4_OF_A_KIND == hand1.rank) + ' ' + str(Card.RANK_ACE == hand1.made[0].rank)

    # testing full house with high 3 of a kind
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 6, 2)
    combined = [Card(0, 5, 1), Card(0, 7, 1), Card(0, 7, 0), Card(0, 7, 3), Card(0, 8, 0)]

    hand2 = Hand(hole1, hole2)
    hand2.make(combined)
    print '6 ' + str(Hand.RANKING_FULL_HOUSE == hand2.rank) + ' ' + str(7 == hand2.made[0].rank)

    print '6a ' + str(1 <= hand1.compare(hand2))
    print '6b ' + str(-1 >= hand2.compare(hand1))
    print '6c ' + str(0 == hand1.compare(hand1))

    # testing full house with low 3 of a kind
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 12, 2)
    combined = [Card(0, 12, 1), Card(0, 7, 1), Card(0, 7, 0), Card(0, 7, 3), Card(0, 8, 0)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '7 ' + str(Hand.RANKING_FULL_HOUSE == hand.rank) + ' ' + str(7 == hand.made[0].rank)


    # testing fluuuush
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 6, 2)
    combined = [Card(0, 13, 0), Card(0, 7, 1), Card(0, 7, 0), Card(0, 10, 0), Card(0, 8, 0)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '8 ' + str(Hand.RANKING_FLUSH == hand.rank) + ' ' + str(13 == hand.made[0].rank)

    # testing slighty hidden straight straight
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 6, 2)
    combined = [Card(0, 4, 3), Card(0, 7, 1), Card(0, 7, 0), Card(0, 10, 0), Card(0, 8, 0)]

    hand1 = Hand(hole1, hole2)
    hand1.make(combined)
    print '9 ' + str(Hand.RANKING_STRAIGHT == hand1.rank) + ' ' + str(8 == hand1.made[0].rank)

    # testing straight with A on the bottom
    hole1 = Card(0, 5, 0)
    hole2 = Card(0, 8, 3) 
    combined = [Card(0, 14, 2), Card(0, 4, 1), Card(0, 4, 1), Card(0, 3, 0), Card(0, 2, 0)]

    hand2 = Hand(hole1, hole2)
    hand2.make(combined)
    print '10a ' + str(Hand.RANKING_STRAIGHT == hand2.rank) + ' ' + str(5 == hand2.made[0].rank)

    print '10b ' + str(1 <= hand1.compare(hand2))
    print '10c ' + str(-1 >= hand2.compare(hand1))
    print '10d ' + str(0 == hand1.compare(hand1))


    # testing straight with A on the top
    combined = [Card(0, 12, 3), Card(0, 11, 1), Card(0, 13, 3), Card(0, 10, 2), Card(0, 9, 3)]

    hole1 = Card(0, 9, 1)
    hole2 = Card(0, 5, 3)
    hand1 = Hand(hole1, hole2)
    hand1.make(combined)

    hole1 = Card(0, 14, 2)
    hole2 = Card(0, 3, 0) 
    hand2 = Hand(hole1, hole2)
    hand2.make(combined)

    print '11a ' + str(Hand.RANKING_STRAIGHT == hand1.rank) + ' ' + str(13 == hand1.made[0].rank)
    print '11b ' + str(Hand.RANKING_STRAIGHT == hand2.rank) + ' ' + str(14 == hand2.made[0].rank)   
    print '11c ' + str(1 <= hand2.compare(hand1))
    print '11d ' + str(-1 >= hand1.compare(hand2))
    print '11e ' + str(0 != hand1.compare(hand2))    
    print '11f ' + str(0 == hand1.compare(hand1))
    print '11g ' + str(0 == hand2.compare(hand2))


    # testing for 3 of a kind
    hole1 = Card(0, 6, 0)
    hole2 = Card(0, 6, 1)
    combined = [Card(0, 9, 1), Card(0, 7, 3), Card(0, 6, 3), Card(0, 12, 2), Card(0, 14, 3)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '12 ' + str(Hand.RANKING_3_OF_A_KIND == hand.rank) + ' ' + str(6 == hand.made[0].rank)

    # testing for 2 pair
    hole1 = Card(0, 6, 0)
    hole2 = Card(0, 4, 1)
    combined = [Card(0, 12, 1), Card(0, 12, 3), Card(0, 6, 3), Card(0, 7, 2), Card(0, 14, 3)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '13 ' + str(Hand.RANKING_2_PAIR == hand.rank) + ' ' + str(12 == hand.made[0].rank)

    combined = [Card(0, 14, 3), Card(0, 14, 1), Card(0, 5, 3), Card(0, 2, 2)]

    hole1 = Card(0, 13, 1)
    hole2 = Card(0, 2, 3)
    hand1 = Hand(hole1, hole2)
    hand1.make(combined)

    hole1 = Card(0, 3, 2)
    hole2 = Card(0, 2, 0) 
    hand2 = Hand(hole1, hole2)
    hand2.make(combined)

    print '13a ' + str(Hand.RANKING_2_PAIR == hand1.rank) + ' ' + str(14 == hand1.made[0].rank)
    print '13b ' + str(Hand.RANKING_2_PAIR == hand2.rank) + ' ' + str(14 == hand2.made[0].rank)   
    print '13c ' + str(-1 >= hand2.compare(hand1))
    print '13d ' + str(1 <= hand1.compare(hand2))
    print '13e ' + str(0 != hand1.compare(hand2))    
    print '13f ' + str(0 == hand1.compare(hand1))
    print '13g ' + str(0 == hand2.compare(hand2))

    combined = [Card(0, 13, 3), Card(0, 6, 1), Card(0, 13, 3), Card(0, 12, 2), Card(0, 12, 2)]

    hole1 = Card(0, 6, 1)
    hole2 = Card(0, 4, 3)
    hand1 = Hand(hole1, hole2)
    hand1.make(combined)

    hole1 = Card(0, 9, 2)
    hole2 = Card(0, 2, 0) 
    hand2 = Hand(hole1, hole2)
    hand2.make(combined)

    print '13h ' + str(Hand.RANKING_2_PAIR == hand1.rank) + ' ' + str(13 == hand1.made[0].rank)
    print '13i ' + str(Hand.RANKING_2_PAIR == hand2.rank) + ' ' + str(13 == hand2.made[0].rank)   
    print '13j ' + str(-1 >= hand1.compare(hand2))
    print '13k ' + str(1 <= hand2.compare(hand1))
    print '13l ' + str(0 != hand1.compare(hand2))    
    print '13m ' + str(0 == hand1.compare(hand1))
    print '13n ' + str(0 == hand2.compare(hand2))



    # testing for a pair
    hole1 = Card(0, 6, 0)
    hole2 = Card(0, 4, 1)
    combined = [Card(0, 12, 1), Card(0, 8, 3), Card(0, 6, 3), Card(0, 7, 2), Card(0, 14, 3)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '14 ' + str(Hand.RANKING_PAIR == hand.rank) + ' ' + str(6 == hand.made[0].rank)

    # testing for high card
    hole1 = Card(0, 9, 0)
    hole2 = Card(0, 4, 1)
    combined = [Card(0, 12, 1), Card(0, 7, 3), Card(0, 6, 3), Card(0, 10, 2), Card(0, 14, 3)]

    hand = Hand(hole1, hole2)
    hand.make(combined)
    print '15 ' + str(Hand.RANKING_HIGH_CARD == hand.rank) + ' ' + str(Card.RANK_ACE == hand.made[0].rank)

   # print ''
   # print hand.rank
   # for card in hand.made:
   #     print str(card.rank) + ' ' + str(card.suit)
    
