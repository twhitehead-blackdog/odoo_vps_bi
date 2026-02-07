/**
 * Odoo BI Portal - JavaScript
 */

let syncPollInterval = null;

/**
 * Inicia una sincronización (incremental o completa)
 */
function startSync(full) {
    const body = { full: !!full };

    fetch('/api/sync/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        showSyncModal();
    })
    .catch(err => alert('Error al iniciar sync: ' + err));
}

/**
 * Sincroniza un modelo específico
 */
function syncModel(modelName) {
    const body = { models: [modelName] };

    fetch('/api/sync/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        showSyncModal();
    })
    .catch(err => alert('Error al iniciar sync: ' + err));
}

/**
 * Muestra el modal de sync y empieza a hacer polling de la salida
 */
function showSyncModal() {
    const modal = new bootstrap.Modal(document.getElementById('syncModal'));
    const outputEl = document.getElementById('sync-output');
    const statusEl = document.getElementById('sync-modal-status');
    const closeBtn = document.getElementById('sync-close-btn');
    const indicator = document.getElementById('sync-indicator');

    outputEl.textContent = 'Iniciando sincronizacion...\n';
    closeBtn.disabled = true;
    if (indicator) indicator.classList.remove('d-none');

    modal.show();

    // Poll output
    if (syncPollInterval) clearInterval(syncPollInterval);
    syncPollInterval = setInterval(() => {
        fetch('/api/sync/output')
            .then(r => r.json())
            .then(data => {
                outputEl.textContent = data.output || 'Esperando salida...\n';
                outputEl.scrollTop = outputEl.scrollHeight;

                if (!data.running) {
                    clearInterval(syncPollInterval);
                    syncPollInterval = null;
                    closeBtn.disabled = false;
                    statusEl.textContent = 'Sincronizacion completada';
                    if (indicator) indicator.classList.add('d-none');

                    // Refresh page after closing modal
                    document.getElementById('syncModal').addEventListener('hidden.bs.modal', () => {
                        location.reload();
                    }, { once: true });
                } else {
                    statusEl.textContent = 'Ejecutando...';
                }
            })
            .catch(() => {});
    }, 1000);
}

/**
 * Check if sync is running on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/sync/status')
        .then(r => r.json())
        .then(data => {
            const indicator = document.getElementById('sync-indicator');
            if (data.running && indicator) {
                indicator.classList.remove('d-none');
            }
        })
        .catch(() => {});
});
