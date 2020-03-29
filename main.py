import asyncio
import json
import random
import uuid
import websockets

from codenames import CodeNames, Player, WIDTH, HEIGHT, RED, BLUE

with open('words.txt') as f:
    WORDS = [line.strip() for line in f.readlines()]

WORDS_LEFT = list(WORDS)
GAME = CodeNames()
USERS = {}
GAMEMASTERS = []

def reset_game():
    if len(WORDS_LEFT) < 25:
        WORDS_LEFT.clear()
        for word in WORDS:
            WORDS_LEFT.append(word)
        print('Words empty, needs new words')
    sample = random.sample(WORDS_LEFT, 25)
    for word in sample:
        WORDS_LEFT.remove(word)
    GAME.reset(sample)

async def reset(user, _):
    if not GAME.players[user].gamemaster:
        await send_error(USERS[user], 'You are not a gamemaster!')
    else:
        reset_game()
        await notify_users('user')
        await notify_users('state')
        await send_message('The game has been reset!')

def state_event():
    return json.dumps({'type': 'state', 'state': GAME.state})

def user_event():
    return json.dumps(
        {
            'type': 'user',
            'users': [{'name': user.name, 'gamemaster': user.gamemaster, 'team': user.colour }
                      for user in GAME.players.values()]
        })

def gameover_event():
    return json.dumps(
        {
            'type': 'gameover',
            'winner': GAME.winner,
            'reason': GAME.reason
        })

EVENTS = {
    'user': user_event,
    'state': state_event,
    'gameover': gameover_event
}

async def notify_users(msg_type):
    if USERS:
        message = EVENTS[msg_type]()
        await asyncio.wait([socket.send(message) for socket in USERS.values()])

async def send_message(message):
    if USERS:
        msg = json.dumps({'type':'message', 'msg': message})
        await asyncio.wait([socket.send(msg) for socket in USERS.values()])

async def send_error(socket, message, error_type="error"):
    await socket.send(json.dumps({'type': error_type, 'msg': message}))

async def add_user(websocket, name):
    if name in GAME.players:
        return None
    GAME.add_player(name)
    USERS[name] = websocket
    await notify_users("user")
    await send_message('%s joined the game!' % name)
    return name

async def remove_user(user):
    del GAME.players[user]
    del USERS[user]
    await notify_users('user')
    await send_message('%s left the game.' % user)

async def open_field(user, data):
    if GAME.players[user].gamemaster:
        await send_error(USERS[user], 'A gamemaster can\'t open fields!')
    else:
        index = data['index']
        if GAME.state[index]['colour'] > -1:
            await send_error(USERS[user], 'Field %d:%d is already open!' %
                           (index % WIDTH + 1, int(index / HEIGHT) + 1))
        else:
            GAME.open_field(index, user)
            await notify_users('state')
            await send_message('%s (%d:%d) was opened by %s' %
                    (GAME.state[index]['word'],
                        index % WIDTH + 1, int(index / HEIGHT) + 1, user))
            if GAME.winner > -1:
                await notify_users('gameover')
                await send_message('Team %s wins the game!'
                        % ('red' if GAME.winner == RED else 'blue'))

async def become_master(user, _):
    if GAME.players[user].gamemaster:
        await send_error(USERS[user], 'You are already a gamemaster!')
    elif GAME.gamemaster_count() >= 2:
        await send_error(USERS[user], 'There are already two gamemasters!')
    else:
        GAME.players[user].gamemaster = True
        await USERS[user].send(json.dumps(
            {
                'type': 'colours',
                'colours': GAME.colours
            }))
        await notify_users('user')
        await send_message('%s has become game master!' % user)

async def set_colour(user, data):
    if not data['colour'] or (data['colour'] != RED and data['colour'] != BLUE):
        send_error(USERS[user], 'Invalid colour!')
        return
    USERS[user].colour = data['colour']
    await notify_users('user')
    await send_message('%s is now part of team %s' %
                       (user, 'red' if data['colour'] == RED else 'blue'))

ACTIONS = {
    'open': open_field,
    'become_master': become_master,
    'set_colour': set_colour,
    'reset': reset
}

async def serve(websocket, path):
    try:
        user = None
        async for message in websocket:
            data = json.loads(message)
            if 'action' not in data or data['action'] != 'set_name':
                await send_error(websocket, 'First message must be a set_name action!')
                await websocket.close()
                return
            user = await add_user(websocket, data['name'])
            if user:
                break
            await send_error(websocket, 'Name is already taken!')

        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] in ACTIONS:
                await ACTIONS[data['action']](user, data)
            else:
                await send_error(websocket, '%s is not a valid action!' % data['action'])

    # TODO: proper error handling?!
    finally:
        if user:
            await remove_user(user)

start_server = websockets.serve(serve, "localhost", 6789)

reset_game()
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
