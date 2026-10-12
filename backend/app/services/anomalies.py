from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from app.services.extraction import ExtractedItem
from app.services.risk import SignalResult


@dataclass
class ContentAnomaly:
    id: str
    anomaly_type: str
    title: str
    explanation: str
    evidence: str
    severity: str


DISCLAIMER_TERMS = re.compile(
    r"\b(?:capital (?:is )?at risk|subject to market risk|past performance (?:is not|does not)|securities can lose value|trading involves (?:high )?risk|losses can exceed|investments? (?:are )?subject to)\b",
    re.I,
)

SPECULATIVE_TERMS = re.compile(
    r"\b(?:forex|crypto(?:currency)?|bitcoin|btc|usdt|options|derivatives|binary options|day trading|algorithmic trading)\b",
    re.I,
)

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com", "proton.me", "protonmail.com"}


def detect_content_anomalies(
    text: str,
    entities: list[ExtractedItem],
    signals: list[SignalResult],
) -> list[ContentAnomaly]:
    anomalies: list[ContentAnomaly] = []
    seen_types: set[str] = set()

    if not text.strip():
        return []

    # 1. Extreme Advertised Return Claims
    high_return_items = [e for e in entities if e.entity_type == "phrase" and e.normalized_value.startswith("high_return_claim:")]
    doubling_items = [e for e in entities if e.entity_type == "phrase" and e.normalized_value.startswith("financial_solicitation:")]
    extreme_item = None
    for item in high_return_items:
        # e.g. "high_return_claim:20.0% monthly:20% monthly"
        parts = item.normalized_value.split(":")
        if len(parts) >= 2:
            spec = parts[1].lower()
            try:
                rate_val = float(re.search(r"\d+(?:\.\d+)?", spec).group(0))
            except (AttributeError, ValueError):
                rate_val = 0.0

            if any(term in spec for term in ("day", "daily")) and rate_val >= 1.5:
                extreme_item = item
                break
            elif any(term in spec for term in ("week", "weekly")) and rate_val >= 8.0:
                extreme_item = item
                break
            elif any(term in spec for term in ("month", "monthly", "p.m")) and rate_val >= 15.0:
                extreme_item = item
                break
            elif any(term in spec for term in ("year", "annual", "apy")) and rate_val >= 50.0:
                extreme_item = item
                break
            elif rate_val >= 25.0:
                extreme_item = item
                break

    if not extreme_item and doubling_items:
        for item in doubling_items:
            if any(w in item.raw_value.lower() for w in ("double", "triple", "multiply")):
                extreme_item = item
                break

    if extreme_item and "extreme_return_claim" not in seen_types:
        seen_types.add("extreme_return_claim")
        anomalies.append(
            ContentAnomaly(
                id=str(uuid.uuid4()),
                anomaly_type="extreme_return_claim",
                title="Extreme Advertised Return",
                explanation=(
                    "The advertisement advertises return rates that deviate drastically from standard regulated investment benchmarks "
                    "(which historically average 8-12% annually for broad equity markets). Such extreme yields are anomalous in legitimate finance."
                ),
                evidence=extreme_item.source_text,
                severity="HIGH",
            )
        )

    # 2. Conflicting Claims within an Advertisement
    has_guarantee = any(s.signal_type == "guaranteed_return" for s in signals)
    disclaimer_match = DISCLAIMER_TERMS.search(text)
    speculative_match = SPECULATIVE_TERMS.search(text)
    if has_guarantee and (disclaimer_match or speculative_match) and "conflicting_risk_claims" not in seen_types:
        seen_types.add("conflicting_risk_claims")
        conflict_evidence = []
        guarantee_sig = next(s for s in signals if s.signal_type == "guaranteed_return")
        conflict_evidence.append(f"Guaranteed claim: '{guarantee_sig.evidence}'")
        if disclaimer_match:
            conflict_evidence.append(f"Disclaimer: '{disclaimer_match.group(0)}'")
        if speculative_match:
            conflict_evidence.append(f"Speculative asset: '{speculative_match.group(0)}'")

        anomalies.append(
            ContentAnomaly(
                id=str(uuid.uuid4()),
                anomaly_type="conflicting_risk_claims",
                title="Conflicting Risk Disclosures",
                explanation=(
                    "The advertisement presents contradictory risk statements, asserting guaranteed or risk-free results while "
                    "acknowledging investment risk or describing speculative markets."
                ),
                evidence=" | ".join(conflict_evidence),
                severity="HIGH",
            )
        )

    # 3. Unusual Combinations of Financial Promises and Urgency
    has_urgency = any(s.signal_type == "urgency_pressure" for s in signals)
    has_financial_promise = any(
        s.signal_type in {"high_return_claim", "guaranteed_return", "suspicious_solicitation", "deposit_incentive"}
        for s in signals
    )
    if has_urgency and has_financial_promise and "high_yield_urgency_combination" not in seen_types:
        seen_types.add("high_yield_urgency_combination")
        urgency_sig = next(s for s in signals if s.signal_type == "urgency_pressure")
        promise_sig = next(
            s for s in signals if s.signal_type in {"high_return_claim", "guaranteed_return", "suspicious_solicitation", "deposit_incentive"}
        )
        anomalies.append(
            ContentAnomaly(
                id=str(uuid.uuid4()),
                anomaly_type="high_yield_urgency_combination",
                title="High-Yield Promise with Urgency Pressure",
                explanation=(
                    "The copy combines an aggressive financial return or bonus promise with artificial urgency tactics. "
                    "This combination is structured to induce hasty decisions and compress the investor's due diligence window."
                ),
                evidence=f"Promise: '{promise_sig.evidence}' | Urgency: '{urgency_sig.evidence}'",
                severity="HIGH",
            )
        )

    # 4. Inconsistencies Between Stated Claims and Available Evidence
    has_regulatory_claim = any(s.signal_type == "regulatory_claim" for s in signals)
    personal_channels = []
    for item in entities:
        if item.entity_type == "upi":
            personal_channels.append(f"P2P UPI handle: {item.normalized_value}")
        elif item.entity_type == "email":
            domain = item.normalized_value.split("@")[-1].lower()
            if domain in FREE_EMAIL_DOMAINS:
                personal_channels.append(f"Free webmail: {item.normalized_value}")
        elif item.entity_type == "crypto_wallet":
            personal_channels.append(f"Crypto wallet: {item.normalized_value}")

    suspicious_url_sig = next((s for s in signals if s.signal_type == "suspicious_url"), None)
    if suspicious_url_sig and "ip address" in suspicious_url_sig.explanation.lower():
        personal_channels.append(f"Raw IP host: {suspicious_url_sig.evidence}")

    if has_regulatory_claim and personal_channels and "institutional_channel_inconsistency" not in seen_types:
        seen_types.add("institutional_channel_inconsistency")
        reg_sig = next(s for s in signals if s.signal_type == "regulatory_claim")
        anomalies.append(
            ContentAnomaly(
                id=str(uuid.uuid4()),
                anomaly_type="institutional_channel_inconsistency",
                title="Regulatory Claim Inconsistent with Payment Channel",
                explanation=(
                    "The advertisement claims official regulatory registration or institutional status, but directs payment or contact "
                    "to personal peer-to-peer handles, free webmail, or unverified hosts. Regulated financial entities operate through verified corporate channels."
                ),
                evidence=f"Claim: '{reg_sig.evidence}' | Channel: '{personal_channels[0]}'",
                severity="CRITICAL",
            )
        )

    return anomalies
