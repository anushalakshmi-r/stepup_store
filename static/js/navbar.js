const dropdownItems = document.querySelectorAll('.category-nav .nav-dropdown-item');

function closeDropdowns() {
    dropdownItems.forEach(function(item) {
        item.classList.remove('open');
        item.querySelector('.nav-trigger-link').setAttribute('aria-expanded', 'false');
    });
}

document.addEventListener('click', function(event) {
    const clickedElement = event.target instanceof Element ? event.target : null;
    const trigger = clickedElement && clickedElement.closest('.category-nav .nav-trigger-link');
    const item = trigger && trigger.closest('.nav-dropdown-item');

    if (item) {
        if (item.classList.contains('category-hover-item')) {
            closeDropdowns();
            return;
        }

        event.preventDefault();
        const shouldOpen = !item.classList.contains('open');
        closeDropdowns();
        if (shouldOpen) {
            item.classList.add('open');
            trigger.setAttribute('aria-expanded', 'true');
        }
        return;
    }

    closeDropdowns();
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeDropdowns();
    }
});
