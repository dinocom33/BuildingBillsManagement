document.addEventListener('DOMContentLoaded', function () {
    const textarea = document.getElementById('text');

    function autoResize() {
        this.style.height = 'auto';  // Reset height
        this.style.height = (this.scrollHeight) + 'px';  // Set height based on content
    }

    textarea.addEventListener('input', autoResize);  // Attach the event listener
});