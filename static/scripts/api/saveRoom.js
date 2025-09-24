import { generateRequestHeaders } from './generateRequestHeaders.js';

const saveRoom = async ({
    text = null,
    file = null,
    noteToken,
    own = true,
}) => {
    const url = `/rooms/${noteToken}/save`;
    let body;

    if (file !== null) {
        body = new FormData();
        body.append('file', file);
    } else {
        body = new URLSearchParams();
        body.append('text', text);
    }

    body.append('own', own);

    const response = await fetch(url, {
        method: 'POST',
        headers: generateRequestHeaders({
            contentType:
                file !== null ? null : 'application/x-www-form-urlencoded',
        }),
        body: body,
    });

    return response.json();
};

export { saveRoom };
