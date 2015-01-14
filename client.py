import sys, time, signal
from socket import *
from player import *
from select import select


global player



class AlarmException(Exception):
    pass

def alarmHandler(signum, frame):
    raise AlarmException

def nonBlockingRawInput(prompt='', timeout=20):
    signal.signal(signal.SIGALRM, alarmHandler)
    signal.alarm(timeout)
    try:
        text = raw_input(prompt)
        signal.alarm(0)
        return text
    except AlarmException:
        print '\nPrompt timeout. Continuing...'
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    return ''

def handle_deal_msg(msg):
    msg_parts = msg.split('|')
    dealer_card = msg_parts[1]
    current_cards = ''
    for player_info in msg_parts:
        if player.username in player_info:
            cards = player_info.split(',')
            current_cards = cards[2 : len(cards)]
            # Add delt cards to players hand.
            for card in current_cards:
                player.hand.cards.append(card)
    new_msg = 'The dealer is showing a ' + dealer_card + '. You have ' + ','.join(current_cards) + '.'
    return new_msg

def format_send_message_type(msg):
    send_msg = ''
    msg_parts = msg.split(' ')
    if msg_parts[0] == '/join':
        send_msg = '[JOIN|' + msg_parts[1] + ']'
        player.username = msg_parts[1]
    elif msg_parts[0] == '/ante':
        send_msg = '[ANTE|' + msg_parts[1] + ']'
    elif msg_parts[0] == '/hit':
        send_msg = '[TURN|HITT]'
    elif msg_parts[0] == '/stay':
        send_msg = '[TURN|STAY]'
    else:
        send_msg = '[CHAT|' + player.username + '|' + msg + ']'
    return send_msg

def parse_server_message(msg):
    new_msg = ''
    messages = msg.split(']')
    #Parse each pair of "[]" messages seperately as they may have queued
    for message in messages:
        msg_parts = message.split('|')
        if msg_parts[0] == '[CONN':
            location = msg_parts[1]
            funds = msg_parts[2]
            player.funds = funds
            new_msg += 'You are at ' + location + ' with $' + funds.replace(']', '') + '\n' + '\n'
        elif msg_parts[0] == '[CHAT':
            username = msg_parts[1]
            text = msg_parts[2].replace(']', '')
            new_msg += '<' + username + '>: ' + text + '\n'
        elif msg_parts[0] == '[ANTE':
            new_msg += 'Ante up! Min bet is: ' + msg_parts[1].replace(']', '') + '\n'
        elif msg_parts[0] == '[DEAL':
            new_msg += handle_deal_msg(message)
        elif msg_parts[0] == '[TURN':
            user = msg_parts[1]
            if user == player.username:
                new_msg += 'It is your turn. Hit or stand?'
            else: new_msg += "It is " + user + "'s turn. Wait for them to finish."
        elif msg_parts[0] == '[HITT':
            user = msg_parts[1]
            card = msg_parts[2].replace(']', '')
            if user == player.username:
                player.hand.cards.append(card)
                new_msg += "You got a " + card + ". Hit or say?"
            else: new_msg += user + " hit and got a " + card + "."
    return new_msg


host = 'localhost'
port = '8080'
address = (host, int(port))
buffer_size = 4096
prompt_timeout = 5

client = socket(AF_INET, SOCK_STREAM)
client.connect((address))

player = Player('','', client, address, 'ANTE')

msg = ''
while msg != 'quit':
    #Server is talking to us
    try: server_msg = client.recv(buffer_size)
    except: print "Server message not recieved..."
    if server_msg:
        print "Server message: " + server_msg
        parsed_msg = parse_server_message(server_msg)
        print "Parsed message: " + parsed_msg

    #Talk to server
    msg = nonBlockingRawInput('', 5)
    send_msg = format_send_message_type(msg)
    try: client.send(send_msg)
    except: "Issue sending message..."
    print "You are sending: " + msg
    time.sleep(.25)

client.close()
print "Client closed. gg."
