
    function submitTaoLich() {
        const bacsi_id = document.getElementById('bacsiSelect').value;
        const ngay_lam_viec = document.getElementById('ngayLamViec').value;

        const checkedBoxes = document.querySelectorAll('.khung-gio-cb:checked');
        const danh_sach_gio = Array.from(checkedBoxes).map(cb => cb.value);

        if (!bacsi_id) { alert("Vui lòng chọn bác sĩ!"); return; }
        if (!ngay_lam_viec) { alert("Vui lòng chọn ngày làm việc!"); return; }
        if (danh_sach_gio.length === 0) { alert("Vui lòng chọn ít nhất 1 khung giờ!"); return; }

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
                location.reload()
            } else {
                alert("Lỗi: " + data.msg);
            }
        })
        .catch(err => {
            console.error(err);
            alert("Có lỗi kết nối máy chủ!");
        });
    }

    function chonCa(ca) {
        const checkboxes = document.querySelectorAll('.khung-gio-cb');
        checkboxes.forEach(cb => {
            const gio = parseInt(cb.value.split(':')[0]);
            if (ca === 'sang') {
                cb.checked = (gio >= 8 && gio < 12);
            } else if (ca === 'chieu') {
                cb.checked = (gio >= 13 && gio < 17);
            } else if (ca === 'cangay') {
                cb.checked = true;
            } else if (ca === 'clear') {
                cb.checked = false;
            }
        });
    }

    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

 let currentLichData = {}; // Lưu thông tin để gửi API

function openModal(lichId) {
    document.getElementById('modalLich').classList.remove('hidden');

    fetch(`/api/admin/chi-tiet-lich/${lichId}`)
        .then(res => res.json())
        .then(res => {
            if(res.success) {
                const d = res.data;
                currentLichData = { bacsi_id: d.bacsi_id, ngay: d.raw_date };

                document.getElementById('modalTitle').innerText = `BS. ${d.ten_bacsi}`;
                document.getElementById('modalSubTitle').innerText = `Ngày làm việc: ${d.ngay_lam_viec}`;

                // 1. Hiển thị các ca đã có
                let htmlDaCo = "";
                let gioDaTao = [];
                d.ca_lam_viec.forEach(ca => {
                    gioDaTao.push(ca.time);
                    const colorClass = ca.is_booked ? "bg-red-100 text-red-700 border-red-200" : "bg-green-100 text-green-700 border-green-200";
                    const icon = ca.is_booked ? "user-check" : "clock";
                    htmlDaCo += `<span class="px-3 py-1 border rounded-lg text-xs font-bold flex items-center gap-1 ${colorClass}"><i data-lucide="${icon}" class="w-3 h-3"></i>${ca.time}</span>`;
                });
                document.getElementById('caDaCo').innerHTML = htmlDaCo;

                // 2. Hiển thị các ca còn trống để thêm (Lọc bỏ giờ đã tạo)
                const fullHours = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30'];
                let htmlTrong = "";
                fullHours.forEach(h => {
                    if(!gioDaTao.includes(h)) {
                        htmlTrong += `
                        <label class="flex items-center gap-2 p-2 border border-gray-200 rounded-lg cursor-pointer hover:border-primary has-[:checked]:bg-blue-50 transition-all">
                            <input type="checkbox" value="${h}" class="add-more-cb w-4 h-4 accent-primary">
                            <span class="text-xs font-bold">${h}</span>
                        </label>`;
                    }
                });
                document.getElementById('caConTrong').innerHTML = htmlTrong || '<p class="text-xs text-slate-400">Đã hết khung giờ trống.</p>';

                if(typeof lucide !== 'undefined') lucide.createIcons();
            }
        });
}

function closeModal() {
        document.getElementById('modalLich').classList.add('hidden');
    }

function saveMoreSchedule() {
    const checked = document.querySelectorAll('.add-more-cb:checked');
    const ds_gio = Array.from(checked).map(c => c.value);

    if(ds_gio.length === 0) return alert("Vui lòng chọn ít nhất 1 ca mới!");

    fetch('/api/admin/tao-lich', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            bacsi_id: currentLichData.bacsi_id,
            ngay_lam_viec: currentLichData.ngay,
            danh_sach_gio: ds_gio
        })
    }).then(res => res.json()).then(data => {
        if(data.success) {
            alert("Đã bổ sung ca khám thành công!");
            location.reload();
        } else {
            alert("Lỗi: " + data.msg);
        }
    });
}