WHITE = 0
RED = 1
BLUE = 2
BLACK = 3

var ws, username,
    gamemaster = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Content loaded');
    var form = document.getElementsByClassName('join')[0];
    form.addEventListener('submit', function (event) {
        ws = new WebSocket("ws://127.0.0.1:6789/");
        ws.onopen = onOpen;
        ws.onmessage = onMessage;
        var data = new FormData(form);
        form.className = 'join hidden';
        username = data.get('name');
        console.log(username + ' wants to join');

        event.preventDefault();
    });
});

function setColour(field, colour, classname) {
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

function onMessage(event) {
    data = JSON.parse(event.data);
    switch (data.type) {
        case 'state':
            console.log('Got state message');
            words = document.querySelectorAll(".cnfield button")
            console.log(words.length)
            for (i = 0; i < words.length; ++i) {
                words[i].innerHTML = data.state[i].word;
                setColour(words[i], data.state[i].colour, "word opened");
            }
            break;
        case 'user':
            console.log('Got user message');
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
};
function addMessage(msg, is_error) {
    var messages = document.getElementsByClassName('messages')[0],
        message = document.createElement('li'),
        content = document.createTextNode(msg);
    if (is_error) {
        message.className = 'error';
    }
    message.appendChild(content);
    messages.appendChild(message);
}

function openField(index) {
    ws.send(JSON.stringify({action: 'open', index: index}));
}

function onOpen() {
    console.log('Setting username ' + username);
    ws.send(JSON.stringify({action: "set_name", name: username}));
    document.getElementsByClassName('controlpanel')[0].className = 'controlpanel';
    words = document.querySelectorAll('.cnfield button');
    for (i = 0; i < words.length; ++i) {
        words[i].addEventListener('click', Function('openField('+i+');'));
    }
};
