# API GuinéeMarket

## Authentification

### POST /api/auth/register
Inscription utilisateur

### POST /api/auth/login
Connexion et obtention des tokens JWT

### POST /api/auth/verify-phone
Vérification du numéro de téléphone

## Produits

### GET /api/products
Liste des produits avec filtres et pagination

### POST /api/products
Créer une annonce (authentifié)

### GET /api/products/{id}
Détails d'un produit

## Commandes

### POST /api/orders
Créer une commande

### GET /api/orders/{id}
Détails d'une commande

### PUT /api/orders/{id}/status
Mettre à jour le statut (marchand)

### POST /api/orders/{id}/confirm-delivery
**CRITIQUE**: Confirmation livraison → Libération paiement

## Paiements MobilePay

### POST /api/payments/initiate
Initier un paiement MobilePay

### POST /api/payments/verify
Vérifier un paiement

### POST /api/payments/{order_id}/release
Libérer le paiement au marchand

## Webhooks

### POST /api/webhooks/mobilepay
Callback MobilePay pour notifications automatiques