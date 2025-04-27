// backtest.js - Client-side functionality for the MMVB Trading Bot Backtesting

// Initialization
document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initDateRangePicker();
    initCharts();
    setupEventListeners();
    loadInstruments();
    loadStrategies();
    updateServerTime();
    setInterval(updateServerTime, 1000);
});

// Initialize sidebar functionality
function initSidebar() {
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarState', sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded');
        });
    }
    
    // Load saved state
    const savedState = localStorage.getItem('sidebarState');
    if (savedState === 'collapsed') {
        sidebar.classList.add('collapsed');
    }
}

// Initialize date range picker
function initDateRangePicker() {
    const dateRangeInput = document.getElementById('dateRange');
    
    if (dateRangeInput) {
        // Set default dates (last 3 months)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setMonth(endDate.getMonth() - 3);
        
        $(dateRangeInput).daterangepicker({
            startDate: startDate,
            endDate: endDate,
            maxDate: new Date(),
            opens: 'left',
            ranges: {
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'Last 3 Months': [moment().subtract(3, 'months'), moment()],
                'Last 6 Months': [moment().subtract(6, 'months'), moment()],
                'Year to Date': [moment().startOf('year'), moment()],
                'Last Year': [moment().subtract(1, 'year').startOf('year'), moment().subtract(1, 'year').endOf('year')]
            }
        });
    }
}

// Set up event listeners
function setupEventListeners() {
    // Strategy select change
    const strategySelect = document.getElementById('strategySelect');
    if (strategySelect) {
        strategySelect.addEventListener('change', function() {
            loadStrategyParameters(this.value);
        });
    }
    
    // Instrument select change
    const instrumentSelect = document.getElementById('instrumentSelect');
    
    // Advanced options toggle
    const showAdvancedOptions = document.getElementById('showAdvancedOptions');
    const advancedOptions = document.getElementById('advancedOptions');
    
    if (showAdvancedOptions && advancedOptions) {
        showAdvancedOptions.addEventListener('change', function() {
            if (this.checked) {
                advancedOptions.classList.remove('d-none');
            } else {
                advancedOptions.classList.add('d-none');
            }
        });
    }
    
    // Form submission
    const backtestForm = document.getElementById('backtestForm');
    if (backtestForm) {
        backtestForm.addEventListener('submit', function(e) {
            e.preventDefault();
            runBacktest();
        });
    }
    
    // Export report button
    const exportReportBtn = document.getElementById('exportReportBtn');
    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', function() {
            exportBacktestReport();
        });
    }
    
    // Save strategy button
    const saveStrategyBtn = document.getElementById('saveStrategyBtn');
    if (saveStrategyBtn) {
        saveStrategyBtn.addEventListener('click', function() {
            saveOptimizedStrategy();
        });
    }
}

// Load instruments from API
function loadInstruments() {
    const instrumentSelect = document.getElementById('instrumentSelect');
    if (!instrumentSelect) return;
    
    // Clear existing options except the first one
    while (instrumentSelect.options.length > 1) {
        instrumentSelect.remove(1);
    }
    
    // Show loading state
    const loadingOption = document.createElement('option');
    loadingOption.text = 'Loading instruments...';
    loadingOption.disabled = true;
    instrumentSelect.add(loadingOption);
    
    // Fetch instruments from API
    fetch('/api/instruments')
        .then(response => response.json())
        .then(data => {
            // Remove loading option
            instrumentSelect.remove(instrumentSelect.options.length - 1);
            
            // Add instruments to select
            data.forEach(instrument => {
                const option = document.createElement('option');
                option.value = instrument.figi || instrument.id;
                option.text = `${instrument.ticker} - ${instrument.name}`;
                instrumentSelect.add(option);
            });
        })
        .catch(error => {
            console.error('Error loading instruments:', error);
            instrumentSelect.remove(instrumentSelect.options.length - 1);
            const errorOption = document.createElement('option');
            errorOption.text = 'Error loading instruments';
            errorOption.disabled = true;
            instrumentSelect.add(errorOption);
        });
}

// Load strategies from API
function loadStrategies() {
    const strategySelect = document.getElementById('strategySelect');
    if (!strategySelect) return;
    
    // Clear existing options except the first one
    while (strategySelect.options.length > 1) {
        strategySelect.remove(1);
    }
    
    // Show loading state
    const loadingOption = document.createElement('option');
    loadingOption.text = 'Loading strategies...';
    loadingOption.disabled = true;
    strategySelect.add(loadingOption);
    
    // Fetch strategies from API
    fetch('/api/strategies')
        .then(response => response.json())
        .then(data => {
            // Remove loading option
            strategySelect.remove(strategySelect.options.length - 1);
            
            // Add strategies to select
            data.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id;
                option.text = strategy.name;
                strategySelect.add(option);
            });
        })
        .catch(error => {
            console.error('Error loading strategies:', error);
            strategySelect.remove(strategySelect.options.length - 1);
            const errorOption = document.createElement('option');
            errorOption.text = 'Error loading strategies';
            errorOption.disabled = true;
            strategySelect.add(errorOption);
        });
}

// Load strategy parameters based on selection
function loadStrategyParameters(strategyId) {
    const strategyParams = document.getElementById('strategyParams');
    if (!strategyParams) return;
    
    // Clear existing parameters
    strategyParams.innerHTML = '<div class="text-center my-3"><div class="spinner-border spinner-border-sm" role="status"></div> Loading parameters...</div>';
    
    // Fetch strategy parameters from API
    fetch(`/api/strategies/${strategyId}`)
        .then(response => response.json())
        .then(data => {
            renderStrategyParameters(strategyParams, data);
        })
        .catch(error => {
            console.error('Error loading strategy parameters:', error);
            strategyParams.innerHTML = '<div class="alert alert-danger">Error loading strategy parameters</div>';
        });
}

// Render strategy parameters form elements
function renderStrategyParameters(container, strategyData) {
    // Clear container
    container.innerHTML = '';
    
    if (!strategyData.parameters) {
        container.innerHTML = '<div class="alert alert-info">No configurable parameters for this strategy</div>';
        return;
    }
    
    // Create title
    const title = document.createElement('h6');
    title.classList.add('mt-4', 'mb-3');
    title.textContent = 'Strategy Parameters';
    container.appendChild(title);
    
    // Create form elements for each parameter
    const parameters = strategyData.parameters;
    Object.keys(parameters).forEach(paramName => {
        const paramValue = parameters[paramName];
        const paramType = typeof paramValue;
        
        const formGroup = document.createElement('div');
        formGroup.classList.add('mb-3');
        
        const label = document.createElement('label');
        label.classList.add('form-label');
        label.setAttribute('for', `param_${paramName}`);
        label.textContent = formatParamName(paramName);
        formGroup.appendChild(label);
        
        let input;
        if (paramType === 'boolean') {
            const switchDiv = document.createElement('div');
            switchDiv.classList.add('form-check', 'form-switch');
            
            input = document.createElement('input');
            input.classList.add('form-check-input');
            input.setAttribute('type', 'checkbox');
            input.setAttribute('id', `param_${paramName}`);
            input.setAttribute('name', paramName);
            input.checked = paramValue;
            
            const switchLabel = document.createElement('label');
            switchLabel.classList.add('form-check-label');
            switchLabel.setAttribute('for', `param_${paramName}`);
            switchLabel.textContent = paramValue ? 'Enabled' : 'Disabled';
            
            switchDiv.appendChild(input);
            switchDiv.appendChild(switchLabel);
            formGroup.appendChild(switchDiv);
        } else if (Array.isArray(paramValue)) {
            input = document.createElement('select');
            input.classList.add('form-select');
            input.setAttribute('id', `param_${paramName}`);
            input.setAttribute('name', paramName);
            
            paramValue.forEach(option => {
                const optionEl = document.createElement('option');
                optionEl.value = option;
                optionEl.textContent = option;
                input.appendChild(optionEl);
            });
            
            formGroup.appendChild(input);
        } else {
            input = document.createElement('input');
            input.classList.add('form-control');
            input.setAttribute('id', `param_${paramName}`);
            input.setAttribute('name', paramName);
            
            if (paramType === 'number') {
                input.setAttribute('type', 'number');
                input.setAttribute('step', paramName.includes('period') ? '1' : '0.01');
                input.setAttribute('min', '0');
                input.value = paramValue;
            } else {
                input.setAttribute('type', 'text');
                input.value = paramValue;
            }
            
            formGroup.appendChild(input);
        }
        
        container.appendChild(formGroup);
    });
}

// Format parameter name for display (convert snake_case to Title Case)
function formatParamName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Run backtest with current configuration
function runBacktest() {
    // Get form data
    const strategyId = document.getElementById('strategySelect').value;
    const instrumentId = document.getElementById('instrumentSelect').value;
    const dateRange = document.getElementById('dateRange').value.split(' - ');
    const startDate = dateRange[0];
    const endDate = dateRange[1];
    const timeframe = document.getElementById('timeframeSelect').value;
    const initialCapital = parseFloat(document.getElementById('initialCapital').value);
    
    // Get strategy parameters
    const strategyParams = {};
    const paramInputs = document.querySelectorAll('#strategyParams input, #strategyParams select');
    paramInputs.forEach(input => {
        const paramName = input.getAttribute('name');
        let paramValue;
        
        if (input.type === 'checkbox') {
            paramValue = input.checked;
        } else if (input.type === 'number') {
            paramValue = parseFloat(input.value);
        } else {
            paramValue = input.value;
        }
        
        strategyParams[paramName] = paramValue;
    });
    
    // Get advanced options if enabled
    let advancedOptions = {};
    if (document.getElementById('showAdvancedOptions').checked) {
        advancedOptions = {
            commission_pct: parseFloat(document.getElementById('commissionRate').value) / 100,
            slippage_pct: parseFloat(document.getElementById('slippageRate').value) / 100,
            optimize: document.getElementById('optimizeParameters').checked
        };
    }
    
    // Prepare request data
    const requestData = {
        strategy_id: strategyId,
        instrument_id: instrumentId,
        start_date: startDate,
        end_date: endDate,
        timeframe: timeframe,
        initial_capital: initialCapital,
        strategy_params: strategyParams,
        ...advancedOptions
    };
    
    // Show spinner and hide results
    document.getElementById('backtestSpinner').classList.remove('d-none');
    document.getElementById('noBacktestData').classList.add('d-none');
    document.getElementById('backtestResults').classList.add('d-none');
    
    // Send request to API
    fetch('/api/backtest/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
    })
        .then(response => response.json())
        .then(data => {
            // Hide spinner
            document.getElementById('backtestSpinner').classList.add('d-none');
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Display results
            displayBacktestResults(data);
        })
        .catch(error => {
            document.getElementById('backtestSpinner').classList.add('d-none');
            showError('An error occurred while running the backtest');
            console.error('Backtest error:', error);
        });
}

// Display backtest results
function displayBacktestResults(results) {
    // Show results container
    document.getElementById('backtestResults').classList.remove('d-none');
    
    // Update metrics
    document.getElementById('metricTotalReturn').textContent = formatPercentage(results.total_return);
    document.getElementById('metricAnnualizedReturn').textContent = formatPercentage(results.annualized_return);
    document.getElementById('metricSharpeRatio').textContent = results.sharpe_ratio.toFixed(2);
    document.getElementById('metricMaxDrawdown').textContent = formatPercentage(results.max_drawdown);
    document.getElementById('metricWinRate').textContent = formatPercentage(results.win_rate);
    document.getElementById('metricTotalTrades').textContent = results.total_trades;
    document.getElementById('metricProfitFactor').textContent = results.profit_factor.toFixed(2);
    document.getElementById('metricAvgTrade').textContent = formatCurrency(results.avg_trade);
    document.getElementById('metricAvgWinTrade').textContent = formatCurrency(results.avg_win);
    document.getElementById('metricAvgLossTrade').textContent = formatCurrency(results.avg_loss);
    
    // Update charts
    updateEquityCurveChart(results.equity_curve);
    updateMonthlyReturnsChart(results.monthly_returns);
    updateDrawdownChart(results.drawdowns);
    
    // Update trades table
    updateTradesTable(results.trades);
}

// Initialize charts
function initCharts() {
    // Equity curve chart
    const equityCtx = document.getElementById('equityCurveChart');
    if (equityCtx) {
        window.equityChart = new Chart(equityCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Equity',
                    data: [],
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
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
                        ticks: {
                            maxTicksLimit: 10
                        },
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
    
    // Monthly returns chart
    const monthlyCtx = document.getElementById('monthlyReturnsChart');
    if (monthlyCtx) {
        window.monthlyChart = new Chart(monthlyCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Monthly Returns',
                    data: [],
                    backgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return value >= 0 ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)';
                    },
                    borderColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return value >= 0 ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)';
                    },
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return formatPercentage(context.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Drawdown chart
    const drawdownCtx = document.getElementById('drawdownChart');
    if (drawdownCtx) {
        window.drawdownChart = new Chart(drawdownCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Drawdown',
                    data: [],
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return formatPercentage(context.raw);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            maxTicksLimit: 10
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        reverse: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Update equity curve chart
function updateEquityCurveChart(equityCurve) {
    if (!window.equityChart) return;
    
    const dates = equityCurve.map(point => point.date);
    const values = equityCurve.map(point => point.equity);
    
    window.equityChart.data.labels = dates;
    window.equityChart.data.datasets[0].data = values;
    window.equityChart.update();
}

// Update monthly returns chart
function updateMonthlyReturnsChart(monthlyReturns) {
    if (!window.monthlyChart) return;
    
    const months = monthlyReturns.map(point => point.month);
    const returns = monthlyReturns.map(point => point.return * 100);
    
    window.monthlyChart.data.labels = months;
    window.monthlyChart.data.datasets[0].data = returns;
    window.monthlyChart.update();
}

// Update drawdown chart
function updateDrawdownChart(drawdowns) {
    if (!window.drawdownChart) return;
    
    const dates = drawdowns.map(point => point.date);
    const values = drawdowns.map(point => point.drawdown * 100);
    
    window.drawdownChart.data.labels = dates;
    window.drawdownChart.data.datasets[0].data = values;
    window.drawdownChart.update();
}

// Update trades table
function updateTradesTable(trades) {
    const tableBody = document.querySelector('#tradesTable tbody');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add new rows
    trades.forEach((trade, index) => {
        const row = document.createElement('tr');
        
        // Add columns
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${formatDateTime(trade.entry_time)}</td>
            <td>${formatDateTime(trade.exit_time)}</td>
            <td><span class="badge ${trade.type === 'long' ? 'bg-success' : 'bg-danger'}">${trade.type}</span></td>
            <td>${formatPrice(trade.entry_price)}</td>
            <td>${formatPrice(trade.exit_price)}</td>
            <td>${trade.size.toFixed(2)}</td>
            <td class="${trade.pnl >= 0 ? 'text-success' : 'text-danger'}">${formatCurrency(trade.pnl)}</td>
            <td class="${trade.pnl_percent >= 0 ? 'text-success' : 'text-danger'}">${formatPercentage(trade.pnl_percent)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Export backtest report
function exportBacktestReport() {
    // Prepare HTML content for report
    // For now, we'll just create a basic popup
    alert('Export functionality will be implemented soon');
}

// Save optimized strategy
function saveOptimizedStrategy() {
    // Save current backtest parameters as a new strategy
    alert('Save strategy functionality will be implemented soon');
}

// Show error message
function showError(message) {
    document.getElementById('noBacktestData').innerHTML = `
        <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
        <h4 class="text-danger">Error Running Backtest</h4>
        <p>${message}</p>
    `;
    document.getElementById('noBacktestData').classList.remove('d-none');
}

// Format percentage value
function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}

// Format currency value
function formatCurrency(value) {
    return '$' + value.toFixed(2);
}

// Format price value
function formatPrice(value) {
    return '$' + value.toFixed(2);
}

// Format date and time
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Update server time display
function updateServerTime() {
    const serverTimeElement = document.getElementById('serverTime');
    if (serverTimeElement) {
        const now = new Date();
        serverTimeElement.textContent = now.toLocaleTimeString();
    }
} 