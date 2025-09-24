import { downloadTextFile } from '../utilities/files.js';
import { setDefaultDisplay } from '../api/setDefaultDisplay.js';
import { getInputValue } from '../utilities/inputs.js';
import { getInlineIcon } from '../utilities/icon.js';
import { isAnonymous } from '../anonymous.js';

const noteName = document.querySelector('[name="note-name"]').value;
const textAreaContainer = document.querySelector('.text-area');
const canvasWrapper = document.querySelector('.canvas-wrapper');
const textArea = document.querySelector('.text-area textarea');
const downloadButton = document.querySelector('.download-button');
const switchModeButton = document.querySelector('.switch-mode-button');

const searchBar = document.querySelector('.search-bar');
const taskBarCanvasOptions = document.querySelector(
    '.task-bar .canvas-options',
);

const noteId = getInputValue('note-id', parseInt);
const isUsersRoom = getInputValue('is-users-room', (value) => value === 'true');

let _inCanvasMode = false;

downloadButton.addEventListener('click', () => {
    if (!_inCanvasMode) {
        downloadTextFile(`${noteName}.txt`, textArea.value);
    }
});

if (switchModeButton) {
    const switchToCanvasMode = async () => {
        textAreaContainer.classList.add('hidden');
        canvasWrapper.classList.remove('hidden');
        taskBarCanvasOptions.classList.remove('hidden');
        searchBar.classList.add('hidden');
        _inCanvasMode = true;

        if (!isAnonymous && isUsersRoom) {
            setDefaultDisplay({ noteId, type: 'canvas' });
        }

        switchModeButton.innerHTML = '';
        switchModeButton.appendChild(await getInlineIcon('file-text', 'icon'));
    };

    const switchToTextArea = async () => {
        textAreaContainer.classList.remove('hidden');
        canvasWrapper.classList.add('hidden');
        taskBarCanvasOptions.classList.add('hidden');
        searchBar.classList.remove('hidden');
        _inCanvasMode = false;

        if (!isAnonymous && isUsersRoom) {
            setDefaultDisplay({ noteId, type: 'text' });
        }

        switchModeButton.innerHTML = '';
        switchModeButton.appendChild(await getInlineIcon('pen-tool', 'icon'));
    };

    switchModeButton.addEventListener('click', () => {
        if (_inCanvasMode) {
            switchToTextArea();
        } else {
            switchToCanvasMode();
        }
    });
}

const inCanvasMode = () => {
    return _inCanvasMode;
};

export { inCanvasMode };
