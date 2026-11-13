"""
Thin eBay publishing stub. Replace placeholders with real eBay API calls.
"""
import logging
import secrets
import base64
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


@dataclass
class EbayCredentials:
    client_id: str
    client_secret: str
    refresh_token: str
    environment: str = "sandbox"  # or "production"


@dataclass
class PublishResult:
    success: bool
    listing_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class EbayOrder:
    order_id: str
    buyer_id: str
    total: float
    status: str


def generate_oauth_url(client_id: str, redirect_uri: str, environment: str = "sandbox") -> tuple[str, str]:
    """
    Generates eBay OAuth authorization URL and state token.
    Returns: (auth_url, state)
    """
    state = secrets.token_urlsafe(32)
    base_url = (
        "https://auth.ebay.com/oauth2/authorize"
        if environment == "production"
        else "https://auth.sandbox.ebay.com/oauth2/authorize"
    )
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory",
        "state": state,
    }
    auth_url = f"{base_url}?{urlencode(params)}"
    return auth_url, state


def exchange_code_for_token(client_id: str, client_secret: str, code: str, redirect_uri: str, environment: str = "sandbox") -> Optional[dict]:
    """
    Exchanges authorization code for access/refresh tokens.
    In production, this would call eBay's token endpoint.
    Currently returns stub tokens.
    """
    try:
        logger.info("Exchanging OAuth code for tokens (stub)")
        # TODO: Implement real POST to https://api.ebay.com/identity/v1/oauth2/token
        # with Basic Auth header: base64(client_id:client_secret)
        # body: grant_type=authorization_code&code={code}&redirect_uri={redirect_uri}
        
        # Stub response
        return {
            "access_token": f"stub_access_{secrets.token_urlsafe(16)}",
            "refresh_token": f"stub_refresh_{secrets.token_urlsafe(16)}",
            "expires_in": 7200,
            "token_type": "Bearer",
        }
    except Exception as exc:
        logger.exception("Failed to exchange OAuth code")
        return None


def publish_product(product, images: List[str], creds: EbayCredentials) -> PublishResult:
    """
    Publishes a product to eBay. Currently a stub returning success.
    Replace with real eBay Inventory/Trading API calls.
    """
    try:
        logger.info("Publishing product %s to eBay (%s)", product.title, creds.environment)
        # TODO: Implement OAuth, image upload, and inventory/create requests.
        fake_listing_id = f"EBAY-{product.id}"
        return PublishResult(success=True, listing_id=fake_listing_id)
    except Exception as exc:  # pragma: no cover - stub
        logger.exception("Failed to publish to eBay")
        return PublishResult(success=False, error=str(exc))


def fetch_orders(creds: EbayCredentials) -> List[EbayOrder]:
    """
    Fetches orders from eBay. Stub returning fake data.
    Replace with real eBay Fulfillment API calls.
    """
    try:
        logger.info("Fetching orders from eBay (%s)", creds.environment)
        # TODO: Implement OAuth + fulfillment/order API
        return [
            EbayOrder(order_id="EBAY-ORD-001", buyer_id="buyer123", total=49.99, status="pending"),
            EbayOrder(order_id="EBAY-ORD-002", buyer_id="buyer456", total=99.50, status="processing"),
        ]
    except Exception as exc:
        logger.exception("Failed to fetch orders from eBay")
        return []
