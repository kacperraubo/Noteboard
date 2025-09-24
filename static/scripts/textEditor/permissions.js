import { updatePermission } from '../api/updatePermission.js';
import { isAnonymous } from '../anonymous.js';

const roomId = document.querySelector('[name="room-id"]').value;
const toggleViewPermissionButton = document.querySelector(
    '.privacy-settings .view-setting',
);
const toggleEditPermissionButton = document.querySelector(
    '.privacy-settings .edit-setting',
);

let isViewable = toggleViewPermissionButton.dataset.isViewable === 'true';
let isEditable = toggleEditPermissionButton.dataset.isEditable === 'true';

const updateViewPermissionButtons = () => {
    const activeIcon = toggleViewPermissionButton.querySelector('.active-icon');
    const inactiveIcon =
        toggleViewPermissionButton.querySelector('.inactive-icon');

    if (isViewable) {
        activeIcon.classList.add('hidden');
        inactiveIcon.classList.remove('hidden');
        toggleViewPermissionButton.classList.remove('active');
    } else {
        activeIcon.classList.remove('hidden');
        inactiveIcon.classList.add('hidden');
        toggleViewPermissionButton.classList.add('active');
    }
};

const updateEditPermissionButtons = () => {
    const activeIcon = toggleEditPermissionButton.querySelector('.active-icon');
    const inactiveIcon =
        toggleEditPermissionButton.querySelector('.inactive-icon');

    if (isEditable) {
        activeIcon.classList.add('hidden');
        inactiveIcon.classList.remove('hidden');
        toggleEditPermissionButton.classList.remove('active');
    } else {
        activeIcon.classList.remove('hidden');
        inactiveIcon.classList.add('hidden');
        toggleEditPermissionButton.classList.add('active');
    }
};

if (!isAnonymous) {
    toggleViewPermissionButton.addEventListener('click', async () => {
        const value = !isViewable;

        const response = await updatePermission({
            roomId,
            permission: 'publicity',
            value,
        });

        if (response.success) {
            isViewable = response.payload.is_public;
            isEditable = response.payload.is_editable;

            updateViewPermissionButtons();
            updateEditPermissionButtons();

            toggleViewPermissionButton.dataset.isViewable = isViewable;
        } else {
            alert('Failed to update view permission.');
            console.error(response);
        }
    });
} else {
    toggleViewPermissionButton.addEventListener('click', () => {
        alert('You need to sign in to change the view permission.');
    });
}

if (!isAnonymous) {
    toggleEditPermissionButton.addEventListener('click', async () => {
        const value = !isEditable;

        const response = await updatePermission({
            roomId,
            permission: 'editable',
            value,
        });

        if (response.success) {
            isViewable = response.payload.is_public;
            isEditable = response.payload.is_editable;

            updateViewPermissionButtons();
            updateEditPermissionButtons();

            toggleEditPermissionButton.dataset.isEditable = value;
        } else {
            alert('Failed to update edit permission.');
            console.error(response);
        }
    });
} else {
    toggleEditPermissionButton.addEventListener('click', () => {
        alert('You need to sign in to change the edit permission.');
    });
}
