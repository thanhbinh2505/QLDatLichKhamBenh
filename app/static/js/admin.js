let doctorsList = [];
let scheduleData = {};
const daysOfWeek = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

let thu2HienTai
let chuNhatHienTai

document.addEventListener('DOMContentLoaded', async () => {

    thu2HienTai = new Date(thu2)
    chuNhatHienTai = new Date(chuNhat)

    try {
        const [doctorsRes, scheduleRes] = await Promise.all([
            fetch('/api/doctors'),
            fetch(`/api/admin/lay-lich-tuan?ngayBatDau=${thu2}&ngayKetThuc=${chuNhat}`)
        ]);

        if (!doctorsRes.ok || !scheduleRes.ok) {
            throw new Error("Không thể tải dữ liệu từ máy chủ");
        }

        doctorsList = await doctorsRes.json();
        const scheduleJson = await scheduleRes.json();
        scheduleData = scheduleJson.data || {};

        renderScheduleThead();
        renderScheduleTable();

    } catch (error) {
        console.error("Lỗi khởi tạo:", error);
        alert("Có lỗi xảy ra khi tải dữ liệu lịch làm việc!");
    }
});

async function changeWeek(action) {
    if (action === 'next') {
        thu2HienTai.setDate(thu2HienTai.getDate() + 7);
    }
    else if (action === 'prev') {
        thu2HienTai.setDate(thu2HienTai.getDate() - 7);
    }
    else if (action === 'current') {
        const today = new Date();
        const day = today.getDay() || 7;

        thu2HienTai = new Date(today);
        thu2HienTai.setDate(today.getDate() - (day - 1));
        thu2HienTai.setHours(0, 0, 0, 0);
    }

    const chuNhatHienTai = new Date(thu2HienTai);
    chuNhatHienTai.setDate(thu2HienTai.getDate() + 6);

    const formatDate = (d) => {
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    };

    const ngayBatDau = formatDate(thu2HienTai);
    const ngayKetThuc = formatDate(chuNhatHienTai);

    const weekSpan = document.getElementById('weekSpan')
    weekSpan.textContent = `Tuần: ${ngayBatDau} - ${ngayKetThuc}`;

    try {
        const response = await fetch(`/api/admin/lay-lich-tuan?ngayBatDau=${ngayBatDau}&ngayKetThuc=${ngayKetThuc}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || "Không thể tải dữ liệu từ máy chủ");
        }

        const scheduleJson = await response.json();
        scheduleData = scheduleJson.data || {};

        renderScheduleThead();
        renderScheduleTable();

    } catch (error) {
        console.error("Lỗi chuyển tuần:", error);
        alert("Lỗi: " + error.message);
    }
}

const dayLabels = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];
function renderScheduleThead(){

    const thead = document.getElementById('scheduleThead');
    if (!thead) return;

    thead.innerHTML = '';
    let html = `<tr>
        <th class="w-32 p-4 font-semibold text-center border-r border-gray-200 bg-white">
            <span class="text-slate-500">Ca trực</span>
        </th>`;

    for (let i = 0; i < 7; i++) {
        let currentDate = new Date(thu2HienTai)
        currentDate.setDate(currentDate.getDate() + i);

        let dateStr = `${String(currentDate.getDate()).padStart(2, '0')}/${String(currentDate.getMonth() + 1).padStart(2, '0')}`;

        if (i === 6) {
            html += `
                <th class="p-4 font-semibold text-center w-[12.5%]">
                    <div class="flex flex-col items-center gap-0.5">
                        <span>${dayLabels[i]}</span>
                        <span class="text-xs font-normal text-slate-500">${dateStr}</span>
                    </div>
                </th>
            `;
        }
        else{
            html += `
                <th class="p-4 font-semibold text-center border-r border-gray-200 w-[12.5%]">
                    <div class="flex flex-col items-center gap-0.5">
                        <span>${dayLabels[i]}</span>
                        <span class="text-xs font-normal text-slate-500">${dateStr}</span>
                    </div>
                </th>
            `;
        }
    }
    html += `</tr>`;
    thead.innerHTML = html;
}

function renderScheduleTable() {
    const tbody = document.getElementById('scheduleBody');
    tbody.innerHTML = '';

    dsCaLam.forEach(ca => {
        let rowHtml = `<tr>`;

        rowHtml += `
            <td class="p-4 border-r border-gray-200 bg-slate-50/50 text-center align-middle">
                <div class="flex flex-col items-center gap-1.5">
                    <span class="font-semibold text-slate-700">${ca.tenCa}</span>
                    <span class="text-[11px] text-slate-500 whitespace-nowrap">${ca.gioBatDau} - ${ca.gioKetThuc}</span>
                </div>
            </td>
        `;

        daysOfWeek.forEach(thu => {
            const bacSiIds = (scheduleData[thu] && scheduleData[thu][ca.id]) ? scheduleData[thu][ca.id] : [];

            if (bacSiIds.length === 0) {
                rowHtml += `
                    <td class="p-2 border-r border-gray-200 align-top h-[220px] bg-slate-50/30 schedule-cell group transition-all">
                        <div class="flex flex-col items-center justify-center h-full gap-3 opacity-70 group-hover:opacity-100 transition-opacity">
                            <span class="text-xs italic text-slate-400">Chưa có lịch</span>
                            <button class="w-10/12 py-2 border border-dashed border-gray-300 rounded-lg text-xs font-medium text-slate-500 transition-all flex items-center justify-center gap-1.5 hover:bg-white hover:text-primary hover:border-primary/50 shadow-sm">
                                <i data-lucide="plus" class="w-3.5 h-3.5"></i> Thêm
                            </button>
                        </div>
                    </td>
                `;
            } else {
                let cellContent = `<div class="flex flex-col gap-2 h-full overflow-y-auto scrollbar-hide pr-1 pb-1">`;

                bacSiIds.forEach(bsId => {
                    // Tìm object thông tin chi tiết của bác sĩ này
                    const doctor = doctorsList.find(d => d.id === bsId);

                    if (doctor) {
                        const avatarUrl = doctor.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(doctor.hoTen)}&background=dbeafe&color=1d4ed8`;
                        const chuyenKhoa = doctor.chuyenKhoa || 'Đa khoa';

                        cellContent += `
                            <div class="group flex items-center gap-2.5 p-2 rounded-lg border border-gray-100 bg-white hover:bg-blue-50/50 hover:border-blue-200 transition-all cursor-pointer shadow-sm relative">
                                <div class="relative shrink-0">
                                    <img src="${avatarUrl}" class="w-8 h-8 rounded-full object-cover border border-gray-100" alt="avatar">
                                    <span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-white rounded-full"></span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p class="text-xs font-semibold text-slate-700 truncate group-hover:text-primary">
                                        BS. ${doctor.hoTen}
                                    </p>
                                    <p class="text-[10px] text-slate-500 truncate">${chuyenKhoa}</p>
                                </div>
                            </div>
                        `;
                    }
                });

                cellContent += `
                    <button class="mt-auto w-full py-1.5 border border-dashed border-gray-200 rounded-lg text-[11px] font-medium text-slate-500 transition-colors flex items-center justify-center gap-1 hover:bg-slate-50 hover:text-primary">
                        <i data-lucide="plus" class="w-3 h-3"></i>
                    </button>
                </div>`;

                rowHtml += `<td class="p-2 border-r border-gray-200 align-top h-[220px] bg-white schedule-cell">${cellContent}</td>`;
            }
        });

        rowHtml += `</tr>`;

        tbody.insertAdjacentHTML('beforeend', rowHtml);
    });

    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}