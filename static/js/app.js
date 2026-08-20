import { state } from './state.js';
import { showAlert, clearAlert, populateTimeSelect, renderTables, updateNavigationClock } from './ui.js';
import { loadAppFromBackend, evaluateCalendarSchedule } from './api.js';

function getLocalISOString(dateStr, timeStr) {
    return `${dateStr}T${timeStr}:00`;
}

window.handleDateChange = function() {
    state.currentSelectedDate = document.getElementById('cust-date').value;
    populateTimeSelect();
    evaluateCalendarSchedule();
};

window.handleTimeSelectChange = function(val) {
    state.currentSelectedTime = val;
    evaluateCalendarSchedule();
};

window.selectTable = function(id) {
    const table = state.backendTables.find(t => t.id === id);
    if (!table) return;

    if (table.status === 'out_of_service') {
        showAlert("warning", `Table ${table.table_number} is out of service.`);
        return;
    }
    if (table.status === 'reserved') {
        showAlert("info", `Table ${table.table_number} is already booked at this time by ${table.assignedGuest || 'another guest'}.`);
        return;
    }

    if (state.selectedTable && state.selectedTable.id === table.id) {
        state.selectedTable = null;
        renderTables();
        const card = document.getElementById("table-info-card");
        if (card) {
            card.innerHTML = `<p class="text-sm font-semibold text-slate-500 text-center py-4">No Table Selected</p>`;
        }
        return;
    }

    state.selectedTable = table;
    renderTables();

    const card = document.getElementById("table-info-card");
    if (card) {
        card.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h4 class="text-sm font-bold text-slate-900">Table Selected: ${table.table_number}</h4>
                    <p class="text-xs text-slate-500">Zone: <span class="capitalize font-semibold">${table.zone.replace('-', ' ')}</span></p>
                </div>
                <div class="bg-amber-100 border border-amber-200 px-3 py-1.5 rounded-xl text-center">
                    <span class="block text-[10px] font-bold text-amber-800 uppercase">Seating</span>
                    <span class="text-sm font-black text-amber-900">${table.capacity} Pax</span>
                </div>
            </div>
        `;
    }

    const form = document.getElementById("booking-form");
    if (form) form.classList.remove("opacity-50", "pointer-events-none");

    const tableIdInput = document.getElementById("selected-table-id");
    if (tableIdInput) tableIdInput.value = table.id;

    const partyInput = document.getElementById("cust-party");
    if (partyInput) {
        partyInput.max = table.capacity;
        partyInput.placeholder = `Max ${table.capacity}`;
    }

    clearAlert();
};

window.filterTables = function(type) {
    state.currentFilter = type;
    const capSelect = document.getElementById("capacity-filter");
    if ((type === 'all' || type === 'available') && capSelect) capSelect.value = "all";

    const btnAll = document.getElementById("filter-all");
    const btnAvailable = document.getElementById("filter-available");

    if (btnAll) btnAll.className = `px-3.5 py-1.5 rounded-lg text-xs font-medium ${type === 'all' ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"} transition-all h-[32px] flex items-center`;
    if (btnAvailable) btnAvailable.className = `px-3.5 py-1.5 rounded-lg text-xs font-medium ${type === 'available' ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"} transition-all h-[32px] flex items-center`;

    renderTables();
};

window.handleCapacityFilterChange = function(value) {
    window.filterTables(value === 'all' ? 'all' : 'cap_' + value);
};

window.handleFormSubmission = async function(event) {
    event.preventDefault();

    const activeDate = state.currentSelectedDate || document.getElementById("cust-date")?.value;
    const activeTime = state.currentSelectedTime || document.getElementById("time-select")?.value;

    const missingFields = [];
    if (!activeDate) missingFields.push("Booking Date");
    if (!activeTime) missingFields.push("Time Slot");
    if (!state.selectedTable) missingFields.push("Table Selection");

    const name = document.getElementById("cust-name")?.value.trim() || "";
    const email = document.getElementById("cust-email")?.value.trim() || "";
    const phone = document.getElementById("cust-phone")?.value.trim() || "";
    const partySize = parseInt(document.getElementById("cust-party")?.value, 10) || 0;

    if (!name) missingFields.push("Customer Name");
    if (!email) missingFields.push("Email Address");
    if (!phone) missingFields.push("Phone Number");
    if (isNaN(partySize) || partySize <= 0) missingFields.push("Valid Party Size");

    if (missingFields.length > 0) {
        showAlert("warning", `Please complete: <strong>${missingFields.join(", ")}</strong>.`);
        return;
    }

    if (partySize > state.selectedTable.capacity) {
        showAlert("danger", `Over-capacity! Table ${state.selectedTable.table_number} holds up to ${state.selectedTable.capacity} guests.`);
        return;
    }

    const payload = {
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
        party_size: partySize,
        reservation_time: getLocalISOString(activeDate, activeTime),
        table_id: state.selectedTable.id
    };

    try {
        const response = await fetch('/api/reservations/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const responseText = await response.text();
        let responseData = {};
        try { responseData = JSON.parse(responseText); } catch (e) {}

        if (!response.ok) {
            throw new Error(responseData.error || responseData.detail || responseText || `Server error (${response.status})`);
        }

        state.selectedTable = null;
        state.currentSelectedTime = "";

        const form = document.getElementById("booking-form");
        if (form) {
            form.reset();
            form.classList.add("opacity-50", "pointer-events-none");
        }

        const infoCard = document.getElementById("table-info-card");
        if (infoCard) {
            infoCard.innerHTML = `<p class="text-sm font-semibold text-slate-500 text-center py-4">No Table Selected</p>`;
        }

        showAlert("success", "Reservation successfully completed!");
        populateTimeSelect();
        await loadAppFromBackend();

    } catch (err) {
        showAlert("danger", err.message);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('cust-date');
    if (dateInput && !dateInput.value) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${year}-${month}-${day}`;
        dateInput.min = `${year}-${month}-${day}`;
    }

    updateNavigationClock();
    setInterval(updateNavigationClock, 60000);

    window.handleDateChange();
    loadAppFromBackend();
});