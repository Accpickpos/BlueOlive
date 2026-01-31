"""
Thread-safe transaction number generator service
"""
import threading
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NumberGenerator:
    """Thread-safe transaction number generator"""
    
    def __init__(self):
        """Initialize the number generator"""
        self.counters: Dict[str, int] = {}
        self.prefixes: Dict[str, str] = {}
        self.lock = threading.RLock()
        
        # Default prefixes
        self.set_prefix("invoice", "INV")
        self.set_prefix("cash_sale", "REC")
        self.set_prefix("credit_note", "CN")
        self.set_prefix("receipt", "RCPT")
        self.set_prefix("laybye", "LAY")
        self.set_prefix("quotation", "QT")
        self.set_prefix("job_costing", "JOB")
        self.set_prefix("repair", "REP")
        self.set_prefix("payout", "PAY")
        self.set_prefix("cash_control", "CC")
    
    def set_prefix(self, transaction_type: str, prefix: str):
        """Set prefix for transaction type"""
        with self.lock:
            self.prefixes[transaction_type] = prefix
            if transaction_type not in self.counters:
                self.counters[transaction_type] = 0
    
    def get_prefix(self, transaction_type: str) -> str:
        """Get prefix for transaction type"""
        return self.prefixes.get(transaction_type, transaction_type.upper()[:3])
    
    def reset_counter(self, transaction_type: str):
        """Reset counter for transaction type"""
        with self.lock:
            if transaction_type in self.counters:
                self.counters[transaction_type] = 0
    
    def reset_all_counters(self):
        """Reset all counters"""
        with self.lock:
            for key in self.counters:
                self.counters[key] = 0
    
    def generate_number(
        self,
        transaction_type: str,
        prefix_override: Optional[str] = None,
        suffix: Optional[str] = None
    ) -> str:
        """
        Generate next transaction number
        
        Args:
            transaction_type: Type of transaction (invoice, cash_sale, etc.)
            prefix_override: Optional override for prefix
            suffix: Optional suffix (e.g., date string)
        
        Returns:
            Next transaction number in format: PREFIX-YYYYMMDD-######
        """
        with self.lock:
            # Get prefix
            prefix = prefix_override or self.get_prefix(transaction_type)
            
            # Initialize counter if needed
            if transaction_type not in self.counters:
                self.counters[transaction_type] = 0
            
            # Increment counter
            self.counters[transaction_type] += 1
            counter = self.counters[transaction_type]
            
            # Get date suffix if not provided
            if suffix is None:
                suffix = datetime.utcnow().strftime("%Y%m%d")
            
            # Format: PREFIX-YYYYMMDD-######
            transaction_number = f"{prefix}-{suffix}-{counter:06d}"
            
            logger.info(f"Generated {transaction_type} number: {transaction_number}")
            return transaction_number
    
    def generate_number_simple(
        self,
        transaction_type: str,
        prefix_override: Optional[str] = None
    ) -> str:
        """
        Generate simple transaction number without date
        
        Format: PREFIX-######
        """
        with self.lock:
            # Get prefix
            prefix = prefix_override or self.get_prefix(transaction_type)
            
            # Initialize counter if needed
            if transaction_type not in self.counters:
                self.counters[transaction_type] = 0
            
            # Increment counter
            self.counters[transaction_type] += 1
            counter = self.counters[transaction_type]
            
            # Format: PREFIX-######
            transaction_number = f"{prefix}-{counter:06d}"
            
            logger.info(f"Generated {transaction_type} number: {transaction_number}")
            return transaction_number
    
    def get_next_number(self, transaction_type: str) -> int:
        """Get next number without generating (for preview)"""
        with self.lock:
            if transaction_type not in self.counters:
                return 1
            return self.counters[transaction_type] + 1
    
    def get_current_counter(self, transaction_type: str) -> int:
        """Get current counter value"""
        with self.lock:
            return self.counters.get(transaction_type, 0)


# Global instance
_generator = None


def get_generator() -> NumberGenerator:
    """Get or create global number generator instance"""
    global _generator
    if _generator is None:
        _generator = NumberGenerator()
    return _generator


# Async wrapper functions
async def generate_transaction_number(
    transaction_type: str,
    prefix_override: Optional[str] = None,
    suffix: Optional[str] = None
) -> str:
    """Async wrapper for generating transaction number"""
    generator = get_generator()
    return generator.generate_number(transaction_type, prefix_override, suffix)


async def generate_simple_number(
    transaction_type: str,
    prefix_override: Optional[str] = None
) -> str:
    """Async wrapper for generating simple transaction number"""
    generator = get_generator()
    return generator.generate_number_simple(transaction_type, prefix_override)
