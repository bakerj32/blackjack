
class Hand:
    cards = []

    def __init__(self):
        cards = []

    def print_hand(self):
        for card in self.cards:
            print card
    def compute_value(self):
        value = 0
        has_ace = False
        #Go through each card in the hand.
        for card in self.cards:
            card_value = card[0]
            #Card is 10, Jack, Queen, or King: Add 10.
            if card_value == 'T' or card_value == 'J' or card_value == 'Q' or card_value == 'K':
                value += 10
            #Found ace: Add 10 for now, check later.
            elif card_value == 'A':
                has_ace = True
                value += 11
            #Found 'normal' card. Add it's value
            else: value += int(card_value)
        #If we busted with an ace, reduce the Ace's value to 1.
        if value > 21 and has_ace:
            value -= 10
        return value
