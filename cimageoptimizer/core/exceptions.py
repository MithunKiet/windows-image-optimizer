"""Exceptions raised by the optimization pipeline."""


class OptimizationError(Exception):
    """Base exception for optimization failures."""


class ImageProcessingError(OptimizationError):
    """Raised when an individual image cannot be read, transformed, or saved."""
