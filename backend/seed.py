from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models import Advertisement  # noqa: E402
from app.services.analysis import analyze_advertisement  # noqa: E402


def templates() -> list[dict]:
    cluster_a_phone = "+91 90000 11111"
    cluster_a_upi = "quickgain@okaxis"
    cluster_a_url = "http://quick-gain-now.example.com/join"
    cluster_b_phone = "080-4455-7788"
    cluster_b_domain = "kyc-update-secure.example.net"
    cluster_c_email = "payouts@ledgerboost.example"
    cluster_c_upi = "ledgerboost@upi"

    ads: list[dict] = []

    for i in range(1, 9):
        ads.append(
            {
                "seed_key": f"cluster-a-{i}",
                "source": "messaging",
                "source_url": cluster_a_url if i % 2 else None,
                "text": (
                    f"Guaranteed returns of 8% weekly. Double your money with QuickGain plan {i}. "
                    f"Limited time: act now and pay the processing fee. Call {cluster_a_phone} "
                    f"or send funds to {cluster_a_upi}. Visit {cluster_a_url}."
                ),
            }
        )

    for i in range(1, 7):
        ads.append(
            {
                "seed_key": f"cluster-b-{i}",
                "source": "social",
                "text": (
                    f"Your bank KYC is pending. Share OTP immediately to avoid account freeze. "
                    f"Visit https://{cluster_b_domain}/verify-{i} and call {cluster_b_phone} today only."
                ),
            }
        )

    for i in range(1, 6):
        ads.append(
            {
                "seed_key": f"cluster-c-{i}",
                "source": "website",
                "text": (
                    f"LedgerBoost insider tip: multiply your investment in 48 hours. "
                    f"Deposit now via {cluster_c_upi}. Questions? Email {cluster_c_email}."
                ),
            }
        )

    similar_base = (
        "Urgent payout window closing tonight. Advance payment required to release profits. "
        "Contact 98765 43210 and use harvest@okicici."
    )
    for i in range(1, 5):
        ads.append(
            {
                "seed_key": f"similar-payout-{i}",
                "source": "forum",
                "text": f"{similar_base} Reference desk {i} for onboarding.",
            }
        )

    ordinary = [
        "Open a high-yield savings account with transparent interest rates. Past returns are not guaranteed.",
        "Compare no-fee checking accounts. Terms and eligibility apply.",
        "Download our budgeting worksheet to track monthly expenses.",
        "Home loan pre-qualification is subject to credit assessment.",
        "Student loan refinancing may lower payments depending on credit history.",
        "Set up an automatic transfer to your emergency fund each payday.",
        "Merchant POS terminals are available for small retailers after KYC.",
        "Foreign exchange travel cards have published conversion fees.",
        "Insurance premiums vary by age, coverage, and underwriting.",
        "Payroll direct deposit typically posts within one business day.",
    ]
    for i, text in enumerate(ordinary, start=1):
        ads.append({"seed_key": f"ordinary-{i}", "source": "display", "text": text})

    education = [
        "Investment education webinar: diversification basics. Securities can lose value.",
        "Learn how index funds work. This is not personalized investment advice.",
        "Retirement planning workshop covering contribution limits and tax treatment.",
        "Bond ladder explainer for long-term savers. Capital is at risk.",
        "How SIP instalments average purchase cost over time. Returns are not assured.",
        "Credit score education: on-time payments matter more than advertised hacks.",
        "Fraud awareness: banks will not ask for OTP or PIN over advertisements.",
        "Mutual fund factsheets disclose expense ratios and historical performance.",
        "Understand lock-in periods before purchasing tax-saving instruments.",
        "Read the offer document before subscribing to any public issue.",
    ]
    for i, text in enumerate(education, start=1):
        ads.append({"seed_key": f"education-{i}", "source": "webinar", "text": text})

    mild = [
        "Personal loan from 10.5% subject to approval. Apply on fairlend.example.",
        "Balance transfer credit card with a 12-month introductory rate.",
        "Gold savings plan with making charges disclosed at checkout.",
        "Tax-filing assistance for salaried employees. Government portals remain free.",
        "MSME working-capital line. Collateral and documentation required.",
        "Vehicle finance for certified pre-owned cars. EMI calculator on site.",
        "Health cover waiting periods apply for pre-existing conditions.",
        "Demat account opening with statutory charges listed in the tariff sheet.",
        "UPI collect requests should only be accepted from known merchants.",
        "Fixed deposit rates are published daily and can change without notice.",
    ]
    for i, text in enumerate(mild, start=1):
        ads.append({"seed_key": f"mild-{i}", "source": "search", "text": text})

    singleton_suspicious = [
        {
            "seed_key": "solo-advance-1",
            "source": "sms",
            "text": "Your refund of Rs 48,000 is ready. Pay a 999 registration fee to 8811223344 first.",
        },
        {
            "seed_key": "solo-guarantee-1",
            "source": "video",
            "text": "Risk-free profit club. Assured income every Friday. Join via profitpulse.example.org.",
        },
        {
            "seed_key": "solo-credentials-1",
            "source": "email",
            "text": "Confirm netbanking password and CVV to unlock a blocked UPI limit. Ignore if not requested? Act now.",
        },
        {
            "seed_key": "solo-ip-url",
            "source": "chat",
            "text": "Claim trading bonus at http://203.0.113.44/secure-update. Limited seats.",
        },
    ]
    ads.extend(singleton_suspicious)

    unrelated_contacts = [
        ("+91 91111 20001", "northdesk@pay.example"),
        ("+91 91111 20002", "southdesk@pay.example"),
        ("+91 91111 20003", "westdesk@pay.example"),
        ("+91 91111 20004", "eastdesk@pay.example"),
        ("+91 91111 20005", "centraldesk@pay.example"),
    ]
    for i, (phone, email) in enumerate(unrelated_contacts, start=1):
        ads.append(
            {
                "seed_key": f"unrelated-contact-{i}",
                "source": "classified",
                "text": f"Freelance bookkeeping available. Call {phone} or email {email}. Hourly rates on request.",
            }
        )

    for i in range(1, 21):
        ads.append(
            {
                "seed_key": f"filler-{i}",
                "source": "display",
                "text": (
                    f"Quarterly market commentary {i}: asset allocation should match time horizon. "
                    "No guaranteed outcome is offered. Visit learn.markets.example/guide."
                ),
            }
        )

    for i in range(1, 16):
        ads.append(
            {
                "seed_key": f"retail-bank-{i}",
                "source": "app",
                "text": (
                    f"Enable spending alerts in the mobile app (notice {i}). "
                    "Never share OTP, PIN, or CVV with advertisers."
                ),
            }
        )

    extra_cluster_phone = "99988 77665"
    for i in range(1, 4):
        ads.append(
            {
                "seed_key": f"cluster-d-{i}",
                "source": "marketplace",
                "text": (
                    f"Crypto recovery agent can restore frozen wallets after an upfront fee. "
                    f"WhatsApp {extra_cluster_phone}. Ticket {i}."
                ),
            }
        )

    return ads


def seed(db: Session) -> int:
    created = 0
    for item in templates():
        existing = db.query(Advertisement).filter_by(seed_key=item["seed_key"]).one_or_none()
        if existing:
            continue
        ad = Advertisement(
            seed_key=item["seed_key"],
            is_seed=True,
            text=item["text"],
            source=item.get("source"),
            source_url=item.get("source_url"),
            analysis_status="processing",
        )
        db.add(ad)
        db.flush()
        analyze_advertisement(db, ad)
        created += 1
    db.commit()
    return created


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = seed(db)
        total = db.query(Advertisement).count()
        print(f"Seed complete. New records: {created}. Total advertisements: {total}.")
        print("Dataset is synthetic demonstration data, not real investigations.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
