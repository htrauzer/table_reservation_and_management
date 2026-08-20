// State variables
export const state = {
    backendTables: [],
    backendReservations: [],
    selectedTable: null,
    currentFilter: 'all',
    currentSelectedDate: document.getElementById('cust-date')?.value || '',
    currentSelectedTime: document.getElementById('time-select')?.value || ''
};

// Configuration Constants
export const RESERVATION_BUFFER_HOURS = 2;