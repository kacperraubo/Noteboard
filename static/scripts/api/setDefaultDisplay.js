import { generateRequestHeaders } from './generateRequestHeaders.js';

const setDefaultDisplay = async ({ noteId, type }) => {
    const url = `/notes/${noteId}/display`;
    const headers = generateRequestHeaders();

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ type }),
    });

    return response.json();
};

export { setDefaultDisplay };
