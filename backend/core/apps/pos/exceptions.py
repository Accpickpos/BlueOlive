"""
Custom exceptions for POS app.
Provides granular error handling for POS operations.
"""


class POSException(Exception):
    """Base exception for all POS operations."""
    pass


class POSValidationException(POSException):
    """Raised when validation fails."""
    pass


class POSStateException(POSException):
    """Raised when operation violates document state rules."""
    pass


class POSStockException(POSException):
    """Raised when stock-related operations fail."""
    pass


class POSPaymentException(POSException):
    """Raised when payment processing fails."""
    pass


class POSCalculationException(POSException):
    """Raised when calculations fail."""
    pass


class InvalidDocumentState(POSStateException):
    """Raised when document is in invalid state for operation."""
    
    def __init__(self, document_type: str, document_number: str, 
                 current_status: str, operation: str):
        self.document_type = document_type
        self.document_number = document_number
        self.current_status = current_status
        self.operation = operation
        message = (
            f"Cannot {operation} {document_type} {document_number}: "
            f"current status is {current_status}"
        )
        super().__init__(message)


class InsufficientStock(POSStockException):
    """Raised when stock is insufficient."""
    
    def __init__(self, stock_code: str, required: float, available: float):
        self.stock_code = stock_code
        self.required = required
        self.available = available
        message = (
            f"Insufficient stock for {stock_code}: "
            f"required {required}, available {available}"
        )
        super().__init__(message)


class PaymentImbalance(POSPaymentException):
    """Raised when tender amounts don't match total."""
    
    def __init__(self, tender_total: float, transaction_total: float):
        self.tender_total = tender_total
        self.transaction_total = transaction_total
        self.balance = abs(tender_total - transaction_total)
        message = (
            f"Payment imbalance: tendered {tender_total}, "
            f"total {transaction_total}, difference {self.balance}"
        )
        super().__init__(message)


class DuplicateTransaction(POSValidationException):
    """Raised when duplicate transaction detected."""
    
    def __init__(self, document_type: str, transaction_number: str):
        self.document_type = document_type
        self.transaction_number = transaction_number
        message = (
            f"Duplicate {document_type}: {transaction_number} already exists"
        )
        super().__init__(message)
