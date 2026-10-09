from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Inquiry:
    inquiry_language: str
    customer_name: str
    property_name: str
    request_type: str
    move_in_date: str
    budget: str
    requirements: str
    notes: str = ""


VERIFY_ITEMS: List[str] = [
    "current availability",
    "current rent and fees",
    "deposit, key money, and other initial costs",
    "furnishing status",
    "lease type and term",
    "applicant eligibility and screening requirements",
    "viewing date availability",
    "English-language support and document availability",
]


@dataclass(frozen=True)
class ResponseDraft:
    """Keep customer-facing content separate from internal-only information."""

    customer_reply: str
    internal_checklist: str


def build_english_reply(inquiry: Inquiry) -> str:
    return f"""Subject: Re: Your Rental Inquiry - {inquiry.property_name}

Dear {inquiry.customer_name},

Thank you for contacting us regarding your apartment search in Tokyo.

We understand that you are looking for {inquiry.requirements}, with a target move-in date of {inquiry.move_in_date} and a budget of approximately {inquiry.budget}.

Regarding {inquiry.property_name}, we will first confirm the latest availability and lease conditions. As availability and terms may change, we would prefer to verify the current information before making any commitment.

We can also review comparable properties that may suit your requirements. If you could share your preferred viewing dates and any additional priorities, such as parking, pet requirements, furniture, school access, or commute preferences, we can narrow the options accordingly.

Once the latest information has been confirmed, we will provide you with the available options and possible viewing arrangements.

Best regards,
[Staff Name]
[Company]
"""


def build_japanese_reply(inquiry: Inquiry) -> str:
    return f"""件名: {inquiry.property_name}のお問い合わせについて

{inquiry.customer_name} 様

この度は、東京でのお住まい探しについてお問い合わせいただき、ありがとうございます。

{inquiry.move_in_date}頃のご入居、月額{inquiry.budget}程度のご予算で、{inquiry.requirements}をご希望とのこと、承知いたしました。

{inquiry.property_name}につきましては、最新の空室状況および募集条件を確認のうえ、改めてご案内いたします。空室状況や条件は変動する可能性があるため、確認前の段階では確約せず、最新情報を確認してご回答いたします。

また、ご希望条件に近い類似物件についても併せて確認可能です。内見希望日時のほか、駐車場、ペット、家具、学校へのアクセス、通勤条件など、優先される条件がございましたらお知らせください。

最新情報を確認でき次第、ご紹介可能な物件および内見候補についてご連絡いたします。

よろしくお願いいたします。

[担当者名]
[会社名]
"""


def build_internal_checklist(inquiry: Inquiry) -> str:
    lines = ["Internal verification required before sending:"]
    lines.extend(f"- [ ] {item}" for item in VERIFY_ITEMS)

    if inquiry.notes:
        lines.append("")
        lines.append(f"Notes: {inquiry.notes}")

    return "\n".join(lines)


def generate_response(inquiry: Inquiry) -> ResponseDraft:
    if inquiry.inquiry_language not in {"ja", "en"}:
        raise ValueError("inquiry_language must be 'ja' or 'en'")

    primary_reply = (
        build_japanese_reply(inquiry)
        if inquiry.inquiry_language == "ja"
        else build_english_reply(inquiry)
    )

    return ResponseDraft(
        customer_reply=primary_reply,
        internal_checklist=build_internal_checklist(inquiry),
    )


if __name__ == "__main__":
    sample = Inquiry(
        inquiry_language="en",
        customer_name="Alex Smith",
        property_name="Sakura Residence Azabu",
        request_type="viewing",
        move_in_date="2026-09-15",
        budget="JPY 650,000/month",
        requirements="a furnished 2LDK or larger apartment in the Azabu area with English support",
        notes="Fictional test data only. Do not treat availability or lease conditions as confirmed.",
    )

    draft = generate_response(sample)
    print("=== CUSTOMER REPLY ===")
    print(draft.customer_reply)
    print("=== INTERNAL CHECKLIST (DO NOT SEND) ===")
    print(draft.internal_checklist)

