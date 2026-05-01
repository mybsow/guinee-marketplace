"""
Rate Limiter pour protéger l'API
"""
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time
from collections import defaultdict
from loguru import logger

class RateLimiter:
    def __init__(self, requests: int = 100, window: int = 60):
        """
        Args:
            requests: Nombre maximum de requêtes
            window: Fenêtre de temps en secondes
        """
        self.requests = requests
        self.window = window
        self.clients: Dict[str, list] = defaultdict(list)
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        """
        Vérifier si un client est limité
        
        Returns:
            Tuple (is_limited, remaining_requests)
        """
        now = time.time()
        window_start = now - self.window
        
        # Nettoyer les anciennes requêtes
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if req_time > window_start
        ]
        
        # Vérifier la limite
        current_requests = len(self.clients[client_id])
        
        if current_requests >= self.requests:
            return True, 0
        
        # Ajouter la requête courante
        self.clients[client_id].append(now)
        
        return False, self.requests - current_requests - 1

# Rate limiters spécifiques
api_limiter = RateLimiter(requests=100, window=60)  # 100 req/min
auth_limiter = RateLimiter(requests=10, window=60)   # 10 tentatives/min
payment_limiter = RateLimiter(requests=5, window=60) # 5 paiements/min

async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting global"""
    client_ip = request.client.host
    
    is_limited, remaining = api_limiter.is_rate_limited(client_ip)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de requêtes. Veuillez réessayer plus tard.",
            headers={"Retry-After": "60"}
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response