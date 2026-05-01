/**
 * Gestion du panier
 */
class CartManager {
    constructor() {
        this.cartKey = 'guinee_market_cart';
        this.cart = this.loadCart();
    }

    /**
     * Charger le panier depuis localStorage
     */
    loadCart() {
        const cartData = localStorage.getItem(this.cartKey);
        return cartData ? JSON.parse(cartData) : { items: [], total: 0 };
    }

    /**
     * Sauvegarder le panier
     */
    saveCart() {
        localStorage.setItem(this.cartKey, JSON.stringify(this.cart));
        this.updateCartUI();
    }

    /**
     * Ajouter un produit au panier
     */
    addToCart(product) {
        const existingItem = this.cart.items.find(item => item.product_id === product.id);
        
        if (existingItem) {
            existingItem.quantity += 1;
            this.showToast('Quantité mise à jour');
        } else {
            this.cart.items.push({
                product_id: product.id,
                title: product.title,
                price: product.price,
                image: product.images?.[0]?.url || '/static/images/placeholder/product.jpg',
                quantity: 1,
                seller_name: product.seller?.full_name || 'Vendeur',
                delivery_fee: product.delivery_fee || 0
            });
            this.showToast('Produit ajouté au panier');
        }
        
        this.recalculateTotal();
        this.saveCart();
    }

    /**
     * Supprimer un produit du panier
     */
    removeFromCart(productId) {
        this.cart.items = this.cart.items.filter(item => item.product_id !== productId);
        this.recalculateTotal();
        this.saveCart();
        this.showToast('Produit retiré du panier');
    }

    /**
     * Mettre à jour la quantité
     */
    updateQuantity(productId, quantity) {
        const item = this.cart.items.find(item => item.product_id === productId);
        
        if (item) {
            if (quantity <= 0) {
                this.removeFromCart(productId);
            } else {
                item.quantity = quantity;
                this.recalculateTotal();
                this.saveCart();
            }
        }
    }

    /**
     * Recalculer le total
     */
    recalculateTotal() {
        this.cart.total = this.cart.items.reduce((sum, item) => {
            return sum + (item.price * item.quantity) + item.delivery_fee;
        }, 0);
    }

    /**
     * Vider le panier
     */
    clearCart() {
        this.cart = { items: [], total: 0 };
        this.saveCart();
    }

    /**
     * Obtenir le nombre d'articles
     */
    getItemCount() {
        return this.cart.items.reduce((count, item) => count + item.quantity, 0);
    }

    /**
     * Obtenir le total
     */
    getTotal() {
        return this.cart.total;
    }

    /**
     * Mettre à jour l'UI du panier
     */
    updateCartUI() {
        const cartCount = document.getElementById('cartCount');
        if (cartCount) {
            const count = this.getItemCount();
            cartCount.textContent = count;
            cartCount.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    /**
     * Afficher un toast de notification
     */
    showToast(message) {
        // Créer un élément toast
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--gray-900);
            color: var(--white);
            padding: 12px 24px;
            border-radius: var(--radius-full);
            font-size: var(--font-size-sm);
            z-index: var(--z-toast);
            animation: slideUp 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideDown 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 2000);
    }

    /**
     * Créer une commande à partir du panier
     */
    async checkout() {
        if (this.cart.items.length === 0) {
            throw new Error('Votre panier est vide');
        }

        const orders = [];
        
        for (const item of this.cart.items) {
            try {
                const order = await api.post('/orders', {
                    product_id: item.product_id,
                    quantity: item.quantity,
                    payment_method: 'mobilepay'
                });
                orders.push(order);
            } catch (error) {
                console.error('Erreur création commande:', error);
                throw error;
            }
        }

        // Vider le panier après commande réussie
        this.clearCart();
        
        return orders;
    }
}

// Instance globale
const cart = new CartManager();