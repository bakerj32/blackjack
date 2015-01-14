import random
import itertools
class Deck:
    #Two of each suit to make 2 decks.
    SUITS = 'CCHHSSDD'
    RANKS = 'A23456789TJQK'

    def __init__(self):
        self.deck = list(''.join(card) for card in itertools. product(self.RANKS, self.SUITS)) 

    def deal_card(self):
        card = self.deck[random.randint(0, len(self.deck)) - 1]
        self.deck.remove(card)
        return card
    
    def print_deck(self):
        i = 0
        for card in self.deck:
            print str(i) + ': ' + card
            i += 1
            
    def shuffle_deck(self):
        random.shuffle(self.deck)
        #return self.deck
