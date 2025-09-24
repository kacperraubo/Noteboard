import { createFolder } from './api/createFolder.js';
import { createNote } from './api/createNote.js';

const createFolderButton = document.querySelector('.create-folder-button');
const currentFolderId = document.querySelector(
    '[name="current-folder-id"]',
).value;

if (createFolderButton) {
    createFolderButton.addEventListener('click', async (event) => {
        const name = prompt('Enter folder name');

        if (!name || !name.trim()) {
            return;
        }

        const response = await createFolder({
            parentFolderId: currentFolderId ? parseInt(currentFolderId) : null,
            name,
        });

        if (!response.success) {
            alert('There was an error creating the folder');
        } else {
            location.reload();
        }
    });
}

const createNoteButton = document.querySelector('.create-note-button');

if (createNoteButton) {
    createNoteButton.addEventListener('click', async () => {
        const response = await createNote({
            folderId: currentFolderId ? parseInt(currentFolderId) : null,
        });

        if (!response.success) {
            alert('There was an error creating the note');
        } else {
            console.log(response);
            window.location.href = response.payload.path;
        }
    });
}
