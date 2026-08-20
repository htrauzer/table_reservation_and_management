import { state, RESERVATION_BUFFER_HOURS } from './state.js';
import { showAlert, renderTables, updateReservationsList } from './ui.js';

export async function loadAppFromBackend() {
    try {
        const [tablesResponse, reservationsResponse] = await Promise.all([
            fetch('/api/tables/'),
            fetch('/api/reservations/')
        ]);

        if (!tablesResponse.ok || !reservationsResponse.ok) {
            throw new Error("Failed to load initial data from backend.");
        }

        state.backendTables = await tablesResponse.json();
        state.backendReservations = await reservationsResponse.json();

        evaluateCalendarSchedule();
    } catch (err) {
        showAlert("danger", "Could not connect to FastAPI server. Please verify your backend service.");
    }
}

export function evaluateCalendarSchedule() {
    if (!state.currentSelectedDate || !state.currentSelectedTime) {
        state.backendTables.forEach(table => {
            table.status = table.is_active ? 'available' : 'out_of_service';
        });
        renderTables();
        return;
    }

    const targetTime = new Date(`${state.currentSelectedDate}T${state.currentSelectedTime}:00`);

    state.backendTables.forEach(table => {
        if (!table.is_active) {
            table.status = 'out_of_service';
            return;
        }

        const overlappingConflict = state.backendReservations.find(res => {
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

    if (state.selectedTable) {
        const refreshedState = state.backendTables.find(t => t.id === state.selectedTable.id);
        if (refreshedState && refreshedState.status !== 'available') {
            state.selectedTable = null;
            const infoCard = document.getElementById("table-info-card");
            if (infoCard) {
                infoCard.innerHTML = `<p class="text-sm font-semibold text-slate-500 text-center py-4">No Table Selected</p>`;
            }
        }
    }

    renderTables();
    updateReservationsList();
}