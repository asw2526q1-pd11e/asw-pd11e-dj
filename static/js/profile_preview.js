document.addEventListener('DOMContentLoaded', function() {

    function setupImagePreview(inputId, previewId, removeBtnId, deleteInputId) {
        const input = document.getElementById(inputId);
        const preview = document.getElementById(previewId);
        const removeButton = document.getElementById(removeBtnId);
        const deleteInput = document.getElementById(deleteInputId);

        if (!input || !preview || !removeButton || !deleteInput) return;

        if (preview.src && preview.src !== window.location.href) {
            preview.style.display = 'block';
            removeButton.style.display = 'flex';
        }

        input.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = e => {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    removeButton.style.display = 'flex';
                    deleteInput.value = 'false';
                };
                reader.readAsDataURL(file);
            }
        });

        removeButton.addEventListener('click', function () {
            preview.src = '';
            preview.style.display = 'none';
            input.value = '';
            removeButton.style.display = 'none';
            deleteInput.value = 'true';
        });
    }

    setupImagePreview('id_avatar', 'avatarPreview', 'avatarRemoveBtn', 'deleteAvatarInput');
    setupImagePreview('id_banner', 'bannerPreview', 'bannerRemoveBtn', 'deleteBannerInput');
});
