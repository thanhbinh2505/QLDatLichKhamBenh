lucide.createIcons();

// 1. MOCK DATA
const days = [
    { id: 'T2', name: 'Thứ 2' },
    { id: 'T3', name: 'Thứ 3' },
    { id: 'T4', name: 'Thứ 4' },
    { id: 'T5', name: 'Thứ 5' },
    { id: 'T6', name: 'Thứ 6' },
    { id: 'T7', name: 'Thứ 7' },
    { id: 'CN', name: 'Chủ nhật' }
];

// 2. STATE MANAGEMENT
let schedule = {};
// dsCaLam được truyền từ HTML sang
days.forEach(d => {
    schedule[d.id] = {};
    dsCaLam.forEach(ca => {
        schedule[d.id][ca.id] = [];
    });
});

let currentEditCell = null; // vd: { dayId: 'T2', shiftId: 1 }
let tempSelectedDoctors = new Set();
let doctors = []; // Khai báo mảng chứa bác sĩ

// 3. INITIALIZATION
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/doctors');
        doctors = await response.json();

        setDefaultDates();
        renderGridHeaders();
        renderAllCells(); // Render động các dòng theo mảng dsCaLam

        // Search event
        document.getElementById('doctorSearch').addEventListener('input', (e) => {
            renderPopoverList(e.target.value.toLowerCase());
        });
    } catch (error) {
        console.error("Lỗi khi load bác sĩ:", error);
    }
});

function setDefaultDates() {
    if (typeof defaultStartDate !== 'undefined' && defaultStartDate) {
        document.getElementById('startDate').value = defaultStartDate;
        document.getElementById('endDate').value = defaultEndDate;
    } else {
        const today = new Date();
        const nextWeek = new Date(today);
        nextWeek.setDate(today.getDate() + 6);
        document.getElementById('startDate').value = today.toISOString().split('T')[0];
        document.getElementById('endDate').value = nextWeek.toISOString().split('T')[0];
    }
}

// 4. RENDER GRID
function renderGridHeaders() {
    const headerContainer = document.getElementById('grid-headers');
    headerContainer.innerHTML = days.map(day => `
        <div class="p-3 border-r border-gray-200 text-center font-bold text-slate-500 uppercase text-[11px] tracking-wider flex items-center justify-center">
            ${day.name}
        </div>
    `).join('');
}

// Render linh động dựa trên số lượng ca trả về từ DB
function renderAllCells() {
    const gridContainer = document.getElementById('dsCaLamGrid');
    gridContainer.innerHTML = '';

    dsCaLam.forEach((ca, index) => {

        const rowHtml = `
            <div class="grid grid-cols-[110px_repeat(7,1fr)] flex-1">
                <div class="p-3 border-r border-gray-200 flex flex-col items-center justify-center gap-1.5 bg-blue-50/30">
                    <span class="font-bold text-slate-700 text-sm text-center">${ca.tenCa}</span>
                    <span class="text-xs font-medium text-slate-500">${ca.gioBatDau} - ${ca.gioKetThuc}</span>
                </div>

                ${days.map(day => `
                    <div id="cell-${day.id}-${ca.id}" class="p-2 border-r border-gray-200 relative group transition-colors">
                        </div>
                `).join('')}
            </div>
        `;
        gridContainer.insertAdjacentHTML('beforeend', rowHtml);
    });

    // Populate dữ liệu cho từng ô
    dsCaLam.forEach(ca => {
        days.forEach(day => {
            updateCellContent(day.id, ca.id);
        });
    });
}

function updateCellContent(dayId, shiftId) {
    const cell = document.getElementById(`cell-${dayId}-${shiftId}`);
    if (!cell) return;

    const selectedDocIds = schedule[dayId][shiftId];
    // Tìm object bác sĩ dựa trên ID
    const selectedDocs = selectedDocIds.map(id => doctors.find(d => d.id === id)).filter(Boolean);

    if (selectedDocs.length === 0) {
        cell.innerHTML = `
            <div onclick="openPopover(event, '${dayId}', ${shiftId})"
                 class="w-full h-full min-h-[120px] border-2 border-dashed border-gray-200 rounded-xl flex items-center justify-center cursor-pointer hover:border-primary hover:bg-blue-50 transition-all">
                <span class="text-primary font-semibold text-sm flex items-center gap-1.5 group-hover:scale-105 transition-transform">
                    <i data-lucide="plus-circle" class="w-4 h-4"></i> Thêm
                </span>
            </div>
        `;
    } else {
        let html = `<div class="flex flex-wrap gap-2 content-start h-full pb-8">`;

        selectedDocs.forEach(doc => {
            html += `
                <div class="flex items-center gap-2 bg-blue-50 text-primary pl-1 pr-2 py-1.5 rounded-lg border border-blue-200 shadow-sm w-full xl:w-auto">
                    <img src="${doc.avatar}" class="w-6 h-6 rounded-full border border-white object-cover" alt="avatar"/>
                    <span class="font-medium text-[13px] whitespace-nowrap truncate flex-1">${doc.hoTen}</span>
                    <button onclick="removeDoctor(event, '${dayId}', ${shiftId}, ${doc.id})"
                            class="p-0.5 rounded-md hover:bg-blue-200 text-blue-400 hover:text-red-500 transition-colors shrink-0">
                        <i data-lucide="x" class="w-3.5 h-3.5"></i>
                    </button>
                </div>
            `;
        });

        html += `</div>
            <button onclick="openPopover(event, '${dayId}', ${shiftId})"
                    class="absolute bottom-2 left-2 right-2 flex items-center justify-center h-8 rounded-lg border border-dashed border-primary bg-white text-primary hover:bg-blue-50 transition-colors text-sm font-medium gap-1 opacity-0 group-hover:opacity-100 shadow-sm">
                <i data-lucide="plus" class="w-4 h-4"></i> Thêm bác sĩ
            </button>
        `;
        cell.innerHTML = html;
    }

    lucide.createIcons({ root: cell });
}

// 5. POPOVER LOGIC
function openPopover(event, dayId, shiftId) {
    currentEditCell = { dayId, shiftId };
    tempSelectedDoctors = new Set(schedule[dayId][shiftId]);

    const popover = document.getElementById('doctorPopover');
    const backdrop = document.getElementById('popoverBackdrop');
    const cellRect = event.currentTarget.closest(`[id^="cell-"]`).getBoundingClientRect();

    let top = cellRect.top + window.scrollY;
    let left = cellRect.left + window.scrollX;

    if (left + 320 > window.innerWidth) {
        left = window.innerWidth - 340;
    }

    if (top + 450 > window.innerHeight) {
        top = top - 400 + cellRect.height;
    }

    popover.style.top = `${top}px`;
    popover.style.left = `${left}px`;

    document.getElementById('doctorSearch').value = '';
    renderPopoverList('');
    updateSelectedCount();

    popover.classList.remove('hidden');
    backdrop.classList.remove('hidden');

    setTimeout(() => document.getElementById('doctorSearch').focus(), 50);
}

function closePopover() {
    document.getElementById('doctorPopover').classList.add('hidden');
    document.getElementById('popoverBackdrop').classList.add('hidden');
    currentEditCell = null;
}

function renderPopoverList(searchTerm = '') {
    const listContainer = document.getElementById('doctorList');

    // Đã fix lỗi filter sử dụng đúng key trả về từ DB (hoTen, chuyenKhoa)
    let filteredDocs = doctors.filter(doc =>
        (doc.hoTen && doc.hoTen.toLowerCase().includes(searchTerm)) ||
        (doc.chuyenKhoa && doc.chuyenKhoa.toLowerCase().includes(searchTerm))
    );

    filteredDocs.sort((a, b) => {
        const aSelected = tempSelectedDoctors.has(a.id);
        const bSelected = tempSelectedDoctors.has(b.id);
        if (aSelected && !bSelected) return -1;
        if (!aSelected && bSelected) return 1;
        return 0;
    });

    if (filteredDocs.length === 0) {
        listContainer.innerHTML = `<div class="p-4 text-center text-sm text-gray-500">Không tìm thấy bác sĩ nào.</div>`;
        return;
    }

    listContainer.innerHTML = filteredDocs.map(doc => {
        const isChecked = tempSelectedDoctors.has(doc.id);
        return `
            <label class="flex items-center p-2.5 rounded-lg cursor-pointer transition-colors border border-transparent hover:bg-blue-50 hover:border-blue-100 ${isChecked ? 'bg-blue-50/50 border-blue-100' : ''}">
                <div class="relative flex items-center">
                    <input type="checkbox"
                           class="peer w-4 h-4 text-primary bg-gray-100 border-gray-300 rounded focus:ring-primary focus:ring-2 cursor-pointer transition-all"
                           value="${doc.id}"
                           ${isChecked ? 'checked' : ''}
                           onchange="toggleDoctor(${doc.id})">
                </div>
                <img src="${doc.avatar || '/static/img/default-avatar.png'}" class="w-9 h-9 rounded-full ml-3 mr-3 object-cover shadow-sm" alt="avatar">
                <div class="flex flex-col flex-1">
                    <span class="text-sm font-semibold text-slate-800">${doc.hoTen}</span>
                    <span class="text-xs text-slate-500 font-medium">${doc.chuyenKhoa}</span>
                </div>
            </label>
        `;
    }).join('');
}

function toggleDoctor(id) {
    if (tempSelectedDoctors.has(id)) {
        tempSelectedDoctors.delete(id);
    } else {
        tempSelectedDoctors.add(id);
    }
    updateSelectedCount();
    const searchTerm = document.getElementById('doctorSearch').value.toLowerCase();
    renderPopoverList(searchTerm);
}

function updateSelectedCount() {
    document.getElementById('selectedCount').innerText = tempSelectedDoctors.size;
}

function confirmSelection() {
    if (!currentEditCell) return;

    // Lưu mảng set vào state
    schedule[currentEditCell.dayId][currentEditCell.shiftId] = Array.from(tempSelectedDoctors);

    // Cập nhật lại UI của ô
    updateCellContent(currentEditCell.dayId, currentEditCell.shiftId);

    closePopover();
}

function removeDoctor(event, dayId, shiftId, doctorId) {
    event.stopPropagation();
    schedule[dayId][shiftId] = schedule[dayId][shiftId].filter(id => id !== doctorId);
    updateCellContent(dayId, shiftId);
}


//API
async function saveSchedule() {
    const startDateStr = document.getElementById('startDate').value;
    const endDateStr = document.getElementById('endDate').value;

    if (!startDateStr || !endDateStr) {
        alert("Vui lòng chọn Từ ngày và Đến ngày!");
        return;
    }

    if (new Date(startDateStr) > new Date(endDateStr)) {
        alert("Ngày bắt đầu không thể lớn hơn ngày kết thúc!");
        return;
    }

    const lichTuan = {};
    let hasData = false;

    for (const dayId in schedule) {
        lichTuan[dayId] = {};

        for (const shiftId in schedule[dayId]) {
            const doctorIds = schedule[dayId][shiftId];

            if (doctorIds.length > 0) {
                lichTuan[dayId][shiftId] = doctorIds;
                hasData = true;
            }
        }

        // Nếu ngày đó không có ca nào được xếp, xóa luôn key ngày đó cho JSON sạch sẽ
        if (Object.keys(lichTuan[dayId]).length === 0) {
            delete lichTuan[dayId];
        }
    }

    if (!hasData) {
        alert("Lịch làm việc đang trống! Vui lòng phân công ít nhất 1 bác sĩ.");
        return;
    }

    // 3. Khối dữ liệu gửi đi (Payload)
    const payload = {
        ngayBatDau: startDateStr, // VD: "2026-04-13"
        ngayKetThuc: endDateStr,  // VD: "2026-04-19"
        lichTuan: lichTuan        // VD: { "T2": { "1": [5, 8], "2": [12] }, "T3": ... }
    };

    console.log("Dữ liệu tinh gọn gửi đi:", JSON.stringify(payload, null, 2));

    // 4. Gửi API
    try {
        const btn = document.querySelector('button[onclick="saveSchedule()"]');
        btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Đang xử lý...`;
        btn.disabled = true;

        const response = await fetch('/api/admin/luu-lich-lam-viec', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            alert("Đã lưu lịch làm việc thành công!");
            window.location.reload();
        } else {
            alert("Có lỗi từ máy chủ: " + result.message);
        }
    } catch (error) {
        console.error("Lỗi:", error);
        alert("Không thể kết nối đến máy chủ!");
    } finally {
        const btn = document.querySelector('button[onclick="saveSchedule()"]');
        if(btn) {
            btn.innerHTML = `<i data-lucide="save" class="w-4 h-4"></i> Lưu lịch làm việc`;
            lucide.createIcons({ root: btn });
            btn.disabled = false;
        }
    }
}