import { escapeRegex } from '../utilities/regex.js';

const searchInput = document.querySelector('.search-bar');
const actualTextArea = document.querySelector('.text-area textarea');
const fakeTextAreaForSearching = document.querySelector(
    '.text-area-for-searching',
);

searchInput.addEventListener('input', () => {
    let query = searchInput.value.toLowerCase().trim();

    if (query === '') {
        actualTextArea.classList.remove('hidden');
        fakeTextAreaForSearching.classList.add('hidden');
        fakeTextAreaForSearching.innerHTML = '';
        return;
    } else {
        actualTextArea.classList.add('hidden');
        fakeTextAreaForSearching.classList.remove('hidden');
    }

    const text = actualTextArea.value;
    query = escapeRegex(query);
    const matchCount = (text.match(new RegExp(query, 'gi')) || []).length;

    if (matchCount === 0) {
        fakeTextAreaForSearching.innerHTML = '';
    } else {
        const highlightedText = text
            .split('\n')
            .map((line) =>
                line.replace(
                    new RegExp(`(${query})`, 'gi'),
                    '<span class="highlight">$1</span>',
                ),
            )
            .join('<br>');

        fakeTextAreaForSearching.innerHTML = highlightedText;

        const firstMatch = fakeTextAreaForSearching.querySelector('.highlight');

        if (firstMatch) {
            firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});
