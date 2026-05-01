/**
 * Service Worker GuinéeMarket
 * Pour le support PWA et le cache offline
 */
const CACHE_NAME = 'guinee-market-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/theme.css',
    '/static/css/main.css',
    '/static/css/responsive.css',
    '/static/js/main.js',
    '/static/js/api.js',
    '/static/js/utils.js',
    '/static/images/logo.svg',
    '/static/images/placeholder/product.jpg',
    '/offline.html'
];

// Installation du Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker: Installation');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Mise en cache des assets');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => {
                return self.skipWaiting();
            })
    );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker: Activation');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Suppression ancien cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// Stratégie de cache: Network First, puis cache
self.addEventListener('fetch', event => {
    // Ignorer les requêtes API
    if (event.request.url.includes('/api/')) {
        return;
    }
    
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Mettre en cache les réponses réussies
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, responseClone);
                        });
                }
                return response;
            })
            .catch(() => {
                // Si le réseau échoue, servir depuis le cache
                return caches.match(event.request)
                    .then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // Si pas en cache, montrer la page offline
                        if (event.request.mode === 'navigate') {
                            return caches.match('/offline.html');
                        }
                        return new Response('', {
                            status: 408,
                            statusText: 'Pas de connexion'
                        });
                    });
            })
    );
});

// Gestion des notifications push
self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    
    const options = {
        body: data.message || 'Nouvelle notification',
        icon: '/static/images/icons/icon-192x192.png',
        badge: '/static/images/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/',
            orderId: data.order_id
        },
        actions: [
            {
                action: 'open',
                title: 'Voir'
            },
            {
                action: 'close',
                title: 'Fermer'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(
            data.title || 'GuinéeMarket',
            options
        )
    );
});

// Gestion du clic sur une notification
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(windowClients => {
            // Ouvrir une fenêtre existante si possible
            for (const client of windowClients) {
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // Sinon, ouvrir une nouvelle fenêtre
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Synchronisation en arrière-plan
self.addEventListener('sync', event => {
    if (event.tag === 'sync-pending-orders') {
        event.waitUntil(syncPendingOrders());
    }
});

async function syncPendingOrders() {
    try {
        const cache = await caches.open('pending-orders');
        const requests = await cache.keys();
        
        for (const request of requests) {
            try {
                await fetch(request);
                await cache.delete(request);
            } catch (error) {
                console.log('Échec synchronisation:', error);
            }
        }
    } catch (error) {
        console.error('Erreur sync:', error);
    }
}