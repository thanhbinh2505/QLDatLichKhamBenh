document.addEventListener("DOMContentLoaded", function() {
    let allDoctors = [];
    let currentDoctorId = null;
    let currentDateSelected = null;

    const specialtyList = document.getElementById('specialtyList');
    const doctorList = document.getElementById('doctorList');
    const currentSpecialtyTitle = document.getElementById('currentSpecialtyTitle');

    const bookingModal = document.getElementById('bookingModal');
    const modalContent = document.getElementById('modalContent');
    const inputBacSiId = document.getElementById('inputBacSiId');
    const inputDate = document.getElementById('inputDate');
    const inputTime = document.getElementById('inputTime');
    const bookingAction = document.getElementById('bookingAction');
    const dateSlider = document.getElementById('dateSlider');
    const btnSubmitBooking = document.getElementById('btnSubmitBooking');

    // TẢI BÁC SĨ TỪ API
    async function fetchDoctors() {
        try {
            const response = await fetch('/api/doctors');
            if (!response.ok) throw new Error("Lỗi tải dữ liệu");
            allDoctors = await response.json();

            renderSpecialties();
            renderDoctors('all');
        } catch (error) {
            console.error(error);
            doctorList.innerHTML = `<div class="text-center text-red-500 py-8">Không thể tải danh sách bác sĩ. Vui lòng thử lại.</div>`;
            specialtyList.innerHTML = '';
        }
    }
    // LẤY GIỜ KHÁM API
    async function fetchTimeSlots(doctorId, dateStr) {
        const loading = document.getElementById('loadingSlots');
        const slotsContainer = document.getElementById('slotsContainer');
        const alertBox = document.getElementById('statusAlert');
        const alertText = document.getElementById('statusText');
        const caSangWrap = document.getElementById('caSangWrapper');
        const caChieuWrap = document.getElementById('caChieuWrapper');
        const caSangGrid = document.getElementById('caSangGrid');
        const caChieuGrid = document.getElementById('caChieuGrid');

        loading.classList.remove('hidden');
        slotsContainer.classList.add('hidden');
        alertBox.classList.add('hidden');
        caSangWrap.classList.add('hidden');
        caChieuWrap.classList.add('hidden');

        try {
            const response = await fetch(`/api/gio-kham-bac-si?bacsi_id=${doctorId}&ngay=${dateStr}`);
            let data;

            if(response.ok) {
                data = await response.json();
            } else {
                data = generateMockSlots(dateStr);
            }

            loading.classList.add('hidden');

            if (data.status === 'nghi_phep') {
                alertBox.className = "mb-6 p-4 rounded-xl flex items-start gap-3 bg-red-50 text-red-700 border border-red-200";
                alertText.innerText = data.message || "Bác sĩ không có lịch làm việc trong ngày này.";
                alertBox.classList.remove('hidden');
                return;
            }

            slotsContainer.classList.remove('hidden');
            let hasSang = false, hasChieu = false;
            caSangGrid.innerHTML = '';
            caChieuGrid.innerHTML = '';

            data.slots.forEach(slot => {
                let btnHTML = '';
                if (slot.trang_thai === 'da_dat') {
                    btnHTML = `<button type="button" disabled class="time-slot booked py-2.5 px-1 rounded-xl text-sm font-medium text-center" title="Đã có người đặt">${slot.gio}</button>`;
                } else {
                    btnHTML = `<button type="button" class="time-slot bg-white border border-gray-200 hover:border-primary hover:text-primary text-slate-700 py-2.5 px-1 rounded-xl text-sm font-semibold transition-all text-center shadow-sm cursor-pointer">${slot.gio}</button>`;
                }

                if (slot.buoi === 'sang') {
                    caSangGrid.innerHTML += btnHTML;
                    hasSang = true;
                } else {
                    caChieuGrid.innerHTML += btnHTML;
                    hasChieu = true;
                }
            });

            if(hasSang) caSangWrap.classList.remove('hidden');
            if(hasChieu) caChieuWrap.classList.remove('hidden');

            attachSlotClickEvents();
        } catch (error) {
            console.error(error);
            loading.classList.add('hidden');
            alertBox.className = "mb-6 p-4 rounded-xl flex items-start gap-3 bg-red-50 text-red-700 border border-red-200";
            alertText.innerText = "Lỗi kết nối máy chủ khi lấy khung giờ.";
            alertBox.classList.remove('hidden');
        }
    }
    //GỌI API ĐẶT LỊCH
    if (btnSubmitBooking) {
        btnSubmitBooking.addEventListener('click', async function() {

            const bacsiId = inputBacSiId.value;
            const ngayKham = inputDate.value;
            const gioKham = inputTime.value;

            if (!bacsiId || !ngayKham || !gioKham) {
                alert("Vui lòng chọn thời gian khám!");
                return;
            }
            this.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Đang xử lý...`;
            this.disabled = true;
            lucide.createIcons();

            try {
                const response = await fetch('/api/dat-lich', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bacsi_id: bacsiId,
                        ngay_kham: ngayKham,
                        gio_kham: gioKham
                    })
                });

                const result = await response.json();
                showResultModal(result);

                if (result.success) {
                    fetchTimeSlots(bacsiId, ngayKham);
                    closeBookingModal();
                }
            } catch (error) {
                console.error("Lỗi đặt lịch:", error);
                showResultModal({
                    loai_thong_bao: 'error',
                    message: "Có lỗi xảy ra khi kết nối máy chủ. Vui lòng thử lại!"
                });
            } finally {
                this.innerHTML = `Xác nhận đặt lịch <i data-lucide="arrow-right" class="w-4 h-4"></i>`;
                this.disabled = false;
                lucide.createIcons();
            }
        });
    }


    // RENDER MENU BÊN TRÁI
    function renderSpecialties() {
        const specialties = [...new Set(allDoctors.map(doc => doc.chuyenKhoa))].filter(Boolean);

        let html = `<li class="specialty-item active cursor-pointer px-5 py-3.5 hover:bg-slate-50 transition-colors border-l-4 border-transparent" data-spec="all">Tất cả chuyên khoa</li>`;

        specialties.forEach(spec => {
            html += `<li class="specialty-item cursor-pointer px-5 py-3.5 hover:bg-slate-50 transition-colors border-l-4 border-transparent text-slate-700" data-spec="${spec}">${spec}</li>`;
        });

        specialtyList.innerHTML = html;

        document.querySelectorAll('.specialty-item').forEach(item => {
            item.addEventListener('click', function() {
                document.querySelectorAll('.specialty-item').forEach(el => {
                    el.classList.remove('active', 'border-primary', 'bg-blue-50', 'text-primary', 'font-bold');
                    el.classList.add('border-transparent', 'text-slate-700');
                });
                this.classList.add('active', 'border-primary', 'bg-blue-50', 'text-primary', 'font-bold');
                this.classList.remove('border-transparent', 'text-slate-700');

                // Lấy tên chuyên khoa mà người dùng vừa click (vd: "Thần Kinh")
                const tenChuyenKhoa = this.innerText;

                // Gọi API lọc danh sách bác sĩ
                renderDoctors(this.getAttribute('data-spec'));

                // GỌI HÀM CẬP NHẬT BREADCRUMB Ở ĐÂY
                capNhatBreadcrumb(tenChuyenKhoa);
            });
        });
    }

    // HÀM CẬP NHẬT BREADCRUMB
    function capNhatBreadcrumb(tenChuyenKhoa) {
        const bcDatLichText = document.getElementById('bcDatLichText');
        const bcSpecialtyDivider = document.getElementById('bcSpecialtyDivider');
        const bcSpecialtyName = document.getElementById('bcSpecialtyName');

        // Nếu có chọn chuyên khoa và không phải là "Tất cả chuyên khoa"
        if (tenChuyenKhoa && tenChuyenKhoa !== "Tất cả chuyên khoa") {
            bcDatLichText.classList.remove('text-[#28539e]', 'font-semibold');

            bcSpecialtyDivider.classList.remove('hidden');
            bcSpecialtyName.classList.remove('hidden');
            bcSpecialtyName.textContent = tenChuyenKhoa;
        } else {
            // Nếu chọn "Tất cả chuyên khoa"
            bcDatLichText.classList.add('text-[#28539e]', 'font-semibold');

            bcSpecialtyDivider.classList.add('hidden');
            bcSpecialtyName.classList.add('hidden');
            bcSpecialtyName.textContent = "";
        }
    }

    // RENDER CARD BÁC SĨ
    function renderDoctors(specialtyFilter) {
        currentSpecialtyTitle.innerText = specialtyFilter === 'all' ? "Tất cả bác sĩ" : specialtyFilter;

        let filtered = allDoctors;
        if (specialtyFilter !== 'all') {
            filtered = allDoctors.filter(doc => doc.chuyenKhoa === specialtyFilter);
        }

        if (filtered.length === 0) {
            doctorList.innerHTML = `<div class="text-center py-10 bg-white rounded-xl border border-gray-100 text-slate-500">Không có bác sĩ nào thuộc chuyên khoa này.</div>`;
            return;
        }

        doctorList.innerHTML = filtered.map(doc => {
            const avatarUrl = doc.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(doc.hoTen)}&background=f0f9ff&color=0284c7&size=200`;
            return `
                <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 sm:p-6 flex flex-col sm:flex-row gap-6 hover:shadow-md transition-shadow">
                    <div class="shrink-0 mx-auto sm:mx-0">
                        <img src="${avatarUrl}" class="w-32 h-32 sm:w-40 sm:h-40 object-cover border border-gray-100" style="border-radius: 12px;">
                    </div>
                    <div class="flex-1 flex flex-col justify-between">
                        <div>
                            <h3 class="text-xl font-bold text-[#28539e] mb-2 uppercase">BS. ${doc.hoTen}</h3>
                            <div class="text-sm text-slate-600 space-y-2 mb-4">
                                <p><span class="font-semibold text-slate-700">Chuyên khoa:</span> ${doc.chuyenKhoa}</p>
                                <p class="flex items-center gap-1.5"><i data-lucide="map-pin" class="w-4 h-4 text-slate-400"></i> Thành phố Hồ Chí Minh</p>
                            </div>
                        </div>
                        <div class="flex gap-3 mt-auto">
                            <button class="px-5 py-2.5 bg-slate-100 text-[#28539e] text-sm font-semibold rounded-lg hover:bg-slate-200 transition-colors">Xem chi tiết</button>
                            <button onclick="openBookingModal('${doc.id}', '${doc.hoTen}')" class="px-5 py-2.5 bg-[#60a5fa] hover:bg-[#3b82f6] text-white text-sm font-semibold rounded-lg flex items-center gap-2 shadow-sm transition-colors">
                                <i data-lucide="calendar-plus" class="w-4 h-4"></i> Đặt lịch khám
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        lucide.createIcons();
    }
   function initDateSlider() {
        const daysOfWeek = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
        const today = new Date();
        const currentMonthDisplay = document.getElementById('currentMonthDisplay');
        if (currentMonthDisplay) {
            currentMonthDisplay.innerText = 'THÁNG ' + (today.getMonth() + 1) + '/' + today.getFullYear();
        }
        dateSlider.innerHTML = '';
        bookingAction.classList.add('hidden');
        inputTime.value = "";
        let activeCard = null;
        let todayCard = null;

        const START_OFFSET = -15;
        const END_OFFSET = 40;

        for (let i = START_OFFSET; i <= END_OFFSET; i++) {
            let nextDate = new Date();
            nextDate.setDate(today.getDate() + i);

            let dateNum = nextDate.getDate().toString().padStart(2, '0');
            let monthNum = (nextDate.getMonth() + 1).toString().padStart(2, '0');
            let optionValue = `${nextDate.getFullYear()}-${monthNum}-${dateNum}`;

            let card = document.createElement('button');
            card.className = "date-card snap-center shrink-0 flex flex-col items-center justify-center w-[72px] h-[72px] rounded-2xl border border-gray-200 bg-white cursor-pointer transition-all hover:border-primary group";

            card.dataset.value = optionValue;
            card.dataset.text = `${dateNum}/${monthNum}`;
            card.dataset.month = nextDate.getMonth() + 1;
            card.dataset.year = nextDate.getFullYear();

            let dayLabel = (i === 0) ? 'Hôm nay' : daysOfWeek[nextDate.getDay()];

            card.innerHTML = `<span class="date-day text-xs font-bold text-slate-400 mb-0.5">${dayLabel}</span>
                              <span class="date-date text-lg font-extrabold text-slate-700">${dateNum}</span>`;

            if (i === 0) {
                card.classList.add('active');
                activeCard = card;
                todayCard = card;
                currentDateSelected = optionValue;
                inputDate.value = optionValue;
                fetchTimeSlots(currentDoctorId, optionValue);
            }

            card.addEventListener('click', function() {
                if (activeCard) activeCard.classList.remove('active');
                this.classList.add('active');
                activeCard = this;

                currentDateSelected = this.dataset.value;
                inputDate.value = this.dataset.value;
                bookingAction.classList.add('hidden');
                inputTime.value = "";

                if (currentMonthDisplay) {
                    currentMonthDisplay.innerText = 'THÁNG ' + this.dataset.month + '/' + this.dataset.year;
                }

                fetchTimeSlots(currentDoctorId, this.dataset.value);
            });

            dateSlider.appendChild(card);
        }

        setTimeout(() => {
            if (todayCard) {
                const scrollPos = todayCard.offsetLeft - (dateSlider.clientWidth / 2) + (todayCard.clientWidth / 2);
                dateSlider.scrollTo({ left: scrollPos, behavior: 'smooth' });
            }
        }, 100);
    }
    function attachSlotClickEvents() {
        const slots = document.querySelectorAll('#slotsContainer .time-slot:not([disabled])');
        slots.forEach(slot => {
            slot.addEventListener('click', function() {
                const isAlreadySelected = this.classList.contains('selected');
                slots.forEach(s => s.classList.remove('selected'));
                if (isAlreadySelected) {
                inputTime.value = "";
                const selectedTimeTextSpan = document.querySelector('#selectedTimeText span');
                if (selectedTimeTextSpan) {
                    selectedTimeTextSpan.innerText = "Chưa chọn giờ";
                }
                bookingAction.classList.add('hidden');
                bookingAction.classList.remove('flex');

            } else {
                this.classList.add('selected');

                let timeText = this.innerText;
                inputTime.value = timeText;
                let activeDateText = document.querySelector('.date-card.active').dataset.text;
                const selectedTimeTextSpan = document.querySelector('#selectedTimeText span');
                if (selectedTimeTextSpan) {
                    selectedTimeTextSpan.innerText = `${timeText} | Ngày ${activeDateText}`;
                }
                bookingAction.classList.remove('hidden');
                bookingAction.classList.add('flex');
            }
            });
        });
    }
    function showResultModal(data) {
        const container = document.getElementById('resultModalContainer');
        const oldModal = document.getElementById('resultModal');
        if (oldModal) oldModal.remove();

        let modalContent = '';

        if (data.loai_thong_bao === 'auth_required') {
            modalContent = `
                <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 sm:p-8 text-center animate-fade-in-up">
                    <div class="w-20 h-20 bg-orange-100 text-orange-500 rounded-full flex items-center justify-center mx-auto mb-5 shadow-inner">
                        <i data-lucide="shield-alert" class="w-10 h-10"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-slate-800 mb-2">Yêu cầu đăng nhập</h3>
                    <p class="text-slate-600 mb-8 leading-relaxed">${data.message}</p>
                    <div class="flex flex-col sm:flex-row gap-3 justify-center">
                        <button onclick="document.getElementById('resultModal').remove()" class="w-full sm:w-auto px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition-colors">Để sau</button>
                        <a href="/login?next=/dat-lich" class="w-full sm:w-auto px-6 py-3 bg-[#28539e] hover:bg-blue-800 text-white font-bold rounded-xl shadow-md transition-colors">Đăng nhập ngay</a>
                    </div>
                </div>`;
        } else if (data.loai_thong_bao === 'success') {
            modalContent = `
                <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-fade-in-up">
                    <div class="bg-gradient-to-br from-green-400 to-green-600 p-8 text-center relative overflow-hidden">
                        <div class="w-20 h-20 bg-white text-green-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <i data-lucide="check-circle-2" class="w-12 h-12"></i>
                        </div>
                        <h3 class="text-2xl font-extrabold text-white tracking-tight">Thành công!</h3>
                        <p class="text-green-50 mt-1 font-medium">${data.message}</p>
                    </div>
                    <div class="p-6 sm:p-8 bg-slate-50">
                        <div class="bg-white border border-gray-100 rounded-2xl p-5 space-y-4 shadow-sm relative">
                            <div class="flex justify-between items-center border-b border-dashed border-gray-200 pb-4">
                                <span class="text-slate-500 text-sm font-medium flex items-center gap-1.5"><i data-lucide="stethoscope" class="w-4 h-4"></i> Bác sĩ:</span>
                                <span class="font-extrabold text-[#28539e] text-right">${data.booking_info.doctor_name}</span>
                            </div>
                            <div class="flex justify-between items-center border-b border-dashed border-gray-200 pb-4">
                                <span class="text-slate-500 text-sm font-medium flex items-center gap-1.5"><i data-lucide="calendar" class="w-4 h-4"></i> Ngày khám:</span>
                                <span class="font-bold text-slate-800">${data.booking_info.date}</span>
                            </div>
                            <div class="flex justify-between items-center pt-1">
                                <span class="text-slate-500 text-sm font-medium flex items-center gap-1.5"><i data-lucide="clock" class="w-4 h-4"></i> Khung giờ:</span>
                                <span class="font-bold text-primary bg-blue-50 px-3 py-1 rounded-lg border border-blue-100">${data.booking_info.time}</span>
                            </div>
                        </div>
                        <button onclick="document.getElementById('resultModal').remove()" class="mt-8 w-full py-3.5 bg-slate-800 hover:bg-slate-900 text-white font-bold rounded-xl transition-all shadow-md">Đóng</button>
                    </div>
                </div>`;
        } else {
            modalContent = `
                <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 sm:p-8 text-center animate-fade-in-up">
                    <div class="w-20 h-20 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-5 shadow-inner">
                        <i data-lucide="x-circle" class="w-10 h-10"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-slate-800 mb-2">Thao tác thất bại</h3>
                    <p class="text-slate-600 mb-8 leading-relaxed">${data.message}</p>
                    <button onclick="document.getElementById('resultModal').remove()" class="w-full py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition-colors">Đóng</button>
                </div>`;
        }

        const fullModalHtml = `
            <style>
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(20px) scale(0.95); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }
                .animate-fade-in-up { animation: fadeInUp 0.4s ease-out forwards; }
            </style>
            <div id="resultModal" class="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/70 backdrop-blur-sm p-4">
                ${modalContent}
            </div>
        `;

        container.innerHTML = fullModalHtml;
        lucide.createIcons();
    }

    // MODAL LỊCH KHÁM
    window.openBookingModal = function(doctorId, doctorName) {
        currentDoctorId = doctorId;
        inputBacSiId.value = doctorId;
        document.getElementById('modalDoctorName').innerText = `BS. ${doctorName}`;

        bookingModal.classList.remove('hidden');
        setTimeout(() => {
            bookingModal.classList.remove('opacity-0');
            modalContent.classList.remove('scale-95');
        }, 10);

        initDateSlider();
    }

    window.closeBookingModal = function() {
        bookingModal.classList.add('opacity-0');
        modalContent.classList.add('scale-95');
        setTimeout(() => { bookingModal.classList.add('hidden'); }, 300);
    }

    window.scrollDate = function(dir) {
        dateSlider.scrollBy({ left: dir === 'left' ? -200 : 200, behavior: 'smooth' });
    }
    fetchDoctors();
});


