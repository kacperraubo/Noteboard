document.addEventListener('click', function(event) {
    const existedInput = document.querySelector('.jsNameInput');
    if (existedInput) {
        const existedInputParentEl = existedInput.parentNode;
        if (event.target !== existedInputParentEl && !existedInputParentEl.contains(event.target)){
                existedInputParentEl.classList.add('hidden_view');
                existedInputParentEl.previousElementSibling.classList.remove('hidden_view');
            }
    }
});