# server.py
import sys, deck, hand, sys, select, Queue
from socket import *
from player import *

global players
global table
global lobby
global game_state
global table_size
global deck
global min_table_start
global writable
global message_queues

def get_file_data(filename):
    fh = open(filename)
    data = fh.readlines()
    fh.close()
    return data

def write_array_to_file(data, filename):
    fh = open(filename, 'w')
    for line in data:
        fh.write(line)
    fh.close()

def update_user_funds(username, funds):
    data = get_file_data('users.txt')
    good_lines = []
    # Keep all lines besides current user
    for line in data:
        parts = line.split(',')
        print parts[0] + '-' + username
        if parts[0] != username:
            good_lines.append(line)
    # Append new updated line
    good_lines.append('\n' + username + ',' + str(funds))
    write_array_to_file(good_lines, 'users.txt')

def create_user(username):
    fh = open('users.txt', 'a')
    fh.write('\n' + username + ',1000')
    fh.close()

def get_users_list():
    data = get_file_data('users.txt')
    users = []
    for line in data:
        parts = line.split(',')
        users.append(parts[0])
    return users

def get_user_funds(username):
    data = get_file_data('users.txt')
    for line in data:
        parts = line.split(',')
        if parts[0] == username:
            funds = parts[1]
    return funds

def get_location():
    if table_is_full(): return 'LBBY'
    else: return 'TABL'

def table_is_full():
    if len(table) >= table_size:
        return True
    else: return False

def get_game_state():
    for player in players:
        if player.state == 'ANTE':
            return 'ANTE'
    for player in players:
        if player.state == 'DEAL':
            return 'DEAL'
    for player in players:
        if player.state == 'TURN':
            return 'TURN'
    for player in players:
        if player.state == 'DONE':
            return 'DONE'
        

def get_login(username, connection, address):
    users = get_users_list()
    #See if user exists in user file. Construct user object
    if username in users:
        #If so, get his current funds.
        funds = get_user_funds(username).replace('\n', '')
        player1 = Player(username, funds, connection, address, 'ANTE')
        print "User " + player1.username + " exists with $" + player1.funds + "!"
    else:
        #Otherwise add the user to the user file.
        create_user(username)
        funds = 1000
        player1 = Player(username, funds, connection, address, 'ANTE')
        print "User " + username + " registered as new user. You start with $1000."
    players.append(player1)
    
    #Decide if player should go to table or lobby
    location = get_location()
    if location == 'TABL':
        table.append(player1)
    else: lobby.append(player1)
    #Prepare reply for client
    reply = '[CONN|' + location + '|' + str(funds) + ']'
    return reply

def set_turn(player_idx):
    if player_idx == len(players) - 1:
        return True
    else:
        players[player_idx + 1].state == 'TURN-NOW'
        message_queues[players[player_idx + 1].connection].put("[TURN|" + players[player_idx + 1].username + "]")
        print "It is now " + players[player_idx + 1].username + " turn.\n"
        return False

def deal_cards(deck, dealer, shuffle):
    deal_msg = '[DEAL|'
    if shuffle == 'SHUFY': deck.shuffle_deck()
    dealer_card = deck.deal_card()
    deal_msg += dealer_card + '|'
    deal_msg += shuffle
    for player in players:
        card1 = deck.deal_card()
        card2 = deck.deal_card()
        player.hand.cards.append(card1)
        player.hand.cards.append(card2)
        player.state = 'TURN'
        deal_msg += '|' + player.username + ',' + str(player.funds) + ',' + card1 + ',' + card2
    deal_msg += ']'
    # Set first players to now.
    players[0].state = 'TURN-NOW'
    message_queues[players[0].connection].put('[TURN|' + players[0].username + ']')
    return deal_msg

def broadcast(msg):
    for player in players:
        print "Broadcasting: " + msg + " to " + player.username
        message_queues[player.connection].put(msg)

def handle_turn(message, connection, address):
    reply_msg = ''
    broadcast_msg = ''
    msg_parts = message.split('|')
    player_idx = 0
    for player in players:
        if player.address == address:
            break
        player_idx += 1
    if players[player_idx].state != 'TURN-NOW':
        players[player_idx].strike_count += 1
        reply_msg += "It's not your turn..."
    else:
        action = msg_parts[1].replace(']', '')
        if action == 'HITT':
            card = deck.deal_card()
            players[player_idx].hand.cards.append(card)
            if players[player_idx].hand.compute_value() > 21:
                bust = 'BUSTY'
            else: bust = 'BUSTN'
            broadcast_msg += '[HITT|' + players[player_idx].username + '|' + card + ']'
            broadcast_msg += '[STAT|' + players[player_idx].username + '|' + action + '|' + card + '|' + bust + '|' + str(players[player_idx].current_bet) + ']'
        elif action == 'STAY':
            if players[player_idx].hand.compute_value() > 21:
                bust = 'BUSTY'
            else: bust = 'BUSTN'
            broadcast_msg += '[STAT|' + players[player_idx].username + '|' + action + '||' + bust + '|' + str(players[player_idx].current_bet) + ']'
            players[player_idx].score = players[player_idx].hand.compute_value()
            players[player_idx].state = 'DONE'
            round_over = set_turn(player_idx)
            if round_over: game_state = 'DEALER-TURN'
    broadcast(broadcast_msg)
    return reply_msg
    

def get_message_type(message, connection, address):
    parts = message.split('|')
    msg_type = parts[0][1 : len(parts[0])]
    if msg_type == 'JOIN':
        reply = get_login(parts[1][0 : len(parts[1]) - 1], connection, address)
    elif msg_type == 'CHAT':
        reply = ''
        broadcast(message)
    elif msg_type == 'ANTE':
        reply = 'Thank you for your ante...'
        for player in players:
            if player.address == address:
                player.current_bet = int(parts[1].replace(']', ''))
                player.funds = int(player.funds) - int(player.current_bet)
                player.state = 'DEAL'
    elif msg_type == 'TURN':
        reply = handle_turn(message, connection, address)
    return reply





    


MAX_QUEUED_CONNECTIONS = 8
host = ''
port = 8080
address = (host, port)
buffer_size = 4096

server = socket( AF_INET, SOCK_STREAM)
server.setblocking(0)
server.bind((address))
server.listen(MAX_QUEUED_CONNECTIONS)

min_bet = 100
game_state = 'ANTE'
table_size = 2
min_table_start = 2
table = []
lobby = []
players = []
inputs = [server]
outputs = []
message_queues = {}
deck = deck.Deck()
dealer = Player('', '', '', '', '')

while inputs:
    print >> sys.stderr, '\nWaiting for next event...'
    readable,writable,exceptional = select.select(inputs, outputs, inputs)
    '''
    for player in players:
        print player.username + " is connected."
        player.connection.send("You are connected...")
    '''
    for sock in readable:
        if sock is server:
            # Server ready to accept a new connection
            connection, client_address = sock.accept()
            print >> sys.stderr, 'New connection from: ', client_address
            connection.setblocking(0)
            inputs.append(connection)
            connection.send("Welcome, what's your name bro?")

            message_queues[connection] = Queue.Queue()

        else:
            print "Client is doing something..."
            # Client connections
            try:
                data = sock.recv(buffer_size)
            except: "something happened..."
            
            if data:
                print >> sys.stderr, 'Received "%s" from %s' % (data, sock.getpeername())
                reply = get_message_type(data, sock, sock.getpeername())
                print "Putting " + reply + " in message queue."
                message_queues[sock].put(reply)
                # Create output channel for new socket.
                if sock not in outputs:
                    outputs.append(sock)
            else:
                # Sockets without data = disconnected.
                print >> sys.stderr, 'closing ', client_address, ' after no data'
                if sock in outputs:
                    outputs.remove(sock)
                sock.close()
                for player in players:
                    if player.connection == sock:
                        del players[player.connection]
                del message_queues[sock]

            # Main blackjack table loop
            game_state = get_game_state()
            if game_state == 'DEAL':
                game_msg = deal_cards(deck, dealer, 'SHUFY')
                broadcast(game_msg)
            for player in table:
                if game_state == 'ANTE' and player.state == 'ANTE':
                    message_queues[player.connection].put("[ANTE|" + str(min_bet) + "]")
                #if game_state == 'DEAL':
                    #message_queues[player.connection].put(game_msg)
                #if player.state == 'TURN-NOW':
                    #message_queues[player.connection].put("[TURN|" + player.username + "]")
                if game_state == 'DEALER-TURN':
                    message_queues[player.connection].put("Its the dealers turn!")
                    
                    
    for sock in writable:
        try:
            next_msg = message_queues[sock].get_nowait()
        except Queue.Empty:
            print >> sys.stderr, 'output queue emtpy for', sock.getpeername()
            outputs.remove(sock)
        else:
            print >> sys.stderr, 'sending "%s" to %s' % (next_msg, sock.getpeername())
            sock.send(next_msg)

    for sock in exceptional:
        print >> sys.stderr, 'handling exception for ', sock.getpeername()

        inputs.remove(sock)
        if sock in outputs:
            outputs.remove(sock)
        sock.close()

        del message_queues[sock]
        
    


conn.close()


