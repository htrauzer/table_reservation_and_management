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
