"""
Custom exceptions for the Gas app (cylinder rental/deposit tracking).
Mirrors apps/pos/exceptions.py's granular hierarchy — no catch-all handling.
"""


class RentalException(Exception):
    """Base exception for all rental operations."""


class RentalStockException(RentalException):
    """Raised when stock-related rental operations fail (e.g. insufficient stock)."""


class RentalStateException(RentalException):
    """Raised when an operation violates rental lifecycle state rules
    (double-submit, double-return, no matching open rental)."""


class RentalLedgerException(RentalException):
    """Raised when posting a rental transaction to the general ledger fails.
    Always raised inside the checkout/return atomic() block so the caller's
    transaction rolls back stock, POS, and GL together."""
