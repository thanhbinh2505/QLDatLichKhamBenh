
lucide.createIcons();
fetchLichKham();

function showStatusModal(message, isSuccess = true) {
    const modal = document.getElementById('statusModal');
    const header = document.getElementById('statusHeader');
    const title = document.getElementById('statusTitle');
    const msgElem = document.getElementById('statusMessage');
    const icon = document.getElementById('statusIcon');

    if (isSuccess) {
        header.className = "p-8 flex flex-col items-center text-white bg-green-500";
        title.innerText = "Thành công!";
        icon.setAttribute('data-lucide', 'check-circle');
    } else {
        header.className = "p-8 flex flex-col items-center text-white bg-red-500";
        title.innerText = "Thất bại!";
        icon.setAttribute('data-lucide', 'alert-circle');
    }

    msgElem.innerText = message;
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function closeStatusModal() {
    const modal = document.getElementById('statusModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

let currentCancelId = null;

function handleHuyClick(id, diffInHours) {
    if (diffInHours < 1) {
        showStatusModal("Không thể hủy lịch khám vì thời gian còn lại dưới 1 giờ!", false);
        return;
    }
    currentCancelId = id;
    openCancelModal();
}

function openCancelModal() {
    const modal = document.getElementById('cancelModal');
    modal.classList.remove('hidden');
}

function closeCancelModal() {
    const modal = document.getElementById('cancelModal');
    modal.classList.add('hidden');
}
document.getElementById('btnConfirmCancel').addEventListener('click', async function() {
    if (!currentCancelId) return;

    this.innerText = 'Đang xử lý...';
    this.disabled = true;

    try {
        const response = await fetch(`/api/huy-lich/${currentCancelId}`, { method: 'POST' });
        const result = await response.json();
        closeCancelModal();
        showStatusModal(result.message, result.success);
        if (result.success) {
            fetchLichKham();
        }
    } catch (error) {
        closeCancelModal();
        showStatusModal("Lỗi kết nối máy chủ, vui lòng thử lại!", false);
    } finally {
        this.innerText = 'Xác nhận hủy';
        this.disabled = false;
    }
});
function renderPhieuKham(phieu) {
    const now = new Date();
    const thoiGianKham = new Date(phieu.ngay_gio_kham);
    const diffInHours = (thoiGianKham - now) / (1000 * 60 * 60);

    const isLocked = phieu.status === 'Completed' || phieu.status === 'Cancelled';

    let statusClass = 'bg-blue-100 text-blue-700';
    if (phieu.status === 'Completed') statusClass = 'bg-green-100 text-green-700';
    if (phieu.status === 'Cancelled') statusClass = 'bg-red-100 text-red-700';

    const btnClass = isLocked
        ? "text-slate-400 cursor-not-allowed border-slate-200"
        : "text-red-500 hover:bg-red-50 border-red-100 hover:border-red-200";

    return `
        <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition-all">
            <div class="space-y-2">
                <div class="flex items-center gap-3">
                    <h4 class="font-bold text-slate-800 text-lg">BS. ${phieu.ten_BS || 'Chưa xác định'}</h4>
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${statusClass}">
                        ${phieu.status}
                    </span>
                </div>
                <div class="text-slate-600 text-sm space-y-1">
                    <p class="flex items-center gap-2"><i data-lucide="calendar" class="w-4 h-4 text-blue-500"></i> Ngày: ${phieu.ngay_kham_str}</p>
                    <p class="flex items-center gap-2"><i data-lucide="clock" class="w-4 h-4 text-blue-500"></i> Giờ: ${phieu.gio_kham_str}</p>
                </div>
            </div>

            <div class="w-full sm:w-auto flex justify-end">
                <button
                    onclick="handleHuyClick(${phieu.id}, ${diffInHours})"
                    ${isLocked ? 'disabled' : ''}
                    class="flex items-center gap-1 px-4 py-2 border rounded-xl font-bold transition-all ${btnClass}">
                    <i data-lucide="${isLocked ? 'ban' : 'x-circle'}" class="w-4 h-4"></i>
                    ${phieu.status === 'Cancelled' ? 'Đã hủy' : (phieu.status === 'Completed' ? 'Đã xong' : 'Hủy lịch')}
                </button>
            </div>
        </div>
    `;
}

async function fetchLichKham() {
    const container = document.getElementById('danhSachLichKham');
    try {
        const response = await fetch('/api/ho-so/lich-kham');
        const data = await response.json();

        if (data.length === 0) {
            container.innerHTML = `<p class="text-center text-slate-500 py-10">Chưa có lịch khám nào.</p>`;
            return;
        }

        container.innerHTML = data.map(p => renderPhieuKham(p)).join('');
        lucide.createIcons();
    } catch (e) {
        container.innerHTML = `<p class="text-center text-red-500 py-10">Lỗi tải dữ liệu.</p>`;
    }
}