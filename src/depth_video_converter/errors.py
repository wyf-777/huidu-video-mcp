"""Public domain exceptions with safe user-facing messages."""


class ConversionError(RuntimeError):
    """Base class for expected conversion failures."""


class InvalidOptionsError(ConversionError):
    """Raised when a caller provides unsupported conversion options."""


class InputVideoError(ConversionError):
    """Raised when the input video cannot be decoded or inspected."""


class OutputVideoError(ConversionError):
    """Raised when a valid output video cannot be written."""
