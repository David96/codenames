import asyncio
import json
import random
import uuid
import websockets

from codenames import CodeNames, WIDTH, HEIGHT

with open('words.txt') as f:
    WORDS = [line.strip() for line in f.readlines()]

WORDS_LEFT = list(WORDS)
GAME = CodeNames()
USERS = []
GAMEMASTERS = []

def reset_game():
    GAMEMASTERS.clear()
    sample = random.sample(WORDS_LEFT, 25)
    for word in sample:
        WORDS_LEFT.remove(word)
    GAME.reset(sample)

async def reset(uid, _):
    if uid is not None and uid not in GAMEMASTERS:
        await send_error(uid, 'You are not a gamemaster!')
    else:
        reset_game()
        await notify_users('state')
        await send_message('The game has been reset!')

def state_event():
    return json.dumps({'type': 'state', 'state': GAME.state})

def user_event():
    return json.dumps(
        {
            'type': 'user',
            'users': [name for _, name in USERS]
        })

EVENTS = {
    'user': user_event,
    'state': state_event
}

async def notify_users(msg_type):
    if USERS:
        message = EVENTS[msg_type]()
        await asyncio.wait([socket.send(message) for socket, _ in USERS])

async def send_message(message):
    if USERS:
        msg = json.dumps({'type':'message', 'msg': message})
        await asyncio.wait([socket.send(msg) for socket, _ in USERS])

async def send_error(user, message):
    await user[0].send(json.dumps({'type':'error', 'msg':message}))

async def add_user(websocket, name):
    user = (websocket, name)
    USERS.append(user)
    await notify_users("user")
    await send_message('%s joined the game!' % name)
    return user

async def remove_user(user):
    name = user[1]
    if user in GAMEMASTERS:
        GAMEMASTERS.remove(user)
    USERS.remove(user)
    await notify_users('user')
    await send_message('%s left the game.' % name)

async def open_field(user, data):
    if user in GAMEMASTERS:
        await send_error(user, 'A gamemaster can\'t open fields!')
    else:
        index = data['index']
        if GAME.state[index]['colour'] > -1:
            await send_error(user, 'Field %d:%d is already open!' %
                           (index % WIDTH + 1, int(index / HEIGHT) + 1))
        else:
            GAME.open_field(index)
            name = user[1]
            await notify_users('state')
            await send_message('Field %d:%d was opened by %s' %
                               (index % WIDTH + 1, int(index / HEIGHT) + 1, name))

async def become_master(user, _):
    if user in GAMEMASTERS:
        await send_error(user, 'You are already a gamemaster!')
    elif len(GAMEMASTERS) >= 2:
        await send_error(user, 'There are already two gamemasters!')
    else:
        GAMEMASTERS.append(user)
        await user[0].send(json.dumps(
            {
                'type': 'colours',
                'colours': GAME.colours
            }))
        await send_message('%s has become game master!' % user[1])

ACTIONS = {
    'open': open_field,
    'become_master': become_master,
    'reset': reset
}

async def serve(websocket, path):
    try:
        msg = json.loads(await websocket.recv())
        assert msg['action'] == 'set_name'
        user = await add_user(websocket, msg['name'])

        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] in ACTIONS:
                await ACTIONS[data['action']](user, data)
            else:
                await send_error(user, '%s is not a valid action!' % data['action'])

    # TODO: proper error handling?!
    finally:
        await remove_user(user)

start_server = websockets.serve(serve, "localhost", 6789)

reset_game()
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
