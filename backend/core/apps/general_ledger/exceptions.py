"""
Custom exceptions for the General Ledger app.
Mirrors apps/gas/exceptions.py's granular hierarchy — no catch-all handling.
"""


class GeneralLedgerException(Exception):
    """Base exception for all general ledger operations."""


class GLPostingException(GeneralLedgerException):
    """Raised when a double-entry posting cannot be completed — an unbalanced
    set of lines, a missing/unknown GL account, or a non-positive amount.
    Always raised inside an atomic() block so the caller's transaction rolls
    back in full."""


class GLIntegrationException(GeneralLedgerException):
    """Raised when the Integration Transfer pipeline cannot proceed — most
    commonly a missing control-account mapping on GLIntegrationSettings.
    Individual source records with no confident natural GL pairing are
    skipped and logged by IntegrationTransferService rather than raising
    this — it is reserved for configuration/setup failures that block an
    entire transfer run."""
