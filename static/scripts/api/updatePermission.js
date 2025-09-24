import { generateRequestHeaders } from './generateRequestHeaders.js';

const updatePermission = async ({ roomId, permission, value }) => {
    const url = `/rooms/${roomId}/permissions/${permission}/update`;
    const headers = generateRequestHeaders();

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ value }),
    });

    return response.json();
};

export { updatePermission };
