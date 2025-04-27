/**
 * Main JavaScript file for trading bot web interface
 */

// DOM Elements
const accountsTable = document.getElementById('accounts-table');
const tradesTable = document.getElementById('trades-table');
const refreshAccountsBtn = document.getElementById('refresh-accounts');
const refreshHistoryBtn = document.getElementById('refresh-history');
const historyFilter = document.getElementById('history-filter');
const tradingSessionForm = document.getElementById('trading-session-form');
const brokerSelect = document.getElementById('broker-select');
const accountSelect = document.getElementById('account-select');
const strategySelect = document.getElementById('strategy-select');
const instrumentSelect = document.getElementById('instrument-select');

// Connection status elements
const connectionStatus = document.getElementById('connection-status');
const activeSessions = document.getElementById('active-sessions');
const todayTrades = document.getElementById('today-trades');
const todayPnl = document.getElementById('today-pnl');

// API endpoints
const API = {
    accounts: '/api/accounts',
    portfolio: (broker, accountId) => `/api/portfolio/${broker}/${accountId}`,
    trades: '/api/trades',
    portfolioHistory: '/api/portfolio_history',
    strategies: '/api/strategies',
    instruments: (broker) => `/api/market/instruments/${broker}`,
    startTradingSession: '/api/trading_session/start',
    stopTradingSession: '/api/trading_session/stop'
};

/**
 * Fetch data from API
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} - JSON response
 */
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error (${response.status}): ${errorText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        showNotification('error', `Ошибка запроса: ${error.message}`);
        return null;
    }
}

/**
 * Format currency amount
 * @param {number} amount - Amount to format
 * @returns {string} - Formatted amount
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Format date to locale string
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

/**
 * Show notification
 * @param {string} type - Notification type (success, error, info)
 * @param {string} message - Notification message
 */
function showNotification(type, message) {
    // Simple implementation using alert (can be replaced with a modal or toast)
    alert(`${type.toUpperCase()}: ${message}`);
}

/**
 * Load and display accounts
 */
async function loadAccounts() {
    const accounts = await fetchAPI(API.accounts);
    
    if (!accounts) return;
    
    // Clear table
    const tbody = accountsTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Add accounts to table
    accounts.forEach(account => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td>${account.broker}</td>
            <td>${account.id}</td>
            <td>${account.type || '-'}</td>
            <td>${account.balance ? formatCurrency(account.balance) : '-'}</td>
            <td><span class="badge bg-success">Активен</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary view-portfolio" 
                        data-broker="${account.broker}" 
                        data-account="${account.id}">
                    Портфель
                </button>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
    
    // If no accounts, show message
    if (accounts.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="6" class="text-center">Нет доступных счетов</td>';
        tbody.appendChild(tr);
    }
    
    // Update account select
    populateAccountSelect(accounts);
}

/**
 * Populate account select dropdown
 * @param {Array} accounts - List of accounts
 */
function populateAccountSelect(accounts) {
    // Filter accounts by selected broker
    const broker = brokerSelect.value;
    const filteredAccounts = accounts.filter(account => account.broker === broker);
    
    // Clear select
    accountSelect.innerHTML = '';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.disabled = true;
    defaultOption.selected = true;
    defaultOption.textContent = filteredAccounts.length > 0 
        ? 'Выберите счет' 
        : 'Нет доступных счетов';
    accountSelect.appendChild(defaultOption);
    
    // Add accounts to select
    filteredAccounts.forEach(account => {
        const option = document.createElement('option');
        option.value = account.id;
        option.textContent = `${account.id} (${account.type || 'Счет'})`;
        accountSelect.appendChild(option);
    });
    
    // Enable/disable select
    accountSelect.disabled = !(broker && filteredAccounts.length > 0);
}

/**
 * Load and display trades
 */
async function loadTrades() {
    const days = historyFilter.value;
    const trades = await fetchAPI(`${API.trades}?days=${days}`);
    
    if (!trades) return;
    
    // Clear table
    const tbody = tradesTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Add trades to table
    trades.forEach(trade => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td>${formatDate(trade.timestamp)}</td>
            <td>${trade.instrument_id}</td>
            <td>
                <span class="badge ${trade.direction === 'buy' ? 'bg-success' : 'bg-danger'}">
                    ${trade.direction === 'buy' ? 'Покупка' : 'Продажа'}
                </span>
            </td>
            <td>${trade.quantity}</td>
            <td>${formatCurrency(trade.price)}</td>
            <td>${formatCurrency(trade.total_value)}</td>
            <td>${trade.broker}</td>
            <td>${trade.account_id}</td>
        `;
        
        tbody.appendChild(tr);
    });
    
    // If no trades, show message
    if (trades.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="8" class="text-center">Нет данных о сделках за выбранный период</td>';
        tbody.appendChild(tr);
    }
    
    // Update today trades count
    const todayTradesCount = trades.filter(trade => {
        const tradeDate = new Date(trade.timestamp);
        const today = new Date();
        return tradeDate.toDateString() === today.toDateString();
    }).length;
    
    todayTrades.textContent = todayTradesCount;
    
    // Update P&L (simplified example - in real app this would be calculated from portfolio history)
    if (trades.length > 0) {
        const randomPnL = Math.round((Math.random() * 2000 - 1000) * 100) / 100;
        todayPnl.textContent = formatCurrency(randomPnL);
        todayPnl.parentElement.classList.remove('bg-success', 'bg-danger', 'bg-primary');
        todayPnl.parentElement.classList.add(randomPnL >= 0 ? 'bg-success' : 'bg-danger');
    }
}

/**
 * Load instruments for selected broker
 */
async function loadInstruments() {
    const broker = brokerSelect.value;
    
    if (!broker) {
        instrumentSelect.innerHTML = '<option value="" selected disabled>Сначала выберите брокера</option>';
        instrumentSelect.disabled = true;
        return;
    }
    
    // In a real app, this would be an API call to get instruments
    // For demo, we'll use some sample data
    const sampleInstruments = {
        'tinkoff': [
            { figi: 'BBG004730N88', ticker: 'SBER', name: 'Сбербанк' },
            { figi: 'BBG004RVFCY3', ticker: 'GAZP', name: 'Газпром' },
            { figi: 'BBG004731354', ticker: 'LKOH', name: 'Лукойл' },
            { figi: 'BBG000NL6ZD9', ticker: 'AAPL', name: 'Apple Inc.' },
            { figi: 'BBG000BVPV84', ticker: 'AMZN', name: 'Amazon' }
        ],
        'bcs': [
            { id: '1', ticker: 'SBER', name: 'Сбербанк' },
            { id: '2', ticker: 'GAZP', name: 'Газпром' },
            { id: '3', ticker: 'LKOH', name: 'Лукойл' },
            { id: '4', ticker: 'YNDX', name: 'Яндекс' },
            { id: '5', ticker: 'VTBR', name: 'ВТБ' }
        ]
    };
    
    const instruments = sampleInstruments[broker] || [];
    
    // Clear select
    instrumentSelect.innerHTML = '';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.disabled = true;
    defaultOption.selected = true;
    defaultOption.textContent = 'Выберите инструмент';
    instrumentSelect.appendChild(defaultOption);
    
    // Add instruments to select
    instruments.forEach(instrument => {
        const option = document.createElement('option');
        option.value = broker === 'tinkoff' ? instrument.figi : instrument.id;
        option.textContent = `${instrument.ticker} - ${instrument.name}`;
        instrumentSelect.appendChild(option);
    });
    
    // Enable select
    instrumentSelect.disabled = false;
}

/**
 * Submit trading session form
 * @param {Event} event - Form submit event
 */
async function submitTradingSessionForm(event) {
    event.preventDefault();
    
    const broker = brokerSelect.value;
    const accountId = accountSelect.value;
    const strategy = strategySelect.value;
    const instrumentId = instrumentSelect.value;
    const riskPercent = document.getElementById('risk-percent').value;
    const fastMA = document.getElementById('fast-ma').value;
    const slowMA = document.getElementById('slow-ma').value;
    
    if (!broker || !accountId || !strategy || !instrumentId) {
        showNotification('error', 'Пожалуйста, заполните все обязательные поля');
        return;
    }
    
    // Prepare data for API
    const data = {
        broker,
        account_id: accountId,
        strategy,
        instruments: [instrumentId],
        parameters: {
            risk_percent: parseFloat(riskPercent),
            fast_ma: parseInt(fastMA),
            slow_ma: parseInt(slowMA)
        }
    };
    
    // Send request to API
    const response = await fetchAPI(API.startTradingSession, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (response && response.status === 'success') {
        showNotification('success', 'Торговая сессия успешно запущена');
        
        // Update active sessions count
        activeSessions.textContent = parseInt(activeSessions.textContent) + 1;
    }
}

/**
 * Initialize event listeners
 */
function initEventListeners() {
    // Refresh accounts button
    refreshAccountsBtn.addEventListener('click', loadAccounts);
    
    // Refresh trades button
    refreshHistoryBtn.addEventListener('click', loadTrades);
    
    // History filter change
    historyFilter.addEventListener('change', loadTrades);
    
    // Broker select change
    brokerSelect.addEventListener('change', () => {
        loadInstruments();
        // Also update account select using existing accounts data
        fetchAPI(API.accounts).then(populateAccountSelect);
    });
    
    // Trading session form submit
    tradingSessionForm.addEventListener('submit', submitTradingSessionForm);
    
    // View portfolio buttons (delegated)
    accountsTable.addEventListener('click', event => {
        const button = event.target.closest('.view-portfolio');
        
        if (button) {
            const broker = button.dataset.broker;
            const accountId = button.dataset.account;
            
            // In a real app, this would open a modal or navigate to a portfolio view
            alert(`Портфель для счета ${accountId} брокера ${broker}`);
        }
    });
}

/**
 * Initialize application
 */
function init() {
    // Set connection status
    connectionStatus.textContent = 'Подключено';
    connectionStatus.parentElement.classList.remove('bg-danger');
    connectionStatus.parentElement.classList.add('bg-success');
    
    // Initialize event listeners
    initEventListeners();
    
    // Load initial data
    loadAccounts();
    loadTrades();
    
    // Simulate active sessions (for demo)
    activeSessions.textContent = '0';
    
    console.log('Trading Bot Web Interface initialized');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init); 