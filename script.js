WHITE = 0
RED = 1
BLUE = 2
BLACK = 3

var ws, username,
    gamemaster = false,
    initialized = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Content loaded');
    var form = document.getElementsByClassName('join')[0];
    form.addEventListener('submit', function (event) {
        ws = new WebSocket("ws://127.0.0.1:6789/");
        ws.onopen = onOpen;
        ws.onmessage = onMessage;
        var data = new FormData(form);
        username = data.get('name');

        event.preventDefault();
    });

    var become_master = document.getElementById('become_master');
    become_master.addEventListener('click', () => {
        if (gamemaster) {
            ws.send(JSON.stringify({action: 'reset'}));
        } else {
            ws.send(JSON.stringify({action: 'become_master'}));
        }
    });
    var choose_red = document.getElementById('choose_red');
    var choose_blue = document.getElementById('choose_blue');

    choose_red.addEventListener('click', () => {
        ws.send(JSON.stringify({action: 'set_colour', colour: RED}));
        choose_red.disabled = true;
        choose_blue.disabled = false;
    });
    choose_blue.addEventListener('click', () => {
        ws.send(JSON.stringify({action: 'set_colour', colour: BLUE}));
        choose_red.disabled = false;
        choose_blue.disabled = true;
    });
});

function setColour(field, colour, classname) {
    if (!field.classList.contains('opened') || colour == -1) {
        switch (colour) {
            case -1:
                if (!gamemaster) {
                    field.className = "word closed";
                }
                break;
            case WHITE:
                field.className = classname + " white";
                break;
            case RED:
                field.className = classname + " red";
                break;
            case BLUE:
                field.className = classname + " blue";
                break;
            case BLACK:
                field.className = classname + " black";
                break;
        }
    }
}

function onMessage(event) {
    data = JSON.parse(event.data);
    switch (data.type) {
        case 'state':
            console.log('Got state message');
            if (!initialized) {
                initGame();
            }
            words = document.querySelectorAll(".cnfield button")
            console.log(words.length)
            for (i = 0; i < words.length; ++i) {
                words[i].innerHTML = data.state[i].word;
                setColour(words[i], data.state[i].colour, "word opened");
            }
            break;
        case 'user':
            console.log('Got user message');
            createUserList(data.users);
            data.users.forEach((user) => {
                if (user.name == username) {
                    if (user.gamemaster && !gamemaster) {
                        onGameMaster(true);
                    } else if (!user.gamemaster && gamemaster) {
                        onGameMaster(false);
                    }
                    return;
                }
            });
            break;
        case 'colours':
            console.log('Got colours message');
            words = document.querySelectorAll(".cnfield button")
            for (i = 0; i < words.length; ++i) {
                setColour(words[i], data.colours[i], "word");
            }
            break;
        case 'message':
            console.log('Got message: ' + data.msg)
            addMessage(data.msg);
            break;
        case 'error':
            console.log('Got error: ' + data.msg)
            addMessage(data.msg, true);
            break
    }
}

function onGameMaster(master) {
    gamemaster = master;
    var become_master = document.getElementById('become_master');
    if (master) {
        become_master.innerHTML = "Reset game";
    } else {
        become_master.innerHTML = "Become gamemaster";
    }
}

function addMessage(msg, is_error) {
    var messages = document.getElementById('messagelist'),
        message = document.createElement('li'),
        content = document.createTextNode(msg);
    if (is_error) {
        message.className = 'error';
    }
    message.appendChild(content);
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
}
function createUserList(users) {
    var list = document.getElementById('userlist');
    list.innerText = '';
    users.forEach((user) => {
        var li = document.createElement('li');
        var text = user.name;
        if (user.gamemaster) {
            text += " (Gamemaster)";
        }
        console.log('Team: ' + user.team);
        if (user.team == RED) {
            li.className = 'team_red';
        } else if (user.team == BLUE) {
            li.className = 'team_blue';
        }
        li.appendChild(document.createTextNode(text));
        list.appendChild(li);
    });
}

function openField(index) {
    ws.send(JSON.stringify({action: 'open', index: index}));
}

function onOpen() {
    console.log('Setting username ' + username);
    ws.send(JSON.stringify({action: "set_name", name: username}));
}

function initGame() {
    initialized = true;
    document.getElementsByClassName('controlpanel')[0].className = 'controlpanel';
    words = document.querySelectorAll('.cnfield button');
    for (i = 0; i < words.length; ++i) {
        words[i].addEventListener('click', Function('openField('+i+');'));
    }
    var form = document.getElementsByClassName('join')[0];
    var data = new FormData(form);
    form.className = 'join hidden';
    username = data.get('name');
}
