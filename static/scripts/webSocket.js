const url = 'wss://' + window.location.host +
'/ws/' + userId + '/' + noteName + '/r/' + roomName + '/';
const WebSocketRetryDelay = 2000;

let webSocket;

function connectWebSocket(url) {
    webSocket = new WebSocket(url);

    webSocket.onopen = function(event) {
        // console.log('WebSocket connected!');
    }

    webSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        textAreaEl.value = data.message ;
    };

    webSocket.onclose = function(event) {
        setTimeout(() => connectWebSocket(url), WebSocketRetryDelay);
    };

    webSocket.onerror = function(event) {
        console.error('WebSocket error:', event);
        setTimeout(() => connectWebSocket(url), WebSocketRetryDelay);
    }
}

connectWebSocket(url);

const delay = 1000; //ms
let typingTimer;
textAreaEl.addEventListener('input', function(event) {
    const message = event.target.value;
    if(message) {
        // send message in JSON format
        if (webSocket.readyState === WebSocket.OPEN) {
            webSocket.send(JSON.stringify({'message': message}));
        } else {
            console.error('WebSocket connection is not open.');
        }
    }

    clearTimeout(typingTimer);
    typingTimer = setTimeout(saveFile, delay);
});


window.addEventListener('beforeunload', function() {
  webSocket.close();
});

