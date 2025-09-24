import { generateRequestHeaders } from './generateRequestHeaders.js';

const createNote = async ({ folderId }) => {
    const url = '/notes/create';

    const response = await fetch(url, {
        method: 'POST',
        headers: generateRequestHeaders(),
        body: JSON.stringify({ folder_id: folderId }),
    });

    return response.json();
};

export { createNote };
