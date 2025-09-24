import { editResourceName } from '../api/editResourceName.js';

const editNameButton = document.querySelector('.resource-history .edit-button');
const nameElement = document.querySelector(
    '.resource-history .resource.current .name',
);

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
        window.location.reload();
    } else {
        alert('An error occurred while updating the name');
    }
});
