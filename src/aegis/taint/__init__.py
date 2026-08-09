"""
Aegis Dynamic Taint and Information Flow Tracking Subsystem.
"""

from aegis.taint.tracker import TaintTracker
from aegis.taint.rules import TaintSinkRule, DEFAULT_SINK_RULES

__all__ = ["TaintTracker", "TaintSinkRule", "DEFAULT_SINK_RULES"]
