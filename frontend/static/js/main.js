/**
 * Script principal - Fonctions communes
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialiser l'application
 */
function initializeApp() {
    updateAuthUI();
    updateCartCount();
    setupSearchListeners();
    setupMobileNavigation();
}

/**
 * Mettre à jour l'interface selon l'authentification
 */
function updateAuthUI() {
    const isAuthenticated = api.isAuthenticated();
    const userData = JSON.parse(localStorage.getItem('user_data') || 'null');
    
    const userMenu = document.getElementById('userMenu');
    const authButtons = document.getElementById('authButtons');
    const sellBtn = document.querySelector('.sell-btn');
    
    if (isAuthenticated && userData) {
        if (userMenu) userMenu.style.display = 'block';
        if (authButtons) authButtons.style.display = 'none';
        if (sellBtn) sellBtn.style.display = 'inline-flex';
        
        const userName = document.getElementById('userName');
        if (userName) {
            userName.textContent = userData.full_name?.split(' ')[0] || 'Mon compte';
        }
    } else {
        if (userMenu) userMenu.style.display = 'none';
        if (authButtons) authButtons.style.display = 'flex';
        if (sellBtn) sellBtn.style.display = 'none';
    }
}

/**
 * Mettre à jour le compteur du panier
 */
function updateCartCount() {
    const cartCount = document.getElementById('cartCount');
    if (cartCount) {
        const count = cart.getItemCount();
        cartCount.textContent = count;
        cartCount.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

/**
 * Configurer les écouteurs de recherche
 */
function setupSearchListeners() {
    const searchInput = document.getElementById('searchInput');
    const categorySelect = document.getElementById('categorySelect');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

/**
 * Effectuer une recherche
 */
function performSearch() {
    const query = document.getElementById('searchInput')?.value || '';
    const category = document.getElementById('categorySelect')?.value || '';
    
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (category) params.append('category', category);
    
    window.location.href = `/products/search?${params.toString()}`;
}

/**
 * Navigation mobile
 */
function setupMobileNavigation() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mobileNav = document.querySelector('.mobile-nav');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
            if (mobileNav) {
                mobileNav.classList.toggle('show');
            }
        });
    }
}

/**
 * Afficher/Masquer le dropdown utilisateur
 */
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

/**
 * Déconnexion
 */
function logout() {
    if (confirm('Voulez-vous vous déconnecter ?')) {
        api.logout();
        window.location.reload();
    }
}

/**
 * Formater une devise
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-GN', {
        style: 'currency',
        currency: 'GNF',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Formater une date
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Valider un numéro de téléphone guinéen
 */
function validateGuineaPhone(phone) {
    const clean = phone.replace(/[\s-]/g, '');
    return /^(\+224)?[67]\d{7}$/.test(clean);
}

/**
 * Normaliser un numéro de téléphone
 */
function normalizePhone(phone) {
    let clean = phone.replace(/[\s-]/g, '');
    if (!clean.startsWith('+224')) {
        clean = '+224' + clean;
    }
    return clean;
}

/**
 * Afficher un message d'erreur
 */
function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-error';
    toast.innerHTML = `
        <span>❌</span>
        <span>${message}</span>
    `;
    toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--danger);
        color: var(--white);
        padding: 12px 24px;
        border-radius: var(--radius-md);
        font-size: var(--font-size-sm);
        z-index: var(--z-toast);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        animation: slideUp 0.3s ease;
        max-width: 90%;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

/**
 * Afficher un message de succès
 */
function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-success';
    toast.innerHTML = `
        <span>✅</span>
        <span>${message}</span>
    `;
    toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--success);
        color: var(--white);
        padding: 12px 24px;
        border-radius: var(--radius-md);
        font-size: var(--font-size-sm);
        z-index: var(--z-toast);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        animation: slideUp 0.3s ease;
        max-width: 90%;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

/**
 * Créer une carte produit
 */
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
        <a href="/products/${product.id}">
            <img src="${product.images?.[0]?.url || '/static/images/placeholder/product.jpg'}" 
                 alt="${product.title}" 
                 class="product-image"
                 loading="lazy">
            <div class="product-info">
                <h3 class="product-title">${product.title}</h3>
                <div class="product-price">${formatCurrency(product.price)}</div>
                <div class="product-meta">
                    <span class="product-city">
                        📍 ${product.city}
                    </span>
                    <span>${formatDate(product.created_at)}</span>
                </div>
            </div>
        </a>
    `;
    return card;
}

// Animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes slideDown {
        from { opacity: 1; transform: translateX(-50%) translateY(0); }
        to { opacity: 0; transform: translateX(-50%) translateY(20px); }
    }
`;
document.head.appendChild(style);

// Fermer les dropdowns en cliquant ailleurs
document.addEventListener('click', function(event) {
    const userDropdown = document.getElementById('userDropdown');
    const userBtn = document.querySelector('.user-btn');
    
    if (userDropdown && userDropdown.classList.contains('show')) {
        if (!event.target.closest('.user-menu')) {
            userDropdown.classList.remove('show');
        }
    }
});