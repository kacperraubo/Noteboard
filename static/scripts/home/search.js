import { removeHiddenElementsFromSelection } from './select.js';

const resources = document.querySelectorAll('.resource-list .resource');
const resourceToNameMap = new Map();
const noSearchResultsFound = document.querySelector('.no-search-results');

const searchInput = document.querySelector('.search-bar');

for (const resource of resources) {
    const name = resource.dataset.name;
    resourceToNameMap.set(resource, name);
}

const applySearch = () => {
    const searchValue = searchInput.value.toLowerCase();
    let found = false;

    for (const resource of resources) {
        const name = resourceToNameMap.get(resource).toLowerCase();

        if (name.includes(searchValue)) {
            found = true;
            resource.classList.remove('hidden');
        } else {
            resource.classList.add('hidden');
        }
    }

    if (!found) {
        noSearchResultsFound.classList.remove('hidden');
    } else {
        noSearchResultsFound.classList.add('hidden');
    }

    removeHiddenElementsFromSelection();
};

searchInput.addEventListener('input', applySearch);

const updateNameForResource = (resource, name) => {
    resourceToNameMap.set(resource, name);
};

export { applySearch, updateNameForResource };
