/**
 * Gestion des paiements MobilePay
 */
class PaymentManager {
    constructor() {
        this.currentPayment = null;
        this.pollingInterval = null;
        this.paymentTimeout = null;
    }

    /**
     * Initier un paiement MobilePay
     */
    async initiatePayment(orderId, phoneNumber) {
        try {
            const response = await api.post('/payments/initiate', {
                order_id: orderId,
                phone_number: phoneNumber,
                payment_method: 'mobilepay'
            });

            this.currentPayment = response;
            return response;
        } catch (error) {
            throw new Error('Échec de l\'initiation du paiement: ' + error.message);
        }
    }

    /**
     * Vérifier le statut d'un paiement
     */
    async checkPaymentStatus(paymentReference) {
        try {
            const status = await api.get(`/payments/${paymentReference}/status`);
            return status;
        } catch (error) {
            throw new Error('Erreur de vérification: ' + error.message);
        }
    }

    /**
     * Vérifier une transaction MobilePay
     */
    async verifyTransaction(paymentReference, transactionId) {
        try {
            const result = await api.post('/payments/verify', {
                payment_reference: paymentReference,
                transaction_id: transactionId
            });
            return result;
        } catch (error) {
            throw new Error('Échec de la vérification: ' + error.message);
        }
    }

    /**
     * Démarrer le polling de vérification automatique
     */
    startPolling(paymentReference, onSuccess, onFailure, timeoutSeconds = 300) {
        let attempts = 0;
        const maxAttempts = timeoutSeconds / 5; // Vérifier toutes les 5 secondes

        this.pollingInterval = setInterval(async () => {
            attempts++;
            
            if (attempts > maxAttempts) {
                this.stopPolling();
                if (onFailure) onFailure('Délai de paiement expiré');
                return;
            }

            try {
                const status = await this.checkPaymentStatus(paymentReference);
                
                if (status === 'COMPLETED' || status.status === 'COMPLETED') {
                    this.stopPolling();
                    if (onSuccess) onSuccess(status);
                } else if (status === 'FAILED' || status.status === 'FAILED') {
                    this.stopPolling();
                    if (onFailure) onFailure('Paiement échoué');
                }
            } catch (error) {
                // Continuer le polling malgré les erreurs temporaires
                console.warn('Erreur polling:', error);
            }
        }, 5000);

        // Timeout global
        this.paymentTimeout = setTimeout(() => {
            this.stopPolling();
            if (onFailure) onFailure('Timeout de paiement');
        }, timeoutSeconds * 1000);
    }

    /**
     * Arrêter le polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        if (this.paymentTimeout) {
            clearTimeout(this.paymentTimeout);
            this.paymentTimeout = null;
        }
    }

    /**
     * Calculer le montant de la commission
     */
    async getCommission(amount, category = null) {
        const response = await api.get('/payments/commission', {
            amount: amount,
            category: category
        });
        return response;
    }
}

// Instance globale
const paymentManager = new PaymentManager();