/**
 * Gestion du suivi de commande
 */
class OrderTracker {
    constructor() {
        this.updateInterval = null;
    }

    /**
     * Démarrer le suivi en temps réel
     */
    startTracking(orderId, onUpdate) {
        // Première mise à jour immédiate
        this.fetchTracking(orderId, onUpdate);
        
        // Puis toutes les 30 secondes
        this.updateInterval = setInterval(() => {
            this.fetchTracking(orderId, onUpdate);
        }, 30000);
    }

    /**
     * Arrêter le suivi
     */
    stopTracking() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Récupérer les informations de suivi
     */
    async fetchTracking(orderId, onUpdate) {
        try {
            const tracking = await api.get(`/orders/${orderId}/tracking`);
            if (onUpdate) {
                onUpdate(tracking);
            }
            return tracking;
        } catch (error) {
            console.error('Erreur suivi commande:', error);
            return null;
        }
    }

    /**
     * Confirmer la livraison
     */
    async confirmDelivery(orderId, confirmationCode, rating = 5, review = '') {
        try {
            const result = await api.post(`/orders/${orderId}/confirm-delivery`, {
                order_id: orderId,
                confirmation_code: confirmationCode,
                rating: rating,
                review: review
            });
            
            if (result.success) {
                this.stopTracking();
                return {
                    success: true,
                    message: 'Livraison confirmée ! Le paiement a été libéré au vendeur.',
                    order: result.order
                };
            } else {
                return {
                    success: false,
                    message: result.message || 'Erreur de confirmation'
                };
            }
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Obtenir une icône pour le statut
     */
    getStatusIcon(status) {
        const icons = {
            'pending_payment': '💳',
            'payment_received': '✅',
            'processing': '🔧',
            'shipped': '🚚',
            'delivered': '📦',
            'completed': '🎉',
            'cancelled': '❌',
            'refunded': '↩️',
            'disputed': '⚠️'
        };
        return icons[status] || '📋';
    }

    /**
     * Obtenir une description pour le statut
     */
    getStatusDescription(status) {
        const descriptions = {
            'pending_payment': 'En attente de paiement',
            'payment_received': 'Paiement reçu - Commande en préparation',
            'processing': 'Le vendeur prépare votre commande',
            'shipped': 'Commande en cours de livraison',
            'delivered': 'Commande livrée - Veuillez confirmer la réception',
            'completed': 'Commande terminée - Paiement libéré au vendeur',
            'cancelled': 'Commande annulée',
            'refunded': 'Commande remboursée',
            'disputed': 'Litige en cours'
        };
        return descriptions[status] || 'Statut inconnu';
    }

    /**
     * Obtenir la couleur pour le statut
     */
    getStatusColor(status) {
        const colors = {
            'pending_payment': 'warning',
            'payment_received': 'info',
            'processing': 'info',
            'shipped': 'info',
            'delivered': 'success',
            'completed': 'success',
            'cancelled': 'danger',
            'refunded': 'danger',
            'disputed': 'warning'
        };
        return colors[status] || 'info';
    }
}

// Instance globale
const orderTracker = new OrderTracker();