/**
 * Client API GuinéeMarket
 * Gère toutes les communications avec le backend
 */
class ApiClient {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('access_token');
        this.refreshTokenValue = localStorage.getItem('refresh_token');
    }

    /**
     * Récupérer les headers avec authentification
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    /**
     * Requête GET
     */
    async get(endpoint, params = {}) {
        const queryString = Object.keys(params).length > 0 
            ? '?' + new URLSearchParams(params).toString() 
            : '';
        
        try {
            const response = await fetch(`${this.baseURL}${endpoint}${queryString}`, {
                method: 'GET',
                headers: this.getHeaders(),
            });

            if (response.status === 401) {
                return await this.handleTokenRefresh(() => this.get(endpoint, params));
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Erreur lors de la requête');
            }

            return await response.json();
        } catch (error) {
            console.error(`GET ${endpoint} error:`, error);
            throw error;
        }
    }

    /**
     * Requête POST
     */
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(data),
            });

            if (response.status === 401) {
                return await this.handleTokenRefresh(() => this.post(endpoint, data));
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Erreur lors de la requête');
            }

            return await response.json();
        } catch (error) {
            console.error(`POST ${endpoint} error:`, error);
            throw error;
        }
    }

    /**
     * Requête PUT
     */
    async put(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(data),
            });

            if (response.status === 401) {
                return await this.handleTokenRefresh(() => this.put(endpoint, data));
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Erreur lors de la requête');
            }

            return await response.json();
        } catch (error) {
            console.error(`PUT ${endpoint} error:`, error);
            throw error;
        }
    }

    /**
     * Requête DELETE
     */
    async delete(endpoint) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'DELETE',
                headers: this.getHeaders(),
            });

            if (response.status === 401) {
                return await this.handleTokenRefresh(() => this.delete(endpoint));
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Erreur lors de la requête');
            }

            return await response.json();
        } catch (error) {
            console.error(`DELETE ${endpoint} error:`, error);
            throw error;
        }
    }

    /**
     * Upload de fichier
     */
    async uploadFile(endpoint, formData) {
        try {
            const headers = {};
            if (this.token) {
                headers['Authorization'] = `Bearer ${this.token}`;
            }
            // Ne pas définir Content-Type, fetch le fait automatiquement avec boundary

            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: headers,
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Erreur lors de l\'upload');
            }

            return await response.json();
        } catch (error) {
            console.error(`UPLOAD ${endpoint} error:`, error);
            throw error;
        }
    }

    /**
     * Gérer le rafraîchissement du token
     */
    async handleTokenRefresh(retryCallback) {
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                this.logout();
                throw new Error('Session expirée');
            }

            const response = await fetch(`${this.baseURL}/auth/refresh-token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (response.ok) {
                const data = await response.json();
                this.setToken(data.access_token);
                return await retryCallback();
            } else {
                this.logout();
                throw new Error('Session expirée');
            }
        } catch (error) {
            this.logout();
            throw error;
        }
    }

    /**
     * Définir le token d'accès
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    /**
     * Définir le token de rafraîchissement
     */
    setRefreshToken(token) {
        this.refreshTokenValue = token;
        localStorage.setItem('refresh_token', token);
    }

    /**
     * Déconnexion
     */
    logout() {
        this.token = null;
        this.refreshTokenValue = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.location.href = '/auth/login';
    }

    /**
     * Vérifier si l'utilisateur est connecté
     */
    isAuthenticated() {
        return !!this.token;
    }
}

// Instance globale
const api = new ApiClient();