import { state } from './state.js';

export function showAlert(type, message) {
    const banner = document.getElementById("alert-banner");
    const icon = document.getElementById("alert-icon");
    const messageDiv = document.getElementById("alert-message");

    if (!banner || !icon || !messageDiv) return;

    banner.className = "mb-4 p-3 rounded-xl text-xs font-semibold flex items-start gap-2.5 transition-all";
    
    if (type === "success") {
        banner.classList.add("bg-emerald-50", "text-emerald-800", "border", "border-emerald-200");
        icon.className = "fa-solid fa-circle-check text-emerald-600";
    } else if (type === "warning" || type === "info") {
        banner.classList.add("bg-amber-50", "text-amber-800", "border", "border-amber-200");
        icon.className = "fa-solid fa-triangle-exclamation text-amber-600";
    } else if (type === "danger") {
        banner.classList.add("bg-rose-50", "text-rose-800", "border", "border-rose-200");
        icon.className = "fa-solid fa-circle-exclamation text-rose-600";
    }

    messageDiv.innerHTML = message;
    banner.classList.remove("hidden");
}

export function clearAlert() {
    const banner = document.getElementById("alert-banner");
    if (banner) banner.classList.add("hidden");
}

export const updateNavigationClock = () => {
    const timeDisplayNode = document.getElementById("current-time-display");
    if (timeDisplayNode) {
        timeDisplayNode.innerText = new Date().toLocaleString('en-US', { 
            weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
        });
    }
};

export function populateTimeSelect() {
    const timeSelect = document.getElementById("time-select");
    if (!timeSelect) return;

    const previousValue = state.currentSelectedTime;
    timeSelect.innerHTML = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.text = "Click to pick a time slot";
    placeholder.disabled = true;
    placeholder.selected = !previousValue;
    timeSelect.appendChild(placeholder);
    
    const now = new Date();
    const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    let hasSelectedValidTime = false;

    for (let hour = 10; hour <= 23; hour++) {
        const timeStr = `${String(hour).padStart(2, '0')}:00`;
        const isPastSlot = (state.currentSelectedDate === todayStr && (hour < currentHour || (hour === currentHour && currentMinute > 0)));

        const option = document.createElement("option");
        option.value = timeStr;
        option.text = timeStr;
        
        if (isPastSlot) {
            option.disabled = true;
            option.text += " (Past)";
            option.className = "text-slate-300 font-medium";
        } else {
            option.className = "text-slate-800 font-semibold";
            if (previousValue === timeStr) {
                option.selected = true;
                hasSelectedValidTime = true;
            }
        }
        timeSelect.appendChild(option);
    }

    if (!hasSelectedValidTime && previousValue !== "") {
        state.currentSelectedTime = "";
        timeSelect.value = "";
    }
}

export function renderTables() {
    const zones = ["private-a", "main-hall", "private-b", "terrace"];
    zones.forEach(zoneId => {
        const container = document.getElementById(`${zoneId}-tables`);
        if (container) container.innerHTML = "";
    });

    state.backendTables.forEach(table => {
        if (state.currentFilter === 'available' && table.status !== 'available') return;
        
        if (state.currentFilter.startsWith('cap_')) {
            const reqCap = state.currentFilter.split('_')[1];
            if (reqCap === '10') {
                if (table.capacity < 10) return;
            } else {
                const capNum = parseInt(reqCap, 10);
                if (table.capacity !== capNum) return;
            }
        }

        const zoneContainer = document.getElementById(`${table.zone}-tables`);
        if (!zoneContainer) return;

        const tableNode = document.createElement("div");
        tableNode.className = "relative flex flex-col items-center justify-center cursor-pointer transition-all duration-200 select-none group";
        tableNode.onclick = () => window.selectTable(table.id);

        let chairsHTML = "";
        const radius = 28;
        for (let i = 0; i < table.capacity; i++) {
            const angle = (i * 2 * Math.PI) / table.capacity;
            const left = Math.round(50 + Math.sin(angle) * radius);
            const top = Math.round(50 - Math.cos(angle) * radius);
            chairsHTML += `<div class="absolute w-2.5 h-2.5 rounded-full bg-slate-600 border border-slate-500/50 shadow-sm" style="top: ${top}%; left: ${left}%; transform: translate(-50%, -50%);"></div>`;
        }

        let colorClasses = "bg-slate-700 hover:bg-slate-600 border-slate-600 text-slate-100";
        if (table.status === 'reserved') {
            colorClasses = "bg-rose-500/20 border-rose-500 text-rose-300 cursor-not-allowed";
        } else if (table.status === 'out_of_service') {
            colorClasses = "bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed opacity-40";
        }

        if (state.selectedTable && state.selectedTable.id === table.id) {
            colorClasses = "bg-amber-500 border-amber-400 text-slate-950 scale-105 shadow-lg shadow-amber-500/20 ring-4 ring-amber-500/20";
        }

        tableNode.innerHTML = `
            <div class="relative w-16 h-16 flex items-center justify-center">
                ${chairsHTML}
                <div class="w-10 h-10 rounded-full flex flex-col items-center justify-center border-2 shadow-md transition-transform ${colorClasses}">
                    <span class="text-xs font-extrabold leading-none">${table.table_number}</span>
                    <span class="text-[8px] font-medium opacity-80 mt-0.5"><i class="fa-solid fa-users"></i>${table.capacity}</span>
                </div>
            </div>
        `;

        zoneContainer.appendChild(tableNode);
    });
}

export function updateReservationsList() {
    const listContainer = document.getElementById("active-reservations-list");
    const countBadge = document.getElementById("total-bookings-count");
    if (countBadge) {
        countBadge.innerText = `${state.backendReservations.length} Booked`;
    }

    if (!listContainer) return;

    if (state.backendReservations.length === 0) {
        listContainer.innerHTML = `<p class="text-xs text-slate-400 text-center py-6 font-medium">No reservations completed yet.</p>`;
        return;
    }

    listContainer.innerHTML = "";
    [...state.backendReservations].reverse().forEach(res => {
        const dateObj = new Date(res.reservation_time);
        const formattedDate = dateObj.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        listContainer.innerHTML += `
            <div class="bg-slate-50 border border-slate-100 p-2.5 rounded-xl text-xs flex items-center justify-between gap-2.5 hover:border-slate-200 transition-all">
                <div class="min-w-0">
                    <h5 class="font-bold text-slate-900 truncate">${res.customer_name}</h5>
                    <p class="text-[10px] text-slate-500 font-medium">${formattedDate} • ${res.party_size} Guests</p>
                </div>
                <span class="bg-slate-200 text-slate-800 font-black px-2 py-1 rounded-md text-[10px] shrink-0">
                    Table ${res.table ? res.table.table_number : 'N/A'}
                </span>
            </div>
        `;
    });
}