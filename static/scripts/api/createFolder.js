import { generateRequestHeaders } from './generateRequestHeaders.js';

const createFolder = async ({ parentFolderId = null, name }) => {
    const url = '/folders/create';
    const headers = generateRequestHeaders();

    const payload = {
        name,
    };

    if (parentFolderId) {
        payload.parent_folder_id = parentFolderId;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    return response.json();
};

export { createFolder };
