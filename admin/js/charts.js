/**
 * Graphiques du dashboard admin
 * Utilise Chart.js (à inclure dans le HTML)
 */
class Charts {
    static ordersChart = null;
    static revenueChart = null;
    
    static renderOrdersChart(data) {
        const ctx = document.getElementById('ordersChart');
        if (!ctx) return;
        
        if (this.ordersChart) {
            this.ordersChart.destroy();
        }
        
        this.ordersChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Commandes',
                    data: data.map(d => d.count),
                    borderColor: '#1a73e8',
                    backgroundColor: 'rgba(26, 115, 232, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    static renderRevenueChart(data) {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        
        if (this.revenueChart) {
            this.revenueChart.destroy();
        }
        
        this.revenueChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Revenus (GNF)',
                    data: data.map(d => d.total_commission || 0),
                    backgroundColor: '#0d904f'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}