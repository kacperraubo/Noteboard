function createElement(tagName, classes=null, attributes=null) {
    // Creating new element
    const newElement = document.createElement(tagName);

    // Adding classes to new element
    if (classes && Array.isArray(classes)) {
        newElement.classList.add(...classes);
    }

    // Adding attributes to new element
    if (attributes && typeof attributes === 'object') {
        for (const attribute in attributes) {
        if (attributes.hasOwnProperty(attribute)) {
            newElement.setAttribute(attribute, attributes[attribute]);
        }
        }
    }

    return newElement;
}