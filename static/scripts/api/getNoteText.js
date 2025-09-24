import { generateRequestHeaders } from './generateRequestHeaders.js';

const getNoteText = async ({ noteToken }) => {
    const url = `/notes/${noteToken}/text`;
    const headers = generateRequestHeaders();

    const response = await fetch(url, {
        headers,
    });

    return response.json();
};

export { getNoteText };
