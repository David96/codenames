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
USERS = {}
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

def generate_uid():
    while uid := uuid.uuid4() in USERS:
        pass
    return uid

def state_event():
    return json.dumps({'type': 'state', 'state': GAME.state})

def user_event():
    return json.dumps(
        {
            'type': 'user',
            'users': [name for __, name in USERS.values()]
        })

EVENTS = {
    'user': user_event,
    'state': state_event
}

async def notify_users(msg_type):
    if USERS:
        message = EVENTS[msg_type]()
        await asyncio.wait([socket.send(message) for socket, _ in USERS.values()])

async def send_message(message):
    if USERS:
        msg = json.dumps({'type':'message', 'msg': message})
        await asyncio.wait([socket.send(msg) for socket, _ in USERS.values()])

async def send_error(uid, message):
    if uid in USERS:
        await USERS[uid][0].send(json.dumps({'type':'error', 'msg':message}))

async def add_user(websocket, name):
    uid = generate_uid()
    USERS[uid] = (websocket, name)
    await notify_users("user")
    await send_message('%s joined the game!' % name)
    return uid

async def remove_user(uid):
    name = USERS[uid][1]
    del USERS[uid]
    await notify_users('user')
    await send_message('%s left the game.' % name)

async def open_field(uid, data):
    if uid in GAMEMASTERS:
        await send_error(uid, 'A gamemaster can\'t open fields!')
    else:
        index = data['index']
        GAME.open_field(index)
        name = USERS[uid][1]
        await notify_users('state')
        await send_message('Field %d:%d was opened by %s' %
                           (index % WIDTH + 1, int(index / HEIGHT) + 1, name))

async def become_master(uid, _):
    if uid in GAMEMASTERS:
        await send_error(uid, 'You are already a gamemaster!')
    elif len(GAMEMASTERS) >= 2:
        await send_error(uid, 'There are already two gamemasters!')
    else:
        GAMEMASTERS.append(uid)
        await USERS[uid][0].send(json.dumps(
            {
                'type': 'colours',
                'colours': GAME.colours
            }))
        await send_message('%s has become game master!' % USERS[uid][1])

ACTIONS = {
    'open': open_field,
    'become_master': become_master,
    'reset': reset
}

async def serve(websocket, path):
    try:
        msg = json.loads(await websocket.recv())
        assert msg['action'] == 'set_name'
        uid = await add_user(websocket, msg['name'])

        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] in ACTIONS:
                await ACTIONS[data['action']](uid, data)
            else:
                await send_error(uid, '%s is not a valid action!' % data['action'])

    # TODO: proper error handling?!
    finally:
        await remove_user(uid)

start_server = websockets.serve(serve, "localhost", 6789)

reset_game()
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
