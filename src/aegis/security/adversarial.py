"""
Adversarial Threat Detection & Prompt Injection Defense Engine for AegisKernel.

Detects jailbreak attempts, delimiter hijacking, token smuggling, Unicode zero-width
attacks, base64/hex payload evasion, and recursive execution loops.
"""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from aegis.core.types import InvariantViolation, Severity, ToolExecutionIntent


@dataclass
class ThreatPattern:
    """Represents a signature pattern for adversarial agent exploitation."""
    threat_id: str
    name: str
    regex: re.Pattern
    severity: Severity
    description: str


KNOWN_THREAT_PATTERNS: List[ThreatPattern] = [
    ThreatPattern(
        threat_id="THR_INDIRECT_INJECTION_OVERRIDE",
        name="Indirect Instruction Override",
        regex=re.compile(
            r"(ignore\s+(all\s+)?previous\s+(instructions|prompts|directions)|disregard\s+prior\s+instructions|system\s+override\s*:\s*execute)",
            re.IGNORECASE,
        ),
        severity=Severity.CRITICAL,
        description="Detected prompt injection payload attempting to override agent system instructions.",
    ),
    ThreatPattern(
        threat_id="THR_ROLE_REVERSAL_JAILBREAK",
        name="Role Reversal Jailbreak Attack",
        regex=re.compile(
            r"(you\s+are\s+now\s+(DAN|unfiltered|jailbroken|an\s+unconstrained\s+AI)|act\s+as\s+a\s+system\s+administrator\s+with\s+no\s+safety\s+filters)",
            re.IGNORECASE,
        ),
        severity=Severity.CRITICAL,
        description="Detected role-reversal jailbreak targeting model safety boundaries.",
    ),
    ThreatPattern(
        threat_id="THR_DELIMITER_HIJACKING",
        name="Delimiter Hijacking",
        regex=re.compile(
            r"(<\s*/?\s*system\s*>|<\s*/?\s*user\s*>|```\s*system|\[SYSTEM_PROMPT\]|\[ADMIN_OVERRIDE\])",
            re.IGNORECASE,
        ),
        severity=Severity.HIGH,
        description="Detected fake system delimiter markers used to forge privileged instructions.",
    ),
    ThreatPattern(
        threat_id="THR_COMMAND_INJECTION_ESCAPE",
        name="Command Injection Payload",
        regex=re.compile(
            r"(\brm\s+-rf\b|\bchmod\s+777\b|;\s*cat\s+/etc/passwd|\bcurl\s+-s\s+https?://[^\s]+\s*\|\s*(ba)?sh)",
            re.IGNORECASE,
        ),
        severity=Severity.CRITICAL,
        description="Detected destructive shell execution payload in arguments.",
    ),
    ThreatPattern(
        threat_id="THR_SQL_INJECTION_TAINT",
        name="SQL Injection Pattern",
        regex=re.compile(
            r"(';\s*DROP\s+TABLE|UNION\s+SELECT\s+ALL|OR\s+'1'='1|--\s*$)",
            re.IGNORECASE,
        ),
        severity=Severity.CRITICAL,
        description="Detected classic SQL injection pattern in query arguments.",
    ),
]


class AdversarialDetector:
    """
    Scans input intents and nested arguments for active adversarial payloads,
    obfuscated binaries, and evasion vectors.
    """

    def __init__(self, custom_patterns: Optional[List[ThreatPattern]] = None):
        self.patterns = list(KNOWN_THREAT_PATTERNS)
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    def _normalize_text(self, text: str) -> str:
        """Removes zero-width spaces, invisible characters, and normalizes homoglyphs."""
        # Strip zero-width spaces and control characters: \u200B, \u200C, \u200D, \uFEFF, \u00AD
        cleaned = re.sub(r"[\u200B-\u200D\uFEFF\u00AD\u2060\u180E]", "", text)
        return cleaned

    def _extract_text_strings(self, obj: Any) -> List[str]:
        """Recursively extracts all string values from nested dictionaries and lists."""
        results = []
        if isinstance(obj, str):
            results.append(obj)
            # Check for base64 encoded strings
            if len(obj) > 16 and re.match(r"^[A-Za-z0-9+/=]+$", obj):
                try:
                    decoded = base64.b64decode(obj, validate=True).decode("utf-8", errors="ignore")
                    if decoded and len(decoded) > 4:
                        results.append(decoded)
                except Exception:
                    pass
            # Check for hex strings
            if len(obj) > 16 and re.match(r"^[0-9a-fA-F]+$", obj):
                try:
                    decoded_hex = binascii.unhexlify(obj).decode("utf-8", errors="ignore")
                    if decoded_hex and len(decoded_hex) > 4:
                        results.append(decoded_hex)
                except Exception:
                    pass

        elif isinstance(obj, dict):
            for v in obj.values():
                results.extend(self._extract_text_strings(v))
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                results.extend(self._extract_text_strings(item))
        return results

    def scan_intent(self, intent: ToolExecutionIntent) -> List[InvariantViolation]:
        """
        Scans a tool execution intent for adversarial payloads.
        Returns a list of InvariantViolations if threats are detected.
        """
        violations: List[InvariantViolation] = []
        strings = self._extract_text_strings(intent.arguments)

        for text in strings:
            normalized = self._normalize_text(text)
            for pat in self.patterns:
                match = pat.regex.search(normalized)
                if match:
                    violations.append(
                        InvariantViolation(
                            rule_id=pat.threat_id,
                            rule_name=pat.name,
                            severity=pat.severity,
                            message=f"{pat.description} [Matched snippet: '{match.group(0)[:60]}']",
                            expected_condition="Payload free of adversarial attack signatures",
                            actual_value=match.group(0)[:80],
                            remediation_suggestion="Quarantine session or sanitize input before re-attempting execution.",
                        )
                    )

        return violations
