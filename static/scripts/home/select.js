import { getCsrfToken } from '../utilities/getCsrfToken.js';
import { downloadTextFile } from '../utilities/files.js';

const resources = document.querySelectorAll('.resource-list .resource');
const dependantItems = document.querySelectorAll('.requires-selection');
const requiresNoteSelection = document.querySelectorAll(
    '.requires-note-selection',
);
const unavailableWhenSelected = document.querySelectorAll(
    '.unavailable-when-selecting',
);

const selectAllButton = document.querySelector('.select-all-button');
const selectAllButtonSelectedIcon =
    selectAllButton.querySelector('.selected-icon');
const selectAllButtonNotSelectedIcon =
    selectAllButton.querySelector('.not-selected-icon');

const downloadButton = document.querySelector('.task-bar .download-button');
const deleteButton = document.querySelector('.task-bar .delete-button');

let selection = [];

const filteredResources = () => {
    return Array.from(resources).filter((resource) => {
        return !resource.classList.contains('hidden');
    });
};

const updateUiForSelection = () => {
    if (selection.length === 0) {
        dependantItems.forEach((item) => {
            item.classList.add('hidden');
        });

        unavailableWhenSelected.forEach((item) => {
            item.classList.remove('hidden');
        });

        requiresNoteSelection.forEach((item) => {
            item.classList.add('hidden');
        });
    } else {
        dependantItems.forEach((item) => {
            item.classList.remove('hidden');
        });

        unavailableWhenSelected.forEach((item) => {
            item.classList.add('hidden');
        });

        const hasNote = selection.some((resource) => {
            return resource.dataset.type === 'note';
        });

        if (hasNote) {
            requiresNoteSelection.forEach((item) => {
                item.classList.remove('hidden');
            });
        } else {
            requiresNoteSelection.forEach((item) => {
                item.classList.add('hidden');
            });
        }
    }

    if (selection.length && selection.length === filteredResources().length) {
        selectAllButtonSelectedIcon.classList.remove('hidden');
        selectAllButtonNotSelectedIcon.classList.add('hidden');
    } else {
        selectAllButtonSelectedIcon.classList.add('hidden');
        selectAllButtonNotSelectedIcon.classList.remove('hidden');
    }

    for (const resource of resources) {
        if (selection.includes(resource)) {
            const selectedIcon = resource.querySelector('.selected-icon');
            const notSelectedIcon =
                resource.querySelector('.not-selected-icon');

            selectedIcon.classList.remove('hidden');
            notSelectedIcon.classList.add('hidden');
        } else {
            const selectedIcon = resource.querySelector('.selected-icon');
            const notSelectedIcon =
                resource.querySelector('.not-selected-icon');

            selectedIcon.classList.add('hidden');
            notSelectedIcon.classList.remove('hidden');
        }
    }
};

resources.forEach((resource) => {
    const selectButton = resource.querySelector('.select-button');

    selectButton.addEventListener('click', () => {
        if (selection.includes(resource)) {
            selection.splice(selection.indexOf(resource), 1);
        } else {
            selection.push(resource);
        }

        updateUiForSelection();
    });
});

selectAllButton.addEventListener('click', () => {
    if (selection.length === filteredResources().length) {
        selection = [];
    } else {
        selection = Array.from(filteredResources());
    }

    updateUiForSelection();
});

downloadButton.addEventListener('click', () => {
    for (const resource of selection) {
        if (resource.dataset.type === 'note') {
            const text = resource.dataset.text;
            downloadTextFile(`${resource.dataset.name}.txt`, text);
        }
    }
});

deleteButton.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete the selected items?')) {
        return;
    }

    for (const resource of selection) {
        const deleteForm = resource.querySelector('.delete-form');
        const action = deleteForm.action;

        await fetch(action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
        });
    }

    window.location.reload();
});

const removeHiddenElementsFromSelection = () => {
    selection = selection.filter((resource) => {
        return !resource.classList.contains('hidden');
    });

    updateUiForSelection();
};

export { removeHiddenElementsFromSelection };
