document.addEventListener('DOMContentLoaded', function() {
    const togglePasswordBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    const eyeIcon = document.getElementById('eyeIcon');

    const termsCheckbox = document.getElementById('termsCheckbox');
    const submitBtn = document.getElementById('submitBtn');

    // 1. Chức năng Ẩn/Hiện mật khẩu
    togglePasswordBtn.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Đổi icon
        if (type === 'text') {
            eyeIcon.setAttribute('data-lucide', 'eye-off');
        } else {
            eyeIcon.setAttribute('data-lucide', 'eye');
        }
        lucide.createIcons(); // Re-render icon
    });

    // 2. Chức năng Enable/Disable nút Submit dựa vào Checkbox
    termsCheckbox.addEventListener('change', function() {
        if (this.checked) {
            submitBtn.removeAttribute('disabled');
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            submitBtn.setAttribute('disabled', 'true');
            submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    });

});