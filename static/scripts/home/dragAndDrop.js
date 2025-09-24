document.addEventListener('DOMContentLoaded', async () => {
    const resourceList = document.querySelector('.resource-list');

    if (!resourceList) {
        return;
    }

    let resources = [...resourceList.querySelectorAll('.resource')];
    const moveResourceIcons = [...document.querySelectorAll('.move-button')];
    const resourcesMovableBetweenFolders = [
        ...document.querySelectorAll('.resource-list .resource'),
    ];
    const targetFolders = [
        ...document.querySelectorAll('.resource-list .resource.folder'),
        ...document.querySelectorAll('.resource-history .resource.folder'),
    ];

    let draggedItemId = null;
    let draggedItemToken = null;

    let dragType = null;
    let draggedItem = null;
    let wasDropped = false;

    function getCSRFToken() {
        return document.querySelector(
            '.jsMainlayout [name="csrfmiddlewaretoken"]',
        ).value;
    }

    function allowDrop(event) {
        event.stopPropagation();
        event.preventDefault();

        if (dragType === 'moveBetweenFolders') {
            event.dataTransfer.dropEffect = 'copy';
        } else if (dragType === 'moveWithinFolder') {
            event.dataTransfer.dropEffect = 'move';
        }
    }

    function movingBetweenFolders() {
        return dragType && dragType === 'moveBetweenFolders';
    }

    function movingWithinFolder() {
        return dragType && dragType === 'moveWithinFolder';
    }

    function resetDragState() {
        if (resourceList.contains(placeholder)) {
            resourceList.removeChild(placeholder);
        }

        placeholder.innerHTML = '';

        dragType = null;
        draggedItem = null;
        wasDropped = false;

        draggedItemId = null;
        draggedItemToken = null;
    }

    function insertDraggedItem(event) {
        event.preventDefault();
        event.stopPropagation();

        const csrfToken = getCSRFToken();
        const destinationIndex = [...resourceList.children].indexOf(
            placeholder,
        );

        const body = {
            moved_resource_id: draggedItemId,
            destination_index: destinationIndex,
            moved_resource_token: draggedItemToken,
        };

        fetch('/resources/move', {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(body),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    resourceList.insertBefore(draggedItem, placeholder);
                    resources = [...resourceList.querySelectorAll('.resource')];
                } else {
                    throw Error(
                        `${data.error.message} code: ${data.error.code}`,
                    );
                }
            })
            .catch((error) => {
                alert('Failed to move resource.');

                const originalIndex = placeholder.dataset.originalIndex;

                if (originalIndex !== undefined) {
                    resourceList.insertBefore(
                        draggedItem,
                        resources[originalIndex],
                    );
                } else {
                    resourceList.appendChild(draggedItem);
                }

                console.error(error);
            })
            .finally(() => {
                resetDragState();
            });
    }

    let placeholder = document.createElement('li');
    placeholder.classList.add('placeholder', 'resource');

    placeholder.addEventListener('dragover', (event) => {
        allowDrop(event);
    });
    placeholder.addEventListener('drop', (event) => {
        if (movingWithinFolder() && draggedItem) {
            wasDropped = true;
            insertDraggedItem(event);
            dragType = null;
        }
    });

    function betweenFolderDragStart(event) {
        if (movingWithinFolder()) {
            return;
        }

        dragType = 'moveBetweenFolders';

        draggedItemToken = event.target.closest('.resource').dataset.token;
        draggedItemId = event.target.closest('.resource').dataset.id;
    }

    function dropIntoFolder(event) {
        if (!movingBetweenFolders()) {
            return;
        }

        const destinationFolderToken = event.currentTarget.dataset.token;

        if (destinationFolderToken === draggedItemToken) {
            return;
        }

        const csrfToken = getCSRFToken();
        const body = {
            moved_resource_id: draggedItemId,
            moved_resource_token: draggedItemToken,
        };

        if (destinationFolderToken) {
            body.destination_folder_token = destinationFolderToken;
        }

        fetch('/resources/transfer', {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(body),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    const { item_id: itemId, item_token: itemToken } =
                        data.payload;
                    const movedItemEl = document.querySelector(
                        `.resource[data-id="${itemId}"][data-token="${itemToken}"]`,
                    );
                    movedItemEl.remove();
                } else {
                    throw Error(
                        `${data.error.message} code: ${data.error.code}`,
                    );
                }
            })
            .catch((error) => {
                console.log(error);
            })
            .finally(() => {
                resetDragState();

                if (resourceList.children.length === 0) {
                    document
                        .querySelector('.empty-state')
                        .classList.remove('hidden');
                } else {
                    document
                        .querySelector('.empty-state')
                        .classList.add('hidden');
                }
            });
    }

    resourcesMovableBetweenFolders.forEach((resource) => {
        resource.addEventListener('dragstart', betweenFolderDragStart);
        resource.addEventListener('dragend', () => {
            if (movingBetweenFolders()) {
                resetDragState();
            }
        });
    });

    targetFolders.forEach((folder) => {
        folder.addEventListener('dragover', allowDrop);
        folder.addEventListener('drop', dropIntoFolder);
    });

    moveResourceIcons.forEach((icon) => {
        icon.addEventListener('dragstart', (event) => {
            if (movingBetweenFolders()) {
                return;
            }

            dragType = 'moveWithinFolder';
            draggedItem = event.target.closest('.resource');
            const draggedItemNextSibling = draggedItem.nextSibling;
            placeholder.innerHTML = draggedItem.innerHTML;
            placeholder.dataset.originalIndex = resources.indexOf(draggedItem);

            if (draggedItem.dataset.type === 'folder') {
                placeholder.classList.add('folder');
                placeholder.classList.remove('note');
            } else {
                placeholder.classList.add('note');
                placeholder.classList.remove('folder');
            }

            draggedItemToken = draggedItem.dataset.token;
            draggedItemId = draggedItem.dataset.id;

            setTimeout(() => {
                draggedItem.remove();
                resources = resources.filter(
                    (resource) => resource !== draggedItem,
                );
                resourceList.insertBefore(placeholder, draggedItemNextSibling);
            }, 0);
        });

        icon.addEventListener('dragend', (event) => {
            if (!wasDropped) {
                insertDraggedItem(event);
            }
        });
    });

    resources.forEach((resource) => {
        resource.addEventListener('dragenter', (event) => {
            event.preventDefault();
        });
        resource.addEventListener('dragover', (event) => {
            if (!movingWithinFolder()) {
                return;
            }

            if (resources.indexOf(resource) !== -1) {
                resourceList.insertBefore(
                    placeholder,
                    resources[resources.indexOf(resource)],
                );
            }
        });

        resource.addEventListener('drop', (event) => {
            wasDropped = true;

            if (movingWithinFolder()) {
                insertDraggedItem(event);
            }
        });
    });

    resourceList.addEventListener('dragover', (event) => {
        if (movingWithinFolder()) {
            allowDrop(event);
        }
    });

    resourceList.addEventListener('drop', (event) => {
        wasDropped = true;

        if (movingWithinFolder() && draggedItem) {
            insertDraggedItem(event);
        }
    });

    document.body.addEventListener('dragover', (event) => {
        if (movingWithinFolder()) {
            allowDrop(event);

            if (
                event.target.lastChild !== placeholder &&
                event.pageY > resourceList.getBoundingClientRect().bottom
            ) {
                if (resourceList.contains(placeholder)) {
                    resourceList.removeChild(placeholder);
                }

                resourceList.appendChild(placeholder);
            }
        }
    });

    document.body.addEventListener('drop', (event) => {
        wasDropped = true;

        if (movingWithinFolder() && draggedItem) {
            insertDraggedItem(event);
        }
    });
});
