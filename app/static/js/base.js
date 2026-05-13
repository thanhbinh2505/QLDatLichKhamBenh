document.addEventListener("DOMContentLoaded", function() {
    lucide.createIcons();
});

// =============================================
// TOAST NOTIFICATION SYSTEM
// Dùng: showToast('Thông báo', 'success' | 'error' | 'warning' | 'info')
// =============================================
(function () {
    const TOAST_TYPES = {
        success: {
            bg: 'bg-emerald-50',
            border: 'border-emerald-400',
            icon: 'check-circle',
            iconColor: 'text-emerald-500',
            titleColor: 'text-emerald-800',
            msgColor: 'text-emerald-700',
            bar: 'bg-emerald-400',
        },
        error: {
            bg: 'bg-red-50',
            border: 'border-red-400',
            icon: 'x-circle',
            iconColor: 'text-red-500',
            titleColor: 'text-red-800',
            msgColor: 'text-red-700',
            bar: 'bg-red-400',
        },
        warning: {
            bg: 'bg-amber-50',
            border: 'border-amber-400',
            icon: 'alert-triangle',
            iconColor: 'text-amber-500',
            titleColor: 'text-amber-800',
            msgColor: 'text-amber-700',
            bar: 'bg-amber-400',
        },
        info: {
            bg: 'bg-blue-50',
            border: 'border-blue-400',
            icon: 'info',
            iconColor: 'text-blue-500',
            titleColor: 'text-blue-800',
            msgColor: 'text-blue-700',
            bar: 'bg-blue-400',
        },
    };

    const TITLES = {
        success: 'Thành công',
        error: 'Lỗi',
        warning: 'Cảnh báo',
        info: 'Thông tin',
    };

    const DURATION = 6000;

    function getContainer() {
        let c = document.getElementById('toast-container');
        if (!c) {
            c = document.createElement('div');
            c.id = 'toast-container';
            c.className = 'fixed top-5 right-5 z-[9999] flex flex-col gap-3 w-80 pointer-events-none';
            document.body.appendChild(c);
        }
        return c;
    }

    window.showToast = function (message, type = 'info') {
        const cfg = TOAST_TYPES[type] || TOAST_TYPES.info;
        const container = getContainer();

        const toast = document.createElement('div');
        toast.className = [
            'relative overflow-hidden flex items-start gap-3 p-4 rounded-xl border shadow-lg',
            'pointer-events-auto cursor-pointer',
            'translate-x-full opacity-0 transition-all duration-300 ease-out',
            cfg.bg, cfg.border,
        ].join(' ');

        toast.innerHTML = `
            <i data-lucide="${cfg.icon}" class="w-5 h-5 mt-0.5 shrink-0 ${cfg.iconColor}"></i>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold ${cfg.titleColor}">${TITLES[type]}</p>
                <p class="text-sm ${cfg.msgColor} break-words">${message}</p>
            </div>
            <button class="shrink-0 ${cfg.iconColor} hover:opacity-70 transition-opacity" onclick="this.closest('[data-toast]').remove()">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
            <div class="absolute bottom-0 left-0 h-1 ${cfg.bar} toast-bar" style="width:100%; transition: width ${DURATION}ms linear;"></div>
        `;
        toast.dataset.toast = '1';

        container.appendChild(toast);
        lucide.createIcons({ nodes: [toast] });

        // Slide in
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                toast.classList.remove('translate-x-full', 'opacity-0');
            });
        });

        // Animate progress bar
        setTimeout(() => {
            const bar = toast.querySelector('.toast-bar');
            if (bar) bar.style.width = '0%';
        }, 50);

        // Click to dismiss
        toast.addEventListener('click', () => dismiss(toast));

        // Auto dismiss
        const timer = setTimeout(() => dismiss(toast), DURATION);
        toast._toastTimer = timer;

        function dismiss(el) {
            clearTimeout(el._toastTimer);
            el.classList.add('opacity-0', 'translate-x-full');
            setTimeout(() => el.remove(), 300);
        }
    };
})();

// =============================================

window.scrollDoctors = function(direction) {
    const container = document.getElementById('doctor-container');
    if (!container) return;
    const firstCard = container.querySelector('div');
    if (!firstCard) return;
    const scrollAmount = firstCard.offsetWidth + 24;
    if (direction === 'left') {
        container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
};
