/**
 * Real-Time Alert System
 * Monitors sensor data and triggers alerts based on thresholds
 */

class AlertManager {
    constructor() {
        this.alerts = [];
        this.maxAlerts = 50;
        this.thresholds = {
            dias: { min: 1, max: 60 },
        };
        this.alertHistory = new Set(); // Evitar alertas duplicadas
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const alertsLink = document.getElementById('alertsLink');
        const closeAlertsBtn = document.getElementById('closeAlertsBtn');
        const alertsPanel = document.getElementById('alertsPanel');

        if (alertsLink) {
            alertsLink.addEventListener('click', (e) => {
                e.preventDefault();
                alertsPanel.style.display = alertsPanel.style.display === 'none' ? 'block' : 'none';
            });
        }

        if (closeAlertsBtn) {
            closeAlertsBtn.addEventListener('click', () => {
                alertsPanel.style.display = 'none';
            });
        }
    }

    /**
     * Check sensor values against thresholds
     * @param {Object} sensorData - Current sensor readings
     */
    checkThresholds(sensorData) {
        if (!sensorData) return;

        // Temperature alert
        if (sensorData.dias !== null && sensorData.dias !== undefined) {
            this.checkMetric('dias', sensorData.dias, 'Dias restantes');
        }

        // Humidity alert
        if (sensorData.humidity !== null && sensorData.humidity !== undefined) {
            this.checkMetric('humidity', sensorData.humidity, 'Humedad del aire');
        }

        // Soil humidity alert
        if (sensorData.soil_humidity !== null && sensorData.soil_humidity !== undefined) {
            this.checkMetric('soil_humidity', sensorData.soil_humidity, 'Humedad del suelo');
        }

        // pH alert
        if (sensorData.ph !== null && sensorData.ph !== undefined) {
            this.checkMetric('ph', sensorData.ph, 'Nivel de pH');
        }

        // Turbidity alert
        if (sensorData.turbidity !== null && sensorData.turbidity !== undefined) {
            this.checkMetric('turbidity', sensorData.turbidity, 'Turbidez');
        }

        // Corrected PPM alert
        if (sensorData.correctedppm !== null && sensorData.correctedppm !== undefined) {
            this.checkMetric('correctedppm', sensorData.correctedppm, 'PPM Corregido');
        }
    }

    /**
     * Check individual metric against thresholds
     * @param {string} metric - Metric name
     * @param {number} value - Current value
     * @param {string} label - Display label
     */
    checkMetric(metric, value, label) {
        const threshold = this.thresholds[metric];
        if (!threshold) return;

        const alertKey = `${metric}_${value}`;
        let alertType = null;
        let message = null;

        if (value < threshold.min) {
            alertType = 'warning';
            message = `⚠️ ${label} BAJO: ${value} (Mínimo: ${threshold.min})`;
        } else if (value > threshold.max) {
            alertType = 'danger';
            message = `🔴 ${label} ALTO: ${value} (Máximo: ${threshold.max})`;
        }

        // Solo crear alerta si no existe en el historial
        if (alertType && !this.alertHistory.has(alertKey)) {
            this.createAlert(alertType, message, metric, value);
            this.alertHistory.add(alertKey);

            // Limpiar historial después de 10 minutos para permitir nuevas alertas
            setTimeout(() => this.alertHistory.delete(alertKey), 600000);
        }
    }

    /**
     * Create and display an alert
     * @param {string} type - Alert type (info, warning, danger)
     * @param {string} message - Alert message
     * @param {string} metric - Metric name
     * @param {number} value - Metric value
     */
    createAlert(type, message, metric, value) {
        const alert = {
            id: Date.now(),
            type: type,
            message: message,
            metric: metric,
            value: value,
            timestamp: new Date().toLocaleTimeString('es-ES'),
            read: false
        };

        this.alerts.unshift(alert);

        // Mantener máximo de alertas
        if (this.alerts.length > this.maxAlerts) {
            this.alerts.pop();
        }

        this.updateAlertCount();
        this.renderAlerts();
        this.showToast(message, type);
    }

    /**
     * Update alert count badge
     */
    updateAlertCount() {
        const unreadCount = this.alerts.filter(a => !a.read).length;
        const countElement = document.getElementById('alertCount');
        if (countElement) {
            countElement.textContent = unreadCount;
        }
    }

    /**
     * Render alerts list
     */
    renderAlerts() {
        const alertsList = document.getElementById('alertsList');
        if (!alertsList) return;

        if (this.alerts.length === 0) {
            alertsList.innerHTML = '<p class="no-alerts">No hay alertas activas</p>';
            return;
        }

        alertsList.innerHTML = this.alerts.map(alert => `
            <div class="alert-item alert-${alert.type}" data-id="${alert.id}">
                <div class="alert-content">
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${alert.timestamp}</div>
                </div>
                <button class="alert-close" onclick="alertManager.dismissAlert(${alert.id})">✕</button>
            </div>
        `).join('');
    }

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    /**
     * Dismiss an alert
     * @param {number} alertId - Alert ID
     */
    dismissAlert(alertId) {
        this.alerts = this.alerts.filter(a => a.id !== alertId);
        this.updateAlertCount();
        this.renderAlerts();
    }

    /**
     * Dismiss all alerts
     */
    dismissAllAlerts() {
        this.alerts = [];
        this.updateAlertCount();
        this.renderAlerts();
    }

    /**
     * Set custom threshold for a metric
     * @param {string} metric - Metric name
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     */
    setThreshold(metric, min, max) {
        if (this.thresholds.hasOwnProperty(metric)) {
            this.thresholds[metric] = { min, max };
        }
    }

    /**
     * Get all alerts
     */
    getAlerts() {
        return this.alerts;
    }

    /**
     * Get unread alerts count
     */
    getUnreadCount() {
        return this.alerts.filter(a => !a.read).length;
    }
}

// Initialize alert manager
const alertManager = new AlertManager();
