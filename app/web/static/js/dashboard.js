// Dashboard.js - Client-side functionality for the MMVB Trading Bot Dashboard

// Dashboard Initialization
document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initTooltips();
    initCharts();
    setupEventListeners();
    loadActiveSessions();
    loadRecentTrades();
    updateServerTime();
    setInterval(updateServerTime, 1000);
});

// Initialize Bootstrap tooltips and popovers
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Sidebar Toggle
function initSidebar() {
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            
            // Store sidebar state in localStorage
            localStorage.setItem('sidebarState', sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded');
        });
    }
    
    // Check if there's a saved sidebar state
    const savedState = localStorage.getItem('sidebarState');
    if (savedState === 'collapsed') {
        sidebar.classList.add('collapsed');
    }
}

// Chart Initialization
function initCharts() {
    // Portfolio Value Chart
    const portfolioCtx = document.getElementById('portfolioValueChart');
    
    if (portfolioCtx) {
        const portfolioChart = new Chart(portfolioCtx, {
            type: 'line',
            data: {
                labels: generateTimeLabels(30),
                datasets: [{
                    label: 'Portfolio Value',
                    data: generateRandomData(30, 10000, 12000),
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(13, 110, 253, 1)',
                    pointBorderColor: '#fff',
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `$${context.raw.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    // Strategy Performance Chart
    const performanceCtx = document.getElementById('performanceChart');
    
    if (performanceCtx) {
        const performanceChart = new Chart(performanceCtx, {
            type: 'doughnut',
            data: {
                labels: ['Mean Reversion', 'Moving Average', 'Momentum', 'Other'],
                datasets: [{
                    data: [42, 23, 15, 20],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(13, 110, 253, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(108, 117, 125, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // New Session Form
    const createSessionForm = document.getElementById('createSessionForm');
    const strategySelect = document.getElementById('strategySelect');
    const showAdvancedOptions = document.getElementById('showAdvancedOptions');
    const advancedOptions = document.getElementById('advancedOptions');
    
    if (createSessionForm) {
        createSessionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createNewSession();
        });
    }
    
    if (strategySelect) {
        strategySelect.addEventListener('change', function() {
            loadStrategyParameters(this.value);
        });
    }
    
    if (showAdvancedOptions && advancedOptions) {
        showAdvancedOptions.addEventListener('change', function() {
            if (this.checked) {
                advancedOptions.classList.remove('d-none');
            } else {
                advancedOptions.classList.add('d-none');
            }
        });
    }
}

// Load strategy parameters based on selection
function loadStrategyParameters(strategyId) {
    const strategyParams = document.getElementById('strategyParams');
    if (!strategyParams) return;
    
    showSpinner(true);
    
    // Fetch strategy parameters from API
    fetch(`/api/strategies/${strategyId}/parameters`)
        .then(response => response.json())
        .then(data => {
            renderStrategyParameters(data.parameters);
            showSpinner(false);
        })
        .catch(error => {
            console.error('Error fetching strategy parameters:', error);
            showToast('Failed to load strategy parameters', 'error');
            showSpinner(false);
        });
}

// Render strategy parameters in the form
function renderStrategyParameters(parameters) {
    const strategyParams = document.getElementById('strategyParams');
    if (!strategyParams) return;
    
    strategyParams.innerHTML = '<h6 class="mb-3">Strategy Parameters</h6>';
    
    parameters.forEach(param => {
        let inputHtml = '';
        
        switch (param.type) {
            case 'number':
                inputHtml = `
                    <div class="mb-3">
                        <label for="${param.id}" class="form-label">${param.name}</label>
                        <input type="number" class="form-control" id="${param.id}" name="${param.id}" 
                            value="${param.default}" min="${param.min}" max="${param.max}" step="${param.step}">
                        <div class="form-text">${param.description}</div>
                    </div>
                `;
                break;
            case 'select':
                let options = param.options.map(option => 
                    `<option value="${option.value}" ${option.value === param.default ? 'selected' : ''}>${option.label}</option>`
                ).join('');
                
                inputHtml = `
                    <div class="mb-3">
                        <label for="${param.id}" class="form-label">${param.name}</label>
                        <select class="form-select" id="${param.id}" name="${param.id}">
                            ${options}
                        </select>
                        <div class="form-text">${param.description}</div>
                    </div>
                `;
                break;
            case 'checkbox':
                inputHtml = `
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="${param.id}" name="${param.id}" ${param.default ? 'checked' : ''}>
                        <label class="form-check-label" for="${param.id}">${param.name}</label>
                        <div class="form-text">${param.description}</div>
                    </div>
                `;
                break;
            default:
                inputHtml = `
                    <div class="mb-3">
                        <label for="${param.id}" class="form-label">${param.name}</label>
                        <input type="text" class="form-control" id="${param.id}" name="${param.id}" value="${param.default}">
                        <div class="form-text">${param.description}</div>
                    </div>
                `;
        }
        
        strategyParams.innerHTML += inputHtml;
    });
}

// Create a new trading session
function createNewSession() {
    const form = document.getElementById('createSessionForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const sessionData = Object.fromEntries(formData.entries());
    
    showSpinner(true);
    
    fetch('/api/sessions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(sessionData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Trading session created successfully', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('newSessionModal'));
            if (modal) modal.hide();
            loadActiveSessions();
        } else {
            showToast(data.message || 'Failed to create session', 'error');
        }
        showSpinner(false);
    })
    .catch(error => {
        console.error('Error creating session:', error);
        showToast('Failed to create session', 'error');
        showSpinner(false);
    });
}

// Load active trading sessions
function loadActiveSessions() {
    showSpinner(true);
    
    fetch('/api/sessions/active')
        .then(response => response.json())
        .then(data => {
            renderActiveSessionsTable(data.sessions);
            showSpinner(false);
        })
        .catch(error => {
            console.error('Error loading active sessions:', error);
            showToast('Failed to load active sessions', 'error');
            showSpinner(false);
        });
}

// Render active sessions table
function renderActiveSessionsTable(sessions) {
    const tableBody = document.querySelector('#activeSessions tbody');
    if (!tableBody) return;
    
    if (!sessions || sessions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No active trading sessions</td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    
    sessions.forEach(session => {
        html += `
            <tr>
                <td>${session.id}</td>
                <td>${session.strategy}</td>
                <td>${session.market}</td>
                <td>$${session.balance.toFixed(2)}</td>
                <td>
                    <span class="badge bg-${
                        session.status === 'running' ? 'success' : 
                        session.status === 'paused' ? 'warning' : 
                        session.status === 'error' ? 'danger' : 'secondary'
                    }">
                        ${session.status}
                    </span>
                </td>
                <td>${formatDateTime(session.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        ${session.status === 'running' ? 
                            `<button type="button" class="btn btn-outline-warning" onclick="pauseSession('${session.id}')" data-bs-toggle="tooltip" data-bs-title="Pause">
                                <i class="fas fa-pause"></i>
                            </button>` : 
                            session.status === 'paused' ? 
                            `<button type="button" class="btn btn-outline-success" onclick="resumeSession('${session.id}')" data-bs-toggle="tooltip" data-bs-title="Resume">
                                <i class="fas fa-play"></i>
                            </button>` : ''
                        }
                        <button type="button" class="btn btn-outline-danger" onclick="stopSession('${session.id}')" data-bs-toggle="tooltip" data-bs-title="Stop">
                            <i class="fas fa-stop"></i>
                        </button>
                        <button type="button" class="btn btn-outline-primary" onclick="viewSession('${session.id}')" data-bs-toggle="tooltip" data-bs-title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // Reinitialize tooltips
    var tooltipTriggerList = [].slice.call(tableBody.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Load recent trades
function loadRecentTrades() {
    showSpinner(true);
    
    fetch('/api/trades/recent')
        .then(response => response.json())
        .then(data => {
            renderRecentTradesTable(data.trades);
            showSpinner(false);
        })
        .catch(error => {
            console.error('Error loading recent trades:', error);
            showToast('Failed to load recent trades', 'error');
            showSpinner(false);
        });
}

// Render recent trades table
function renderRecentTradesTable(trades) {
    const tableBody = document.querySelector('#recentTrades tbody');
    if (!tableBody) return;
    
    if (!trades || trades.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No recent trades</td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    
    trades.forEach(trade => {
        html += `
            <tr>
                <td>${formatTime(trade.time)}</td>
                <td>${trade.market}</td>
                <td>${trade.type}</td>
                <td class="text-${trade.side === 'buy' ? 'success' : 'danger'}">${trade.side.toUpperCase()}</td>
                <td>$${trade.price.toFixed(2)}</td>
                <td>${trade.quantity}</td>
                <td>$${trade.total.toFixed(2)}</td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Session actions
function pauseSession(sessionId) {
    sessionAction(sessionId, 'pause');
}

function resumeSession(sessionId) {
    sessionAction(sessionId, 'resume');
}

function stopSession(sessionId) {
    if (confirm('Are you sure you want to stop this trading session?')) {
        sessionAction(sessionId, 'stop');
    }
}

function viewSession(sessionId) {
    window.location.href = `/sessions/${sessionId}`;
}

// Perform a session action (pause, resume, stop)
function sessionAction(sessionId, action) {
    showSpinner(true);
    
    fetch(`/api/sessions/${sessionId}/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Session ${action} successful`, 'success');
            loadActiveSessions();
        } else {
            showToast(data.message || `Failed to ${action} session`, 'error');
        }
        showSpinner(false);
    })
    .catch(error => {
        console.error(`Error ${action}ing session:`, error);
        showToast(`Failed to ${action} session`, 'error');
        showSpinner(false);
    });
}

// Update server time display
function updateServerTime() {
    const serverTimeElement = document.getElementById('serverTime');
    if (serverTimeElement) {
        const now = new Date();
        serverTimeElement.textContent = now.toLocaleTimeString();
    }
}

// Helper Functions
function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleString();
}

function formatTime(timeStr) {
    const date = new Date(timeStr);
    return date.toLocaleTimeString();
}

function generateTimeLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(now.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    return labels;
}

function generateRandomData(count, min, max) {
    const data = [];
    for (let i = 0; i < count; i++) {
        data.push(Math.random() * (max - min) + min);
    }
    return data;
}

// UI Helpers
function showSpinner(show) {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        if (show) {
            spinner.classList.add('show');
        } else {
            spinner.classList.remove('show');
        }
    }
}

function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 
                  type === 'error' ? 'bg-danger' : 
                  type === 'warning' ? 'bg-warning' : 'bg-info';
    
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header text-white ${bgClass}">
                <strong class="me-auto">
                    <i class="fas ${
                        type === 'success' ? 'fa-check-circle' : 
                        type === 'error' ? 'fa-exclamation-circle' : 
                        type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'
                    }"></i>
                    ${type.charAt(0).toUpperCase() + type.slice(1)}
                </strong>
                <small>Now</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove the toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
} 