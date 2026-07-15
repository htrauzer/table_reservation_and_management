// Store tables data fetched from the database
let backendTables = [];
// Store reservations data fetched from the database
let backendReservations = [];
// Track the user's currently selected table node
let selectedTable = null;
// Track the active UI filter status ('all', 'available', 'large')
let currentFilter = 'all';

// Constant buffer window configuration matching FastAPI's conflict rules (2 hours)
const RESERVATION_BUFFER_HOURS = 2;

// Update real-time display in the navigation bar
const updateNavigationClock = () => {
    const timeDisplayNode = document.getElementById("current-time-display");
    if (timeDisplayNode) {
        timeDisplayNode.innerText = new Date().toLocaleString('en-US', { 
            weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
        });
    }
};

// Configure boundary limits for the date-time selection input (prevent past bookings)
const configureDateTimeInputLimits = () => {
    const dtInput = document.getElementById("cust-time");
    if (dtInput) {
        const now = new Date();
        // Convert to local ISO string standard format required by datetime-local input fields
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        dtInput.min = now.toISOString().slice(0, 16);
    }
};


// Scans active calendar values to evaluate real-time reservation scheduling overlaps
function evaluateCalendarSchedule() {
    const dtInput = document.getElementById("cust-time");
    if (!dtInput) return;

    const selectedTimeVal = dtInput.value;
    
    // If no specific booking date/time is selected yet, fall back to default table statuses
    if (!selectedTimeVal) {
        backendTables.forEach(table => {
            table.status = table.is_active ? 'available' : 'out_of_service';
        });
        renderTables();
        return;
    }

    const targetTime = new Date(selectedTimeVal);

    backendTables.forEach(table => {
        if (!table.is_active) {
            table.status = 'out_of_service';
            return;
        }

        // Check if any booking reservation conflicts exist within the scheduling window
        const overlappingConflict = backendReservations.find(res => {
            if (res.table.id !== table.id) return false;
            
            const existingResTime = new Date(res.reservation_time);
            const diffMs = Math.abs(targetTime - existingResTime);
            const diffHours = diffMs / (1000 * 60 * 60);
            return diffHours < RESERVATION_BUFFER_HOURS;
        });

        if (overlappingConflict) {
            table.status = 'reserved';
            table.assignedGuest = overlappingConflict.customer_name;
        } else {
            table.status = 'available';
        }
    });

    // Deselect selected table if it becomes booked at the newly chosen date-time
    if (selectedTable) {
        const refreshedState = backendTables.find(t => t.id === selectedTable.id);
        if (refreshedState && refreshedState.status !== 'available') {
            selectedTable = null;
            document.getElementById("booking-form").reset();
            document.getElementById("booking-form").classList.add("opacity-50", "pointer-events-none");
            document.getElementById("table-info-card").innerHTML = `<p class="text-sm font-semibold text-slate-500 text-center py-4">No Table Selected</p>`;
            dtInput.value = selectedTimeVal; // Retain current time choice
        }
    }

    renderTables();
    updateReservationsList();
}


// Builds and appends responsive table map models into specific floor plan zones
function renderTables() {
    const zones = ["private-a", "main-hall", "private-b", "terrace"];
    zones.forEach(zoneId => {
        const container = document.getElementById(`${zoneId}-tables`);
        if (container) container.innerHTML = "";
    });

    backendTables.forEach(table => {
        // Apply active UI filtration parameters
        if (currentFilter === 'available' && table.status !== 'available') return;
        if (currentFilter === 'large' && table.capacity < 4) return;

        const zoneContainer = document.getElementById(`${table.zone}-tables`);
        if (!zoneContainer) return;

        const tableNode = document.createElement("div");
        tableNode.className = "relative flex flex-col items-center justify-center cursor-pointer transition-all duration-200 select-none group";
        tableNode.setAttribute("onclick", `selectTable(${table.id})`);

        // Generate coordinates dynamically to draw border chairs matching table capacity
        let chairsHTML = "";
        const radius = 28;
        for (let i = 0; i < table.capacity; i++) {
            const angle = (i * 2 * Math.PI) / table.capacity;
            const left = Math.round(50 + Math.sin(angle) * radius);
            const top = Math.round(50 - Math.cos(angle) * radius);
            chairsHTML += `<div class="absolute w-2.5 h-2.5 rounded-full bg-slate-600 border border-slate-500/50 shadow-sm" style="top: ${top}%; left: ${left}%; transform: translate(-50%, -50%);"></div>`;
        }

        // Apply visual dynamic feedback classes depending on table status
        let colorClasses = "bg-slate-700 hover:bg-slate-600 border-slate-600 text-slate-100";
        if (table.status === 'reserved') {
            colorClasses = "bg-rose-500/20 border-rose-500 text-rose-300 cursor-not-allowed";
        } else if (table.status === 'out_of_service') {
            colorClasses = "bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed opacity-40";
        }

        if (selectedTable && selectedTable.id === table.id) {
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

// Triggers validation checks and highlights clicked floor plan tables
function selectTable(id) {
    const dtInput = document.getElementById("cust-time");
    if (!dtInput || !dtInput.value) {
        showAlert("warning", "Please select your booking date & time first before choosing a table.");
        return;
    }

    const table = backendTables.find(t => t.id === id);
    if (!table) return;

    if (table.status === 'out_of_service') {
        showAlert("warning", `Table ${table.table_number} is out of service.`);
        return;
    }
    if (table.status === 'reserved') {
        showAlert("info", `Table ${table.table_number} is already booked at this time by ${table.assignedGuest || 'another guest'}.`);
        return;
    }

    selectedTable = table;
    renderTables();

    // Populate metadata inside the dynamic Reservation detail card
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

    // Activate the registration form
    document.getElementById("selected-table-id").value = table.id;
    const partyInput = document.getElementById("cust-party");
    if (partyInput) {
        partyInput.max = table.capacity;
        partyInput.placeholder = `Max ${table.capacity}`;
    }
    
    const form = document.getElementById("booking-form");
    if (form) {
        form.classList.remove("opacity-50", "pointer-events-none");
    }
    clearAlert();
}

// Validates client inputs and submits booking parameters to FastAPI POST router
async function handleFormSubmission(event) {
    event.preventDefault();
    if (!selectedTable) return;

    const name = document.getElementById("cust-name").value.trim();
    const email = document.getElementById("cust-email").value.trim();
    const phone = document.getElementById("cust-phone").value.trim();
    const partySize = parseInt(document.getElementById("cust-party").value);
    const time = document.getElementById("cust-time").value;

    // Safety constraint: double-check that guests do not exceed selected table capacities
    if (partySize > selectedTable.capacity) {
        showAlert("danger", `Over-capacity! Table ${selectedTable.table_number} holds up to ${selectedTable.capacity} guests.`);
        return;
    }

    const payload = {
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
        party_size: partySize,
        reservation_time: new Date(time).toISOString(),
        table_id: selectedTable.id
    };

    try {
        const response = await fetch('/api/reservations/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.detail || "Server validation failed.");
        }

        // Clean user input controls upon successful transaction
        selectedTable = null;
        document.getElementById("booking-form").reset();
        document.getElementById("booking-form").classList.add("opacity-50", "pointer-events-none");
        document.getElementById("table-info-card").innerHTML = `<p class="text-sm font-semibold text-slate-500 text-center py-4">No Table Selected</p>`;
        
        showAlert("success", "Reservation successfully completed! Checked and recorded into system database.");
        
        // Refresh database states dynamically
        await loadAppFromBackend();

    } catch (err) {
        showAlert("danger", err.message);
    }
}

// Filters buttons style toggle and logic distribution
function filterTables(type) {
    currentFilter = type;
    ['filter-all', 'filter-available', 'filter-large'].forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 transition-all";
        }
    });

    const activeBtn = document.getElementById(`filter-${type}`);
    if (activeBtn) {
        activeBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-white transition-all";
    }
    renderTables();
}

// Re-renders list logs for active bookings
function updateReservationsList() {
    const listContainer = document.getElementById("active-reservations-list");
    const countBadge = document.getElementById("total-bookings-count");
    if (countBadge) {
        countBadge.innerText = `${backendReservations.length} Booked`;
    }

    if (!listContainer) return;

    if (backendReservations.length === 0) {
        listContainer.innerHTML = `<p class="text-xs text-slate-400 text-center py-6 font-medium">No reservations completed yet.</p>`;
        return;
    }

    listContainer.innerHTML = "";
    [...backendReservations].reverse().forEach(res => {
        const dateObj = new Date(res.reservation_time);
        const formattedDate = dateObj.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        listContainer.innerHTML += `
            <div class="bg-slate-50 border border-slate-100 p-2.5 rounded-xl text-xs flex items-center justify-between gap-2.5 hover:border-slate-200 transition-all">
                <div class="min-w-0">
                    <h5 class="font-bold text-slate-900 truncate">${res.customer_name}</h5>
                    <p class="text-[10px] text-slate-500 font-medium">${formattedDate} • ${res.party_size} Guests</p>
                </div>
                <span class="bg-slate-200 text-slate-800 font-black px-2 py-1 rounded-md text-[10px] shrink-0">
                    Table ${res.table.table_number}
                </span>
            </div>
        `;
    });
}

function showAlert(type, message) {
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

function clearAlert() {
    const banner = document.getElementById("alert-banner");
    if (banner) banner.classList.add("hidden");
}

// Window init loading logic
window.onload = function() {
    updateNavigationClock();
    configureDateTimeInputLimits();
    loadAppFromBackend();
    
    // Periodically update clock
    setInterval(updateNavigationClock, 60000);
}