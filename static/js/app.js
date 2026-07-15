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