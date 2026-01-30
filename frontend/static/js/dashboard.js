/**
 * Robot Telemetry Dashboard - JavaScript
 * With WebSocket support for real-time updates
 */

// Configuration
const CONFIG = {
    refreshInterval: 2000,  // 2 seconds (fallback for polling)
    historyLimit: 50,
    apiBase: '/api',
    maxAlerts: 5,
    alertDuration: 5000
};

// State
let telemetryChart = null;
let temperatureGauge = null;
let historyData = [];
let currentMetric = 'temperature';
let isConnected = true;
let socket = null;
let useWebSocket = true;
let pollingInterval = null;

// DOM Elements
const elements = {
    robotStatus: document.getElementById('robot-status'),
    temperatureValue: document.getElementById('temperature-value'),
    batteryValue: document.getElementById('battery-value'),
    batteryFill: document.getElementById('battery-fill'),
    rpmValue: document.getElementById('rpm-value'),
    rpmBar: document.getElementById('rpm-bar'),
    temperatureGauge: document.getElementById('temperature-gauge'),
    telemetryChart: document.getElementById('telemetry-chart'),
    telemetryTableBody: document.getElementById('telemetry-table-body'),
    connectionStatus: document.getElementById('connection-status'),
    websocketStatus: document.getElementById('websocket-status'),
    lastUpdate: document.getElementById('last-update'),
    commandFeedback: document.getElementById('command-feedback'),
    alertContainer: document.getElementById('alert-container'),
    dataMode: document.getElementById('data-mode'),
    btnStart: document.getElementById('btn-start'),
    btnStop: document.getElementById('btn-stop'),
    btnReset: document.getElementById('btn-reset')
};

/**
 * Initialize the dashboard
 */
function initDashboard() {
    initTemperatureGauge();
    initTelemetryChart();
    initEventListeners();
    initWebSocket();

    // Fetch initial data
    fetchTelemetryHistory();

    // Start polling as fallback
    startPolling();
}

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    try {
        socket = io({
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });

        socket.on('connect', () => {
            console.log('WebSocket connected');
            setWebSocketStatus(true);
            useWebSocket = true;
            elements.dataMode.textContent = 'Real-time';
            elements.dataMode.className = 'badge bg-success';

            // Subscribe to telemetry channel
            socket.emit('subscribe', { channel: 'telemetry' });

            // Stop polling when WebSocket is connected
            stopPolling();
        });

        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            setWebSocketStatus(false);
            useWebSocket = false;
            elements.dataMode.textContent = 'Polling';
            elements.dataMode.className = 'badge bg-secondary';

            // Start polling as fallback
            startPolling();
        });

        socket.on('connect_error', (error) => {
            console.log('WebSocket connection error:', error);
            setWebSocketStatus(false);
            useWebSocket = false;
        });

        socket.on('telemetry_update', (data) => {
            console.log('Received telemetry via WebSocket:', data);
            updateDashboard(data);
            addToHistory(data);
            updateTable();
        });

        socket.on('alert', (alertData) => {
            console.log('Received alert:', alertData);
            showAlert(alertData);
        });

        socket.on('command_result', (result) => {
            console.log('Command result:', result);
            showFeedback(result.message, result.success ? 'success' : 'danger');
        });

        socket.on('connection_status', (data) => {
            console.log('Connection status:', data);
        });

    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        useWebSocket = false;
        startPolling();
    }
}

/**
 * Start polling for telemetry data
 */
function startPolling() {
    if (pollingInterval) return;

    console.log('Starting polling...');
    pollingInterval = setInterval(() => {
        if (!useWebSocket) {
            fetchLatestTelemetry();
        }
    }, CONFIG.refreshInterval);

    // Also refresh history periodically
    setInterval(fetchTelemetryHistory, CONFIG.refreshInterval * 5);
}

/**
 * Stop polling
 */
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('Polling stopped');
    }
}

/**
 * Add telemetry data to history
 */
function addToHistory(data) {
    historyData.push(data);
    if (historyData.length > CONFIG.historyLimit) {
        historyData.shift();
    }
    updateChart();
}

/**
 * Initialize temperature gauge
 */
function initTemperatureGauge() {
    const ctx = elements.temperatureGauge.getContext('2d');

    temperatureGauge = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#28a745', '#e9ecef'],
                borderWidth: 0
            }]
        },
        options: {
            circumference: 180,
            rotation: -90,
            cutout: '70%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

/**
 * Initialize telemetry time-series chart
 */
function initTelemetryChart() {
    const ctx = elements.telemetryChart.getContext('2d');

    telemetryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                data: [],
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });
}

/**
 * Initialize event listeners
 */
function initEventListeners() {
    // Control buttons
    elements.btnStart.addEventListener('click', () => sendCommand('start'));
    elements.btnStop.addEventListener('click', () => sendCommand('stop'));
    elements.btnReset.addEventListener('click', () => sendCommand('reset'));

    // Metric selection buttons
    document.querySelectorAll('[data-metric]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('[data-metric]').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentMetric = e.target.dataset.metric;
            updateChart();
        });
    });
}

/**
 * Fetch latest telemetry data from API
 */
async function fetchLatestTelemetry() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/telemetry/latest`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        updateDashboard(data);
        addToHistory(data);
        updateTable();
        setConnectionStatus(true);

    } catch (error) {
        console.error('Error fetching telemetry:', error);
        setConnectionStatus(false);
    }
}

/**
 * Fetch telemetry history from API
 */
async function fetchTelemetryHistory() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/telemetry/history?limit=${CONFIG.historyLimit}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        historyData = result.data.reverse();  // Oldest first for chart
        updateChart();
        updateTable();

    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

/**
 * Update dashboard with new telemetry data
 */
function updateDashboard(data) {
    // Update robot status
    updateRobotStatus(data.status);

    // Update temperature
    updateTemperature(data.temperature);

    // Update battery
    updateBattery(data.battery);

    // Update motor RPM
    updateRPM(data.motor_rpm);

    // Update last update time
    elements.lastUpdate.textContent = new Date().toLocaleTimeString();
}

/**
 * Update robot status display
 */
function updateRobotStatus(status) {
    const statusElement = elements.robotStatus;
    statusElement.className = 'status-badge';

    const statusConfig = {
        'idle': { class: 'status-idle', icon: 'bi-pause-circle', text: 'IDLE' },
        'working': { class: 'status-working', icon: 'bi-play-circle', text: 'WORKING' },
        'error': { class: 'status-error', icon: 'bi-exclamation-circle', text: 'ERROR' }
    };

    const config = statusConfig[status] || statusConfig['idle'];
    statusElement.classList.add(config.class);
    statusElement.innerHTML = `<i class="bi ${config.icon}"></i><span>${config.text}</span>`;
}

/**
 * Update temperature gauge and display
 */
function updateTemperature(temperature) {
    elements.temperatureValue.textContent = temperature.toFixed(1);

    // Calculate percentage for gauge (35-60 range)
    const minTemp = 35;
    const maxTemp = 60;
    const percentage = Math.min(100, Math.max(0, ((temperature - minTemp) / (maxTemp - minTemp)) * 100));

    // Update gauge
    temperatureGauge.data.datasets[0].data = [percentage, 100 - percentage];

    // Update gauge color based on temperature
    let color = '#28a745';  // Normal
    if (temperature > 50) color = '#dc3545';  // Hot
    else if (temperature > 45) color = '#ffc107';  // Warm
    else if (temperature < 38) color = '#17a2b8';  // Cold

    temperatureGauge.data.datasets[0].backgroundColor[0] = color;
    temperatureGauge.update('none');

    // Update text color
    elements.temperatureValue.style.color = color;
}

/**
 * Update battery display
 */
function updateBattery(battery) {
    elements.batteryValue.textContent = battery;
    elements.batteryFill.style.width = `${battery}%`;

    // Update color based on level
    elements.batteryFill.classList.remove('low', 'medium');
    if (battery < 20) {
        elements.batteryFill.classList.add('low');
    } else if (battery < 40) {
        elements.batteryFill.classList.add('medium');
    }
}

/**
 * Update motor RPM display
 */
function updateRPM(rpm) {
    elements.rpmValue.textContent = rpm;

    // Update progress bar (0-1800 range)
    const percentage = (rpm / 1800) * 100;
    elements.rpmBar.style.width = `${percentage}%`;
    elements.rpmBar.setAttribute('aria-valuenow', rpm);
}

/**
 * Update the telemetry chart
 */
function updateChart() {
    if (!historyData.length) return;

    const labels = historyData.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleTimeString();
    });

    const metricConfig = {
        'temperature': {
            label: 'Temperature (°C)',
            color: '#dc3545',
            data: historyData.map(d => d.temperature)
        },
        'battery': {
            label: 'Battery (%)',
            color: '#28a745',
            data: historyData.map(d => d.battery)
        },
        'motor_rpm': {
            label: 'Motor RPM',
            color: '#17a2b8',
            data: historyData.map(d => d.motor_rpm)
        }
    };

    const config = metricConfig[currentMetric];

    telemetryChart.data.labels = labels;
    telemetryChart.data.datasets[0].label = config.label;
    telemetryChart.data.datasets[0].data = config.data;
    telemetryChart.data.datasets[0].borderColor = config.color;
    telemetryChart.data.datasets[0].backgroundColor = config.color + '20';

    telemetryChart.update('none');
}

/**
 * Update the telemetry table
 */
function updateTable() {
    const recentData = [...historyData].reverse().slice(0, 10);

    elements.telemetryTableBody.innerHTML = recentData.map(d => {
        const time = new Date(d.timestamp).toLocaleTimeString();
        const statusClass = {
            'idle': 'bg-secondary',
            'working': 'bg-success',
            'error': 'bg-danger'
        }[d.status] || 'bg-secondary';

        return `
            <tr>
                <td>${time}</td>
                <td>${d.temperature.toFixed(1)}°C</td>
                <td>${d.battery}%</td>
                <td>${d.motor_rpm}</td>
                <td><span class="badge ${statusClass} badge-status">${d.status}</span></td>
            </tr>
        `;
    }).join('');
}

/**
 * Send command to robot
 */
async function sendCommand(command) {
    try {
        // Disable buttons temporarily
        setButtonsLoading(true);

        const response = await fetch(`${CONFIG.apiBase}/robot/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command })
        });

        const result = await response.json();

        showFeedback(result.message, result.success ? 'success' : 'danger');

        // Refresh telemetry immediately
        if (!useWebSocket) {
            fetchLatestTelemetry();
        }

    } catch (error) {
        console.error('Error sending command:', error);
        showFeedback('Failed to send command', 'danger');
    } finally {
        setButtonsLoading(false);
    }
}

/**
 * Show feedback message
 */
function showFeedback(message, type = 'info') {
    const feedback = elements.commandFeedback;
    feedback.className = `alert alert-${type} mt-3`;
    feedback.textContent = message;
    feedback.classList.remove('d-none');

    // Auto-hide after 3 seconds
    setTimeout(() => {
        feedback.classList.add('d-none');
    }, 3000);
}

/**
 * Show alert notification
 */
function showAlert(alertData) {
    const alertId = `alert-${Date.now()}`;
    const alertClass = alertData.type === 'critical' ? 'alert-danger' : 'alert-warning';
    const iconClass = alertData.type === 'critical' ? 'bi-exclamation-triangle-fill' : 'bi-exclamation-circle-fill';

    const alertHtml = `
        <div id="${alertId}" class="alert ${alertClass} alert-dismissible fade show d-flex align-items-center" role="alert">
            <i class="bi ${iconClass} me-2"></i>
            <div>
                <strong>${alertData.category.toUpperCase()}:</strong> ${alertData.message}
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    elements.alertContainer.insertAdjacentHTML('beforeend', alertHtml);

    // Limit number of visible alerts
    const alerts = elements.alertContainer.querySelectorAll('.alert');
    if (alerts.length > CONFIG.maxAlerts) {
        alerts[0].remove();
    }

    // Auto-remove after duration
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.remove();
        }
    }, CONFIG.alertDuration);
}

/**
 * Set connection status
 */
function setConnectionStatus(connected) {
    isConnected = connected;
    const status = elements.connectionStatus;

    if (connected) {
        status.className = 'badge bg-success';
        status.innerHTML = '<i class="bi bi-wifi"></i> API Connected';
    } else {
        status.className = 'badge bg-danger';
        status.innerHTML = '<i class="bi bi-wifi-off"></i> API Disconnected';
    }
}

/**
 * Set WebSocket status
 */
function setWebSocketStatus(connected) {
    const status = elements.websocketStatus;

    if (connected) {
        status.className = 'badge bg-success';
        status.innerHTML = '<i class="bi bi-broadcast"></i> WebSocket';
    } else {
        status.className = 'badge bg-warning';
        status.innerHTML = '<i class="bi bi-broadcast"></i> Connecting...';
    }
}

/**
 * Set buttons loading state
 */
function setButtonsLoading(loading) {
    const buttons = [elements.btnStart, elements.btnStop, elements.btnReset];
    buttons.forEach(btn => {
        btn.disabled = loading;
        if (loading) {
            btn.classList.add('loading');
        } else {
            btn.classList.remove('loading');
        }
    });
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', initDashboard);
