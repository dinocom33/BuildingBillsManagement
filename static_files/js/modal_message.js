document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('button[data-bs-target="#viewMessageModal"]');

    buttons.forEach(function (button) {
        button.addEventListener('click', function () {
            const messageTitle = button.getAttribute('data-message-title');
            const messageText = button.getAttribute('data-message-text');

            document.getElementById('message-title').value = messageTitle;
            document.getElementById('message-text').value = messageText;
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const messageText = document.getElementById('message-text');

    function autoResize() {
        messageText.style.height = 'auto';
        messageText.style.height = (messageText.scrollHeight) + 'px';
    }

    // Resize textarea when the modal is shown
    const modal = document.getElementById('viewMessageModal');
    modal.addEventListener('shown.bs.modal', autoResize);
});