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