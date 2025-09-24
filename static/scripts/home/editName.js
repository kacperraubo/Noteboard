import { editResourceName } from '../api/editResourceName.js';
import { applySearch, updateNameForResource } from './search.js';

const resources = document.querySelectorAll('.resource-list .resource');
const currentFolder = document.querySelector(
    '.resource-history .current-folder',
);

resources.forEach((resource) => {
    const editNameButton = resource.querySelector('.edit-button');

    editNameButton.addEventListener('click', async (event) => {
        const newName = prompt('Enter new name', resource.dataset.name);

        if (!newName || !newName.trim()) {
            return;
        }

        const response = await editResourceName({
            resourceId: resource.dataset.id,
            resourceToken: resource.dataset.token,
            newName,
        });

        if (response.success) {
            resource.dataset.name = newName;
            resource.querySelector('.name').textContent = newName;
            updateNameForResource(resource, newName);
            applySearch();
        } else {
            alert('An error occurred while updating the name');
        }
    });
});

if (currentFolder) {
    const editNameButton = currentFolder.querySelector('.edit-button');

    editNameButton.addEventListener('click', async (event) => {
        const newName = prompt('Enter new name', editNameButton.dataset.name);

        if (!newName || !newName.trim()) {
            return;
        }

        const response = await editResourceName({
            resourceId: editNameButton.dataset.id,
            resourceToken: editNameButton.dataset.token,
            newName,
        });

        if (response.success) {
            editNameButton.dataset.name = newName;
            currentFolder.querySelector('.name').textContent = newName;
            updateNameForResource(currentFolder, newName);
        } else {
            alert('An error occurred while updating the name');
        }
    });
}
