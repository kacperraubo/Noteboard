const cache = new Map();

const getInlineIcon = async (iconName, className, extra) => {
    const temporaryElement = document.createElement('div');

    let svgText;

    if (cache.has(iconName)) {
        svgText = cache.get(iconName);
    } else {
        const response = await fetch(`/static/images/icons/${iconName}.svg`);
        svgText = await response.text();

        cache.set(iconName, svgText);
    }

    temporaryElement.innerHTML = svgText;

    const icon = temporaryElement.querySelector('svg');
    icon.classList = className;

    if (extra) {
        for (const [key, value] of Object.entries(extra)) {
            icon.setAttribute(key, value);
        }
    }

    return icon;
};

export { getInlineIcon };
