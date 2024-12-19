document.addEventListener("DOMContentLoaded", function () {
    const viewMessageModal = document.getElementById("viewMessageModal");

    viewMessageModal.addEventListener("show.bs.modal", function (event) {
        const button = event.relatedTarget; // Button that triggered the modal
        const messageId = button.getAttribute("data-message-id");
        const messageTitle = button.getAttribute("data-message-title");
        const messageText = button.getAttribute("data-message-text");
        const fileUrl = button.getAttribute("data-message-file"); // Custom attribute for file URL
        const fileType = button.getAttribute("data-message-file-type"); // Custom attribute for file type

        // Populate title and text fields
        document.getElementById("message-title").value = messageTitle;
        document.getElementById("message-text").value = messageText;

        // Populate file preview
        const filePreviewContainer = document.getElementById("file-preview");
        filePreviewContainer.innerHTML = ""; // Clear previous content

        if (fileUrl) {
            if (fileType.startsWith("image/")) {
                // Display image
                const img = document.createElement("img");
                img.src = fileUrl;
                img.alt = "Uploaded Image";
                img.classList.add("img-fluid", "rounded");
                filePreviewContainer.appendChild(img);
            } else if (fileType === "application/pdf") {
                // Display PDF
                const iframe = document.createElement("iframe");
                iframe.src = fileUrl;
                iframe.classList.add("w-100");
                iframe.style.height = "500px";
                filePreviewContainer.appendChild(iframe);
            } else {
                // For unsupported file types, provide a download link
                const link = document.createElement("a");
                link.href = fileUrl;
                link.textContent = "Click here to view the file";
                link.target = "_blank";
                filePreviewContainer.appendChild(link);
            }
        } else {
            filePreviewContainer.textContent = "No file attached.";
        }
    });
});
