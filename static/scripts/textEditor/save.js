import { isAnonymous } from '../anonymous.js';
import { saveRoom as saveRoomAPI } from '../api/saveRoom.js';
import { getInputValue } from '../utilities/inputs.js';

const textArea = document.querySelector('.editor-text-area');
const noteToken = getInputValue('note-token');
const isUsersRoom = getInputValue('is-users-room', (value) => value === 'true');

const saveFile = async () => {
    const text = textArea.value;

    let response;

    if (isAnonymous && isUsersRoom) {
        response = await saveRoomAPI({
            noteToken,
            text,
            own: isUsersRoom,
        });
    } else {
        response = await saveRoomAPI({
            noteToken,
            file: new Blob([text], { type: 'text/plain' }),
            own: isUsersRoom,
        });
    }

    if (!response.success) {
        alert('Failed to save file');
    }
};

let throttleTimeout;
textArea.addEventListener('input', () => {
    clearTimeout(throttleTimeout);
    throttleTimeout = setTimeout(saveFile, 500);
});
