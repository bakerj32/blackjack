import hand
from socket import *

class Player:
    
    def __init__ (self, username, funds, connection, address, state):
        self.username = username
        self.funds = funds
        self.current_bet = 0
        self.connection = connection
        self.address = address
        self.hand = hand.Hand()
        self.state = state
        self.strike_count = 0
        self.score = 0

    def get_funds(self):
        return self.funds

    def set_funds(self, funds):
        self.funds = funds

    def get_name(self):
        return self.username

    def set_name(self, username):
        self.username = username
