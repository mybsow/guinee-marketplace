/**
 * Admin Dashboard JavaScript
 */
class AdminPanel {
    constructor() {
        this.currentPage = 'dashboard';
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.updateClock();
        this.loadDashboard();
        
        // Actualiser l'horloge
        setInterval(() => this.updateClock(), 1000);
    }
    
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });
    }
    
    navigateTo(page) {
        this.currentPage = page;
        
        // Mettre à jour la navigation active
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        
        // Mettre à jour le titre
        const titles = {
            dashboard: 'Tableau de bord',
            users: 'Gestion des utilisateurs',
            products: 'Modération des produits',
            transactions: 'Transactions',
            commissions: 'Commissions',
            payouts: 'Payouts',
            reports: 'Rapports'
        };
        document.getElementById('pageTitle').textContent = titles[page] || page;
        
        // Charger la page
        switch(page) {
            case 'dashboard': this.loadDashboard(); break;
            case 'users': this.loadUsers(); break;
            case 'products': this.loadProducts(); break;
            case 'transactions': this.loadTransactions(); break;
            case 'commissions': this.loadCommissions(); break;
            case 'payouts': this.loadPayouts(); break;
            case 'reports': this.loadReports(); break;
        }
    }
    
    updateClock() {
        const now = new Date();
        document.getElementById('currentTime').textContent = 
            now.toLocaleString('fr-FR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
    }
    
    async loadDashboard() {
        try {
            const stats = await api.get('/admin/dashboard');
            this.renderDashboardStats(stats);
            this.renderCharts(stats.charts);
        } catch (error) {
            console.error('Erreur chargement dashboard:', error);
            this.showError('Impossible de charger le tableau de bord');
        }
    }
    
    renderDashboardStats(stats) {
        const container = document.getElementById('dashboardStats');
        if (!container) return;
        
        container.innerHTML = `
            <div class="stat-card">
                <h3>Utilisateurs</h3>
                <div class="stat-value">${stats.users.total}</div>
                <div class="stat-change">+${stats.users.new_this_month} ce mois</div>
            </div>
            <div class="stat-card">
                <h3>Produits actifs</h3>
                <div class="stat-value">${stats.products.active}</div>
                <div class="stat-change">+${stats.products.new_this_month} ce mois</div>
            </div>
            <div class="stat-card">
                <h3>Commandes</h3>
                <div class="stat-value">${stats.orders.total}</div>
                <div class="stat-change">${stats.orders.conversion_rate}% de conversion</div>
            </div>
            <div class="stat-card">
                <h3>Revenus plateforme</h3>
                <div class="stat-value">${this.formatCurrency(stats.finance.total_commissions)}</div>
                <div class="stat-change">${this.formatCurrency(stats.finance.revenue_this_month)} ce mois</div>
            </div>
            <div class="stat-card">
                <h3>Paiements traités</h3>
                <div class="stat-value">${this.formatCurrency(stats.finance.total_payments)}</div>
                <div class="stat-change">${this.formatCurrency(stats.finance.recent_payments)} (30j)</div>
            </div>
            <div class="stat-card">
                <h3>Payouts en attente</h3>
                <div class="stat-value">${this.formatCurrency(stats.finance.pending_payouts)}</div>
                <div class="stat-change negative">Nécessite attention</div>
            </div>
        `;
    }
    
    renderCharts(charts) {
        if (window.Charts) {
            Charts.renderOrdersChart(charts.orders_per_day);
        }
    }
    
    async loadUsers(page = 1) {
        try {
            const data = await api.get(`/admin/users`, { page, limit: 20 });
            this.renderUsersTable(data);
        } catch (error) {
            console.error('Erreur chargement utilisateurs:', error);
        }
    }
    
    renderUsersTable(data) {
        const content = document.getElementById('adminContent');
        
        let tableHTML = `
            <div class="data-table">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nom</th>
                            <th>Téléphone</th>
                            <th>Rôle</th>
                            <th>Vérifié</th>
                            <th>Statut</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.users.forEach(user => {
            tableHTML += `
                <tr>
                    <td>#${user.id}</td>
                    <td>${user.full_name}</td>
                    <td>${user.phone_number}</td>
                    <td><span class="badge badge-info">${user.role}</span></td>
                    <td>${user.is_verified ? '✅' : '❌'}</td>
                    <td>${user.is_active ? 
                        '<span class="badge badge-success">Actif</span>' : 
                        '<span class="badge badge-danger">Inactif</span>'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="admin.toggleUser(${user.id})">
                            ${user.is_active ? 'Désactiver' : 'Activer'}
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table></div>';
        
        // Pagination
        tableHTML += this.renderPagination(data);
        
        content.innerHTML = tableHTML;
    }
    
    renderPagination(data) {
        const totalPages = Math.ceil(data.total / data.limit);
        let paginationHTML = '<div class="pagination">';
        
        for (let i = 1; i <= totalPages; i++) {
            paginationHTML += `
                <button class="${i === data.page ? 'active' : ''}" 
                        onclick="admin.loadUsers(${i})">
                    ${i}
                </button>
            `;
        }
        
        paginationHTML += '</div>';
        return paginationHTML;
    }
    
    async toggleUser(userId) {
        try {
            const result = await api.put(`/admin/users/${userId}/toggle-status`);
            alert(result.message);
            this.loadUsers();
        } catch (error) {
            alert('Erreur: ' + error.message);
        }
    }
    
    async loadProducts() {
        try {
            const data = await api.get('/admin/products/moderation');
            this.renderProductsTable(data);
        } catch (error) {
            console.error('Erreur chargement produits:', error);
        }
    }
    
    renderProductsTable(data) {
        const content = document.getElementById('adminContent');
        
        let html = `
            <div class="data-table">
                <h3>Produits en attente de modération</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Titre</th>
                            <th>Prix</th>
                            <th>Vendeur</th>
                            <th>Statut</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.products.forEach(product => {
            html += `
                <tr>
                    <td>#${product.id}</td>
                    <td>${product.title}</td>
                    <td>${this.formatCurrency(product.price)}</td>
                    <td>${product.seller_name}</td>
                    <td><span class="badge badge-warning">${product.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="admin.moderateProduct(${product.id}, 'approve')">
                            ✅ Approuver
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="admin.moderateProduct(${product.id}, 'reject')">
                            ❌ Rejeter
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        content.innerHTML = html;
    }
    
    async moderateProduct(productId, action) {
        try {
            const result = await api.put(`/admin/products/${productId}/moderate?action=${action}`);
            alert(result.message);
            this.loadProducts();
        } catch (error) {
            alert('Erreur: ' + error.message);
        }
    }
    
    async loadTransactions() {
        try {
            const data = await api.get('/admin/transactions');
            this.renderTransactionsTable(data);
        } catch (error) {
            console.error('Erreur chargement transactions:', error);
        }
    }
    
    renderTransactionsTable(data) {
        const content = document.getElementById('adminContent');
        
        let html = `
            <h2>Volume total: ${this.formatCurrency(data.total_volume)}</h2>
            <div class="data-table">
                <table>
                    <thead>
                        <tr>
                            <th>Référence</th>
                            <th>Type</th>
                            <th>Montant</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.transactions.forEach(tx => {
            html += `
                <tr>
                    <td>${tx.reference}</td>
                    <td><span class="badge badge-info">${tx.type}</span></td>
                    <td>${this.formatCurrency(tx.amount)}</td>
                    <td>${new Date(tx.created_at).toLocaleString('fr-FR')}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        content.innerHTML = html;
    }
    
    async loadPayouts() {
        try {
            const data = await api.get('/admin/payouts/pending');
            const content = document.getElementById('adminContent');
            
            content.innerHTML = `
                <h2>Payouts en attente: ${this.formatCurrency(data.total_pending_amount)}</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>En attente</h3>
                        <div class="stat-value">${data.pending.length}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Échoués</h3>
                        <div class="stat-value" style="color: red;">${data.failed.length}</div>
                    </div>
                </div>
                <div class="data-table">
                    <h3>Payouts en attente</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Référence</th>
                                <th>Montant</th>
                                <th>Marchand</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.pending.map(p => `
                                <tr>
                                    <td>${p.reference}</td>
                                    <td>${this.formatCurrency(p.amount)}</td>
                                    <td>${p.merchant_phone}</td>
                                    <td>${new Date(p.created_at).toLocaleString('fr-FR')}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            console.error('Erreur chargement payouts:', error);
        }
    }
    
    async loadCommissions() {
        try {
            const data = await api.get('/admin/commissions');
            const content = document.getElementById('adminContent');
            
            content.innerHTML = `
                <h2>Total commissions: ${this.formatCurrency(data.total_commission)}</h2>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Commission</th>
                                <th>Transactions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.daily_breakdown.map(d => `
                                <tr>
                                    <td>${d.date}</td>
                                    <td>${this.formatCurrency(d.commission)}</td>
                                    <td>${d.transactions}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            console.error('Erreur chargement commissions:', error);
        }
    }
    
    loadReports() {
        const content = document.getElementById('adminContent');
        content.innerHTML = `
            <h2>Rapports</h2>
            <p>Fonctionnalité à venir...</p>
        `;
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-GN', {
            style: 'currency',
            currency: 'GNF',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }
    
    showError(message) {
        alert(message);
    }
}

// Instance globale
const admin = new AdminPanel();