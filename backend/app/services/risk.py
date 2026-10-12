from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.services.extraction import ExtractedItem

CATEGORY_BANDS = (
    (25, "LOW"),
    (50, "MEDIUM"),
    (75, "HIGH"),
    (101, "CRITICAL"),
)


from dataclasses import field

@dataclass
class SignalResult:
    signal_type: str
    title: str
    explanation: str
    evidence: str
    contribution: int
    recommendation: str = ""


@dataclass
class RiskAssessment:
    score: int
    category: str
    signals: list[SignalResult]
    limitations: list[str]
    recommendation: str
    missing_data_warnings: list[str] = field(default_factory=list)


def categorize(score: int) -> str:
    bounded = max(0, min(100, score))
    for upper, label in CATEGORY_BANDS:
        if bounded < upper:
            return label
    return "CRITICAL"


def _has_phrase(items: list[ExtractedItem], prefix: str) -> list[ExtractedItem]:
    return [item for item in items if item.entity_type == "phrase" and item.normalized_value.startswith(f"{prefix}:")]


def _suspicious_url_reason(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?", host):
        return "Host is a raw IP address rather than a registered domain."
    if host.count("-") >= 3:
        return "Domain contains an unusually high number of hyphens."
    if parsed.scheme != "https":
        return "URL uses an unencrypted scheme."
    if any(token in host for token in ("login-", "secure-update", "verify-kyc", "refund-now")):
        return "Domain uses credential-harvesting language in its hostname."
    return None


def assess_risk(
    text: str,
    entities: list[ExtractedItem],
    related_count: int = 0,
    similar_high_risk: bool = False,
    ocr_limitation: str | None = None,
    url_inspected_as_string_only: bool = False,
) -> RiskAssessment:
    signals: list[SignalResult] = []
    used_groups: set[str] = set()

    def add(signal: SignalResult, group: str) -> None:
        if group in used_groups or signal.contribution <= 0:
            return
        used_groups.add(group)
        signals.append(signal)

    # 1. Unusually high advertised returns
    high_returns = _has_phrase(entities, "high_return_claim")
    if high_returns:
        add(
            SignalResult(
                signal_type="high_return_claim",
                title="Unusually high advertised returns",
                explanation=(
                    "The copy advertises return rates that substantially exceed normal regulated market benchmarks. "
                    "Outsized return claims represent a primary indicator of speculative or deceptive solicitations."
                ),
                evidence=high_returns[0].source_text,
                contribution=24,
                recommendation="Cross-reference advertised return rates against audited annual financial statements and regulatory benchmarks.",
            ),
            "high_return_claim",
        )

    # 2. Claims of guaranteed or risk-free returns
    guaranteed = _has_phrase(entities, "guaranteed_return")
    if guaranteed:
        add(
            SignalResult(
                signal_type="guaranteed_return",
                title="Guaranteed-return claim",
                explanation=(
                    "The copy promises assured, guaranteed, or risk-free financial outcomes. "
                    "Regulated investments inherently carry market risk; claims of guaranteed returns are a significant solicitation red flag."
                ),
                evidence=guaranteed[0].source_text,
                contribution=28,
                recommendation="Inspect statutory risk disclosures. Legitimate investment issuers are prohibited by financial regulators from guaranteeing speculative returns.",
            ),
            "guaranteed_return",
        )

    # 3. Urgency and pressure tactics
    urgency = _has_phrase(entities, "urgency")
    if urgency:
        add(
            SignalResult(
                signal_type="urgency_pressure",
                title="Urgency or pressure language",
                explanation=(
                    "The advertisement uses artificial time pressure or scarcity tactics to induce hasty action, "
                    "which limits the prospective investor's ability to conduct independent due diligence."
                ),
                evidence=urgency[0].source_text,
                contribution=14,
                recommendation="Conduct independent due diligence without time constraints before committing any capital.",
            ),
            "urgency",
        )

    # 4. Deposit bonuses and financial incentives
    deposit_incentives = _has_phrase(entities, "deposit_incentive")
    if deposit_incentives:
        add(
            SignalResult(
                signal_type="deposit_incentive",
                title="Deposit bonus or financial incentive",
                explanation=(
                    "The copy offers deposit bonuses, cash matching credits, or promotional incentives to trigger immediate capital deposits, "
                    "a common pattern in aggressive financial trading promotions."
                ),
                evidence=deposit_incentives[0].source_text,
                contribution=16,
                recommendation="Review terms of service for restrictive turnover requirements and withdrawal locks tied to promotional bonuses.",
            ),
            "deposit_incentive",
        )

    # 5. Regulatory registration claims requiring verification
    regulatory = _has_phrase(entities, "regulatory_claim")
    if regulatory:
        add(
            SignalResult(
                signal_type="regulatory_claim",
                title="Regulatory registration claim requiring verification",
                explanation=(
                    "The copy claims registration, regulation, or authorization by a financial regulatory body. "
                    "Unverified regulatory mentions require validation directly against official regulator databases."
                ),
                evidence=regulatory[0].source_text,
                contribution=12,
                recommendation="Search the official public registry of the named regulator (e.g., SEBI, FCA, SEC, FINRA) using the legal entity name or license number.",
            ),
            "regulatory_claim",
        )

    # 6. Requests for advance fees
    advance = _has_phrase(entities, "advance_payment")
    if advance:
        add(
            SignalResult(
                signal_type="advance_payment",
                title="Advance payment request",
                explanation="The copy asks for fees, processing charges, or deposits before a stated benefit or profit release is delivered.",
                evidence=advance[0].source_text,
                contribution=22,
                recommendation="Never pay upfront fees to release promised funds or investment profits.",
            ),
            "advance_payment",
        )

    # 7. Unverified testimonials and review statistics
    testimonials = _has_phrase(entities, "unverified_testimonials")
    if testimonials:
        add(
            SignalResult(
                signal_type="unverified_testimonials",
                title="Unverified testimonials or review statistics",
                explanation=(
                    "The advertisement presents crowd claims, high win rates, or review statistics that cannot be "
                    "substantiated from the advertisement alone."
                ),
                evidence=testimonials[0].source_text,
                contribution=12,
                recommendation="Request third-party audited performance track records rather than relying on self-reported advertising statistics.",
            ),
            "unverified_testimonials",
        )

    # 8. Suspicious payment instructions
    crypto_wallets = [item for item in entities if item.entity_type == "crypto_wallet"]
    suspicious_payments = _has_phrase(entities, "suspicious_payment")
    if crypto_wallets or suspicious_payments:
        evidence_text = crypto_wallets[0].source_text if crypto_wallets else suspicious_payments[0].source_text
        add(
            SignalResult(
                signal_type="suspicious_payment",
                title="Suspicious payment instructions",
                explanation=(
                    "The copy directs payment through cryptocurrency addresses or informal payment channels "
                    "that bypass standard regulated banking protections and investor dispute mechanisms."
                ),
                evidence=evidence_text,
                contribution=20,
                recommendation="Ensure all investment deposits are made to segregated corporate bank accounts registered in the licensed firm's legal name.",
            ),
            "suspicious_payment",
        )

    # 9. Requests for sensitive credentials
    credentials = _has_phrase(entities, "credential_request")
    if credentials:
        add(
            SignalResult(
                signal_type="credential_solicitation",
                title="Request for sensitive credentials",
                explanation="The advertisement asks for OTPs, PINs, CVVs, or account passwords. Legitimate institutions do not request secrets through ads.",
                evidence=credentials[0].source_text,
                contribution=50,
                recommendation="Never disclose one-time passwords (OTPs), PINs, or netbanking credentials in response to advertisements or unverified requests.",
            ),
            "credential_request",
        )

    # 10. High-yield solicitation language
    solicitation = _has_phrase(entities, "financial_solicitation")
    if solicitation:
        add(
            SignalResult(
                signal_type="suspicious_solicitation",
                title="High-yield solicitation language",
                explanation="The copy uses get-rich-quick, insider secrets, or aggressive money-multiplying language.",
                evidence=solicitation[0].source_text,
                contribution=16,
                recommendation="Treat claims of secret methods or guaranteed multiplication of capital with extreme caution.",
            ),
            "financial_solicitation",
        )

    # 11. Suspicious URL characteristics
    urls = [item for item in entities if item.entity_type == "url"]
    for url in urls:
        reason = _suspicious_url_reason(url.normalized_value)
        if reason:
            add(
                SignalResult(
                    signal_type="suspicious_url",
                    title="Suspicious URL characteristics",
                    explanation=f"{reason} The destination was not fetched; only the submitted URL string was inspected.",
                    evidence=url.normalized_value,
                    contribution=12,
                    recommendation="Verify the domain against official corporate registrations. Avoid entering sensitive details on suspicious or unencrypted hosts.",
                ),
                "suspicious_url",
            )
            break

    # 12. Cross-advertisement repeated entities
    if related_count >= 2:
        contribution = 8 if related_count < 4 else 14
        add(
            SignalResult(
                signal_type="repeated_entities",
                title="Shared entities with other advertisements",
                explanation=(
                    f"This advertisement shares contact, payment, or domain evidence with {related_count} other analyzed advertisements. "
                    "Shared identifiers suggest a possible relationship, not common criminal ownership."
                ),
                evidence=f"{related_count} related advertisements",
                contribution=contribution,
                recommendation="Cross-examine connected advertisements and investigate whether they represent a coordinated promotional campaign.",
            ),
            "repeated_entities",
        )

    # 13. Similar to higher-risk advertisement
    if similar_high_risk:
        add(
            SignalResult(
                signal_type="similar_high_risk_copy",
                title="Similar to a higher-risk advertisement",
                explanation=(
                    "The text is similar to another advertisement that already carries elevated risk indicators. "
                    "Similarity is an investigative lead, not independent proof."
                ),
                evidence="TF-IDF cosine similarity above the configured threshold",
                contribution=8,
                recommendation="Review the similar advertisement records for common copy patterns or coordinated syndication.",
            ),
            "similar_high_risk_copy",
        )

    raw_score = sum(signal.contribution for signal in signals)
    score = max(0, min(100, raw_score))

    limitations = [
        "The score is a configured rules-based triage assessment, not a statistically calibrated probability of fraud.",
        "Extracted identifiers are observable strings, not verified identities.",
    ]
    missing_data_warnings: list[str] = []

    if ocr_limitation:
        limitations.append(ocr_limitation)
    if url_inspected_as_string_only:
        limitations.append("Submitted URLs were parsed as text only; destinations were not fetched or executed.")
    if not text.strip():
        limitations.append("No advertisement text was available, so analysis coverage is limited.")
        missing_data_warnings.append("No readable text was available for analysis. Triage assessment cannot score risk without copy.")

    if not text.strip():
        recommendation = "Analysis inconclusive: No advertisement text was available to evaluate. Provide advertisement copy or a readable image."
    elif score >= 75:
        recommendation = "Prioritize investigator review. Collect corroborating evidence before any enforcement action."
    elif score >= 50:
        recommendation = "Review extracted entities and related advertisements. Treat findings as potentially suspicious until verified."
    elif score >= 25:
        recommendation = "Monitor for additional matching evidence. The current indicators are moderate."
    else:
        recommendation = "No elevated rule-based indicators were found. This does not certify legitimacy."

    return RiskAssessment(
        score=score,
        category=categorize(score),
        signals=signals,
        limitations=limitations,
        recommendation=recommendation,
        missing_data_warnings=missing_data_warnings,
    )
