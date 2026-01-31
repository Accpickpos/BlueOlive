"""
Service for integrating with Django REST Framework backend
"""
import httpx
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime
from config import get_settings
import asyncio
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class DRFIntegrationService:
    """Service for interacting with Django REST Framework backend"""
    
    def __init__(self):
        self.base_url = settings.drf_base_url
        self.timeout = settings.drf_timeout
        self._client = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # Debtor operations
    async def get_debtor(self, debtor_account_number: str) -> Optional[Dict[str, Any]]:
        """Get debtor information from DRF backend"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/debtors/{debtor_account_number}/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Debtor {debtor_account_number} not found")
                return None
            else:
                logger.error(f"Error fetching debtor: {response.status_code}")
                return None
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    async def get_debtor_balance(self, debtor_account_number: str) -> Optional[Decimal]:
        """Get debtor account balance"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/debtors/{debtor_account_number}/balance/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data.get('balance', 0)))
            return None
        except (httpx.RequestError, ValueError) as e:
            logger.error(f"Error fetching debtor balance: {str(e)}")
            return None
    
    async def post_transaction_to_debtor(
        self, 
        debtor_account_number: str, 
        amount: Decimal, 
        transaction_type: str,
        reference: str,
        description: Optional[str] = None
    ) -> bool:
        """Post transaction to debtor account"""
        try:
            client = await self.get_client()
            payload = {
                "amount": float(amount),
                "transaction_type": transaction_type,
                "reference": reference,
                "description": description or "",
                "date": datetime.utcnow().isoformat()
            }
            response = await client.post(
                f"{self.base_url}/debtors/{debtor_account_number}/transactions/",
                json=payload,
                headers={"Accept": "application/json"}
            )
            if response.status_code in [200, 201]:
                return True
            else:
                logger.error(f"Error posting to debtor: {response.status_code} - {response.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return False
    
    # Stock operations
    async def get_stock_item(self, item_code: str) -> Optional[Dict[str, Any]]:
        """Get stock item information"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/stock/{item_code}/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Stock item {item_code} not found")
                return None
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    async def get_stock_quantity(self, item_code: str) -> Optional[Decimal]:
        """Get available stock quantity"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/stock/{item_code}/quantity/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data.get('available_quantity', 0)))
            return None
        except (httpx.RequestError, ValueError) as e:
            logger.error(f"Error fetching stock quantity: {str(e)}")
            return None
    
    async def update_stock_quantity(
        self, 
        item_code: str, 
        quantity_delta: Decimal,
        transaction_reference: str,
        transaction_type: str
    ) -> bool:
        """Update stock quantity"""
        try:
            client = await self.get_client()
            payload = {
                "quantity_delta": float(quantity_delta),
                "transaction_reference": transaction_reference,
                "transaction_type": transaction_type,
                "date": datetime.utcnow().isoformat()
            }
            response = await client.patch(
                f"{self.base_url}/stock/{item_code}/quantity/",
                json=payload,
                headers={"Accept": "application/json"}
            )
            if response.status_code in [200, 204]:
                return True
            else:
                logger.error(f"Error updating stock: {response.status_code} - {response.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return False
    
    # Creditor operations
    async def get_creditor(self, creditor_account_number: str) -> Optional[Dict[str, Any]]:
        """Get creditor information"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/creditors/{creditor_account_number}/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    # Cashbook operations
    async def post_cashbook_entry(
        self,
        amount: Decimal,
        entry_type: str,
        description: str,
        reference: str
    ) -> bool:
        """Post entry to cashbook"""
        try:
            client = await self.get_client()
            payload = {
                "amount": float(amount),
                "entry_type": entry_type,
                "description": description,
                "reference": reference,
                "date": datetime.utcnow().isoformat()
            }
            response = await client.post(
                f"{self.base_url}/cashbook/entries/",
                json=payload,
                headers={"Accept": "application/json"}
            )
            return response.status_code in [200, 201]
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return False
    
    # Purchase order operations
    async def get_purchase_order(self, po_number: str) -> Optional[Dict[str, Any]]:
        """Get purchase order information"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/purchase-orders/{po_number}/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    # Configuration
    async def get_system_config(self, key: str) -> Optional[Any]:
        """Get system configuration value"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/config/{key}/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('value')
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    async def get_tax_rate(self, tax_code: str) -> Optional[Decimal]:
        """Get tax rate for tax code"""
        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.base_url}/tax-rates/{tax_code}/",
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data.get('rate', 0)))
            return Decimal("0")
        except (httpx.RequestError, ValueError) as e:
            logger.error(f"Request error: {str(e)}")
            return Decimal("0")
    
    # Search operations
    async def search_debtors(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search debtors by account number or name"""
        try:
            client = await self.get_client()
            params = {
                "search": query,
                "limit": limit
            }
            response = await client.get(
                f"{self.base_url}/debtors/search/",
                params=params,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json() or []
            else:
                logger.warning(f"Debtor search returned {response.status_code}")
                return []
        except httpx.RequestError as e:
            logger.error(f"Request error during debtor search: {str(e)}")
            return []
    
    async def search_stock(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search stock items by code or description"""
        try:
            client = await self.get_client()
            params = {
                "search": query,
                "limit": limit
            }
            response = await client.get(
                f"{self.base_url}/stock/search/",
                params=params,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json() or []
            else:
                logger.warning(f"Stock search returned {response.status_code}")
                return []
        except httpx.RequestError as e:
            logger.error(f"Request error during stock search: {str(e)}")
            return []
    
    async def search_creditors(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search creditors by account number or name"""
        try:
            client = await self.get_client()
            params = {
                "search": query,
                "limit": limit
            }
            response = await client.get(
                f"{self.base_url}/creditors/search/",
                params=params,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                return response.json() or []
            else:
                logger.warning(f"Creditor search returned {response.status_code}")
                return []
        except httpx.RequestError as e:
            logger.error(f"Request error during creditor search: {str(e)}")
            return []
