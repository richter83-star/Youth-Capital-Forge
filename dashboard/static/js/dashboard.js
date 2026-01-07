// Cash Engine Dashboard JavaScript

let socket;
let refreshCountdown = 10;
let countdownInterval;
let revenueSourceChart = null;
let revenueTrendChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeCharts();
    loadDashboardData();
    startCountdown();
});

// Initialize WebSocket connection
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to dashboard server');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from dashboard server');
        updateConnectionStatus(false);
    });
    
    socket.on('dashboard_update', function(data) {
        console.log('Received dashboard update');
        updateDashboard(data);
        resetCountdown();
    });
    
    socket.on('connected', function(data) {
        console.log('Server confirmed connection:', data.message);
    });
}

// Initialize charts
function initializeCharts() {
    // Revenue by Source Chart (Pie)
    const revenueSourceCtx = document.getElementById('revenue-source-chart');
    if (revenueSourceCtx) {
        revenueSourceChart = new Chart(revenueSourceCtx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    label: 'Revenue by Source',
                    data: [],
                    backgroundColor: [
                        '#2563eb',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#8b5cf6',
                        '#ec4899'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1'
                        }
                    }
                }
            }
        });
    }
    
    // Revenue Trend Chart (Line)
    const revenueTrendCtx = document.getElementById('revenue-trend-chart');
    if (revenueTrendCtx) {
        revenueTrendChart = new Chart(revenueTrendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Revenue',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#cbd5e1'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        });
    }
}

// Load dashboard data from API
function loadDashboardData() {
    fetch('/api/dashboard')
        .then(response => response.json())
        .then(data => {
            updateDashboard(data);
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
            showError('Failed to load dashboard data');
        });
}

// Update dashboard with new data
function updateDashboard(data) {
    if (!data) return;
    
    // Update revenue cards
    if (data.revenue) {
        updateElement('revenue-today', formatCurrency(data.revenue.today?.total || 0));
        updateElement('revenue-week', formatCurrency(data.revenue.week?.total || 0));
        updateElement('revenue-month', formatCurrency(data.revenue.month?.total || 0));
        
        // Update revenue by source chart
        if (data.revenue.month?.by_source && revenueSourceChart) {
            const sources = Object.keys(data.revenue.month.by_source);
            const amounts = Object.values(data.revenue.month.by_source);
            revenueSourceChart.data.labels = sources;
            revenueSourceChart.data.datasets[0].data = amounts;
            revenueSourceChart.update();
        }
    }
    
    // Update products
    if (data.products) {
        updateElement('total-products', data.products.count || 0);
    }
    
    // Update leads
    if (data.leads) {
        updateElement('total-leads', data.leads.count || 0);
    }
    
    // Update system status
    if (data.system_status) {
        updateSystemStatus(data.system_status);
    }
    
    // Update content performance table
    if (data.content_performance) {
        updateContentPerformanceTable(data.content_performance);
        updateElement('content-items', data.content_performance.length || 0);
    }
    
    // Update campaign performance table
    if (data.campaign_performance) {
        updateCampaignPerformanceTable(data.campaign_performance);
        updateElement('active-campaigns', data.campaign_performance.length || 0);
    }
    
    // Update A/B tests
    if (data.ab_tests) {
        updateElement('active-tests', data.ab_tests.length || 0);
    }
    
    // Update activity feed
    updateActivityFeed(data);
    
    // Update last update timestamp
    if (data.timestamp) {
        const updateTime = new Date(data.timestamp);
        updateElement('last-update', `Last update: ${updateTime.toLocaleTimeString()}`);
    }
}

// Update system status indicators
function updateSystemStatus(status) {
    // Engine status
    const engineStatusEl = document.getElementById('engine-status');
    const engineStatusValueEl = document.getElementById('engine-status-value');
    if (status.engine_running) {
        engineStatusEl.textContent = 'Running';
        engineStatusEl.className = 'status-badge running';
        engineStatusValueEl.textContent = 'Running';
        engineStatusValueEl.className = 'status-value running';
    } else {
        engineStatusEl.textContent = 'Stopped';
        engineStatusEl.className = 'status-badge stopped';
        engineStatusValueEl.textContent = 'Stopped';
        engineStatusValueEl.className = 'status-value stopped';
    }
    
    // Database status
    const dbStatus = document.getElementById('database-status');
    if (status.database_status) {
        dbStatus.textContent = 'Connected';
        dbStatus.className = 'status-value active';
    } else {
        dbStatus.textContent = 'Disconnected';
        dbStatus.className = 'status-value inactive';
    }
    
    // API status
    if (status.api_status) {
        const gumroadStatus = document.getElementById('gumroad-status');
        if (status.api_status.gumroad) {
            gumroadStatus.textContent = 'Connected';
            gumroadStatus.className = 'status-value active';
        } else {
            gumroadStatus.textContent = 'Disconnected';
            gumroadStatus.className = 'status-value inactive';
        }
        
        const marketingAgentStatus = document.getElementById('marketing-agent-status');
        if (status.api_status.marketing_agent) {
            marketingAgentStatus.textContent = 'Connected';
            marketingAgentStatus.className = 'status-value active';
        } else {
            marketingAgentStatus.textContent = 'Disconnected';
            marketingAgentStatus.className = 'status-value inactive';
        }
    }
    
    // Revenue streams
    if (status.revenue_streams) {
        const streamsList = document.getElementById('revenue-streams-list');
        streamsList.innerHTML = status.revenue_streams.map(stream => {
            const statusClass = stream.status === 'active' ? 'active' : '';
            return `<div class="stream-item ${statusClass}">${stream.name}</div>`;
        }).join('');
    }
}

// Update content performance table
function updateContentPerformanceTable(contentPerf) {
    const tbody = document.getElementById('content-performance-body');
    if (!tbody) return;
    
    if (contentPerf.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No content performance data</td></tr>';
        return;
    }
    
    tbody.innerHTML = contentPerf.slice(0, 10).map(item => `
        <tr>
            <td>${escapeHtml(item.content_file || 'N/A')}</td>
            <td>${escapeHtml(item.platform || 'N/A')}</td>
            <td>${item.clicks || 0}</td>
            <td>${item.conversions || 0}</td>
            <td>${formatCurrency(item.revenue || 0)}</td>
        </tr>
    `).join('');
}

// Update campaign performance table
function updateCampaignPerformanceTable(campaignPerf) {
    const tbody = document.getElementById('campaign-performance-body');
    if (!tbody) return;
    
    if (campaignPerf.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No campaign performance data</td></tr>';
        return;
    }
    
    tbody.innerHTML = campaignPerf.slice(0, 10).map(item => `
        <tr>
            <td>${escapeHtml(item.campaign_id || 'N/A')}</td>
            <td>${item.impressions || 0}</td>
            <td>${item.clicks || 0}</td>
            <td>${item.conversions || 0}</td>
            <td>${formatCurrency(item.revenue || 0)}</td>
            <td>${formatCurrency(item.commissions || 0)}</td>
        </tr>
    `).join('');
}

// Update activity feed
function updateActivityFeed(data) {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;
    
    const activities = [];
    
    // Add recent revenue transactions
    if (data.revenue?.month?.recent) {
        data.revenue.month.recent.slice(0, 5).forEach(trans => {
            activities.push({
                type: 'success',
                message: `Revenue: ${formatCurrency(trans.amount)} from ${trans.source}`,
                timestamp: trans.timestamp
            });
        });
    }
    
    // Add recent leads
    if (data.leads?.recent) {
        data.leads.recent.slice(0, 3).forEach(lead => {
            activities.push({
                type: 'success',
                message: `New lead: ${lead.email} from ${lead.source}`,
                timestamp: lead.timestamp
            });
        });
    }
    
    // Sort by timestamp
    activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    if (activities.length === 0) {
        feed.innerHTML = '<div class="activity-item">No recent activity</div>';
        return;
    }
    
    feed.innerHTML = activities.slice(0, 10).map(activity => `
        <div class="activity-item ${activity.type}">
            <div>${activity.message}</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                ${formatTimestamp(activity.timestamp)}
            </div>
        </div>
    `).join('');
}

// Helper functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateConnectionStatus(connected) {
    // Could update UI to show connection status
    console.log('Connection status:', connected ? 'connected' : 'disconnected');
}

function showError(message) {
    console.error(message);
    // Could show error toast/notification
}

function startCountdown() {
    countdownInterval = setInterval(() => {
        refreshCountdown--;
        if (refreshCountdown <= 0) {
            refreshCountdown = 10;
            loadDashboardData();
        }
        updateElement('refresh-countdown', refreshCountdown);
    }, 1000);
}

function resetCountdown() {
    refreshCountdown = 10;
    updateElement('refresh-countdown', refreshCountdown);
}
