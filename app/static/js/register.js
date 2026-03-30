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

//    const form = document.getElementById('registrationForm')
//    form.addEventListener('submit', async (e) => {
//        e.preventDefault(); // Ngăn trình duyệt load lại trang
//
//        // Lấy lại HTML gốc của nút để khôi phục sau khi gọi API xong
//        const originalBtnContent = submitBtn.innerHTML;
//
//        // Chuyển nút sang trạng thái Loading
//        submitBtn.disabled = true;
//        submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 mr-2 animate-spin"></i> Đang xử lý...`;
//        lucide.createIcons(); // Hiển thị icon xoay (spinner)
//
//        // Gom dữ liệu từ Form (Yêu cầu các thẻ input PHẢI CÓ thuộc tính name="")
//        const formData = new FormData(form);
//        const data = Object.fromEntries(formData.entries());
//
//        try {
//            // Thay URL dưới đây bằng API Endpoint thực tế của Backend
//            const API_URL = 'https://api.phongkhamcuaban.com/v1/auth/register';
//
//            // Gọi API bằng Fetch
//            const response = await fetch(API_URL, {
//                method: 'POST',
//                headers: {
//                    'Content-Type': 'application/json',
//                },
//                body: JSON.stringify(data) // Chuyển dữ liệu thành chuỗi JSON
//            });
//
//            // Lấy kết quả trả về từ server
//            const result = await response.json();
//
//            // Kiểm tra HTTP Status Code (thường 200-299 là thành công)
//            if (!response.ok) {
//                // Nếu lỗi, ném lỗi ra khối catch
//                throw new Error(result.message || 'Đăng ký thất bại, vui lòng thử lại!');
//            }
//
//            // --- XỬ LÝ KHI ĐĂNG KÝ THÀNH CÔNG ---
//            alert('Chúc mừng! Bạn đã đăng ký thành công.');
//            form.reset(); // Xóa trắng form
//            termsCheckbox.checked = false; // Bỏ tích checkbox
//
//            // Chuyển hướng người dùng sang trang đăng nhập (Tùy chọn)
//            // window.location.href = '/login.html';
//
//        } catch (error) {
//            // --- XỬ LÝ KHI CÓ LỖI ---
//            console.error('Lỗi API:', error);
//            alert(`Lỗi: ${error.message}`);
//        } finally {
//            // --- KHÔI PHỤC TRẠNG THÁI NÚT DÙ THÀNH CÔNG HAY THẤT BẠI ---
//            submitBtn.innerHTML = originalBtnContent;
//            submitBtn.disabled = !termsCheckbox.checked; // Disabled lại nếu chưa tích checkbox
//            lucide.createIcons(); // Render lại mũi tên arrow-right
//        }
//    });
});