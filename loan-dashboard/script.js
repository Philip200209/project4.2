// Global chart instance
let loanChartInstance = null;

// API call to fetch data
async function fetchDashboardData() {
    try {
        console.log('Fetching data from API...');
        
        const response = await fetch('http://192.168.100.2:5000/dashboard/api/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Raw API response:', data);
        
        // Convert string numbers to actual numbers
        if (data.loan_stats) {
            data.loan_stats.pending = parseInt(data.loan_stats.pending) || 0;
            data.loan_stats.approved = parseInt(data.loan_stats.approved) || 0;
            data.loan_stats.rejected = parseInt(data.loan_stats.rejected) || 0;
            data.loan_stats.total = parseInt(data.loan_stats.total) || 0;
        }
        
        data.recent_count = parseInt(data.recent_count) || 0;
        
        console.log('Processed data:', data);
        return data;
        
    } catch (error) {
        console.error('API call failed:', error);
        return {
            loan_stats: {
                approved: 0,
                pending: 2,
                rejected: 0,
                total: 2
            },
            recent_count: 2,
            role: "admin"
        };
    }
}

// Update the dashboard with the fetched data
function updateDashboard(data) {
    console.log('Updating dashboard with:', data);
    
    document.getElementById('approved-count').textContent = data.loan_stats.approved;
    document.getElementById('pending-count').textContent = data.loan_stats.pending;
    document.getElementById('rejected-count').textContent = data.loan_stats.rejected;
    document.getElementById('total-count').textContent = data.loan_stats.total;
    
    document.getElementById('recent-activity-text').textContent = 
        `${data.recent_count} new applications pending review`;
    
    updateChart(data);
    hideLoading();
}

// Create and update the chart
function updateChart(data) {
    const ctx = document.getElementById('loanChart');
    
    if (!ctx) {
        console.error('Chart canvas not found!');
        return;
    }
    
    if (loanChartInstance) {
        loanChartInstance.destroy();
    }
    
    loanChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Approved', 'Pending', 'Rejected'],
            datasets: [{
                data: [data.loan_stats.approved, data.loan_stats.pending, data.loan_stats.rejected],
                backgroundColor: [
                    '#4ade80',
                    '#f59e0b', 
                    '#ef4444'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Show loading state
function showLoading() {
    const statsGrid = document.querySelector('.stats-grid');
    const chartContainer = document.querySelector('.chart-container');
    
    if (statsGrid) {
        statsGrid.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading dashboard data...</p>
            </div>
        `;
    }
    
    if (chartContainer) {
        const chartWrapper = chartContainer.querySelector('.chart-wrapper');
        if (chartWrapper) {
            chartWrapper.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading chart...</p>
                </div>
            `;
        }
    }
}

// Hide loading state
function hideLoading() {
    console.log('Dashboard loaded successfully!');
}

// Initialize the dashboard
async function initDashboard() {
    console.log('🚀 Initializing dashboard...');
    showLoading();
    
    try {
        const data = await fetchDashboardData();
        updateDashboard(data);
    } catch (error) {
        console.error('Error in dashboard initialization:', error);
        const statsGrid = document.querySelector('.stats-grid');
        if (statsGrid) {
            statsGrid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ef4444; margin-bottom: 15px;"></i>
                    <p>Failed to load dashboard data</p>
                    <button onclick="initDashboard()" style="margin-top: 10px; padding: 8px 16px; background: #4361ee; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
        }
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up event listeners...');
    
    const reviewBtn = document.getElementById('review-applications');
    if (reviewBtn) {
        reviewBtn.addEventListener('click', function() {
            alert('📋 Redirecting to pending applications...');
        });
    }

    document.querySelectorAll('.quick-actions button').forEach(button => {
        button.addEventListener('click', function() {
            const actionText = this.textContent.trim();
            alert(`⚡ ${actionText} - This would navigate to the appropriate page.`);
        });
    });

    initDashboard();
});

// Auto-refresh every 30 seconds
setInterval(initDashboard, 30000);