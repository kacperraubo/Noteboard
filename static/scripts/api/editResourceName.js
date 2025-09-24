import { generateRequestHeaders } from './generateRequestHeaders.js';

const editResourceName = async ({ resourceId, resourceToken, newName }) => {
    const url = `/${parseInt(resourceId)}/${resourceToken}/rename`;
    const headers = generateRequestHeaders();

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name: newName }),
    });

    return response.json();
};

export { editResourceName };
