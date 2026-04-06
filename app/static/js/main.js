function submitTaoLich() {
    // Lấy dữ liệu từ form
    const bacsi_id = document.getElementById('bacsiSelect').value;
    const ngay_lam_viec = document.getElementById('ngayLamViec').value;

    // Lọc lấy tất cả các checkbox khung giờ đang được tick chọn
    const checkedBoxes = document.querySelectorAll('.khung-gio-cb:checked');
    const danh_sach_gio = Array.from(checkedBoxes).map(cb => cb.value);

    // Kiểm tra validation cơ bản
    if (!bacsi_id) { alert("Vui lòng chọn bác sĩ!"); return; }
    if (!ngay_lam_viec) { alert("Vui lòng chọn ngày làm việc!"); return; }
    if (danh_sach_gio.length === 0) { alert("Vui lòng chọn ít nhất 1 khung giờ!"); return; }

    // Gửi dữ liệu xuống Server (API)
    fetch('/api/admin/tao-lich', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            bacsi_id: bacsi_id,
            ngay_lam_viec: ngay_lam_viec,
            danh_sach_gio: danh_sach_gio
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(data.msg);
            location.reload(); // Tải lại trang để bảng dữ liệu cập nhật
        } else {
            alert("Lỗi: " + data.msg); // Báo lỗi nếu trùng lịch hoặc lố 20 ca
        }
    })
    .catch(err => {
        console.error(err);
        alert("Có lỗi kết nối máy chủ!");
    });
}