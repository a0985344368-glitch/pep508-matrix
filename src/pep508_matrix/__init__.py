"""Static PEP 508 marker coverage observations for CI matrices."""

from .analyzer import analyze
from .models import AnalysisReport, Environment, MarkerObservation, Status

__all__ = ["AnalysisReport", "Environment", "MarkerObservation", "Status", "analyze"]
__version__ = "0.1.1"
