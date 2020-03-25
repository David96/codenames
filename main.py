from codenames import CodeNames

import asyncio
import json
import websockets
import uuid

GAME=CodeNames(['word%d' % i for i in range(25)])
USERS={}

def generate_uid():
    uids = [uid for uid, _ in USERS]
    while (uid := uuid.uuid4()) in uids:
        pass
    return uid

def state_event():
    return json.dumps({'type': 'state', 'state': GAME.state})

def user_event():
    return json.dumps(
        {
            'type': 'user',
            'users': [name for _, name in USERS]
        })

def add_user(websocket):
    USERS[generate_uid()] = (websocket, '')

async def set_name(uid, name):
    USERS[uid][1] = name

async def remove_user(uid):
    del USERS[uid]

async def serve(websocket, path):
    pass

state_event()
