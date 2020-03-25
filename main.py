import asyncio
import json
import random
import uuid
import websockets

from codenames import CodeNames, WIDTH, HEIGHT

with open('words.txt') as f:
    WORDS = [line.strip() for line in f.readlines()]
GAME = CodeNames(random.sample(WORDS, WIDTH*HEIGHT))
USERS = {}

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

async def notify_users(msg_type):
    if USERS:
        if msg_type == 'user':
            message = user_event()
        elif msg_type == 'state':
            message = state_event()
        await asyncio.wait([socket.send(message) for socket, _ in USERS.values()])

async def send_message(message):
    msg = json.dumps({'type':'message', 'msg': message})
    await asyncio.wait([socket.send(msg) for socket, _ in USERS.values()])

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

async def open_field(uid, index):
    GAME.open_field(index)
    name = USERS[uid][1]
    await notify_users('state')
    await send_message('Field %d:%d was opened by %s' %
                       (index % WIDTH + 1, int(index / HEIGHT) + 1, name))

async def serve(websocket, path):
    try:
        msg = json.loads(await websocket.recv())
        assert msg['action'] == 'set_name'
        uid = await add_user(websocket, msg['name'])

        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'open':
                await open_field(uid, data['index'])

    # TODO: proper error handling?!
    finally:
        await remove_user(uid)

start_server = websockets.serve(serve, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
