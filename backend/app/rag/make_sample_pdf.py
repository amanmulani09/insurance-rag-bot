from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DEFAULT_PDF_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge.pdf"


def make_pdf(path: str | Path = DEFAULT_PDF_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(path), pagesize=letter)
    text = c.beginText(40, 750)
    lines = [
    "Insurance Agency Customer Care Knowledge Base",
    "",

    "Q: How do I file an insurance claim?",
    "A: You can file a claim online through our customer portal, mobile app, or by calling our claims department. Please provide policy details, incident information, photos, and supporting documents.",

    "",

    "Q: What is a deductible?",
    "A: A deductible is the amount you must pay out of pocket before your insurance coverage begins paying for a covered loss.",

    "",

    "Q: How long does claim processing take?",
    "A: Most claims are processed within 5 to 10 business days after all required documentation has been received.",

    "",

    "Q: How can I add a driver to my auto insurance policy?",
    "A: Contact customer support or log in to your account. We will need the driver's full name, date of birth, license number, and the date coverage should begin.",

    "",

    "Q: What documents are required for a new auto insurance policy?",
    "A: We typically require a government-issued ID, vehicle registration, driver's license, address proof, and previous insurance details if available.",

    "",

    "Q: What types of insurance do you offer?",
    "A: We offer auto insurance, home insurance, renters insurance, life insurance, health insurance, travel insurance, and commercial insurance products.",

    "",

    "Q: How do I update my address?",
    "A: You can update your address through the customer portal or by contacting our support team. Proof of residence may be required in some cases.",

    "",

    "Q: Can I pay my premium online?",
    "A: Yes. Premium payments can be made online using credit cards, debit cards, net banking, UPI, or automatic bank transfers.",

    "",

    "Q: What happens if I miss a premium payment?",
    "A: Your policy may enter a grace period. If payment is not received before the grace period ends, coverage may be suspended or canceled.",

    "",

    "Q: How do I download my policy documents?",
    "A: Log in to the customer portal and navigate to the Policy Documents section to download copies of your insurance certificates and policy schedules.",

    "",

    "Q: How can I renew my policy?",
    "A: Policies can be renewed online, through the mobile app, or by contacting an insurance advisor before the expiration date.",

    "",

    "Q: What should I do after a car accident?",
    "A: Ensure everyone's safety, contact emergency services if needed, document the scene with photos, exchange information with other parties, and notify us as soon as possible.",

    "",

    "Q: Does my auto policy cover rental cars?",
    "A: Coverage depends on your policy terms. Please review your policy documents or contact customer support for specific details.",

    "",

    "Q: What is covered under homeowners insurance?",
    "A: Homeowners insurance typically covers dwelling damage, personal belongings, liability protection, and additional living expenses resulting from covered events.",

    "",

    "Q: How do I report a stolen vehicle?",
    "A: First report the theft to local law enforcement, obtain a police report number, and then contact our claims department immediately.",

    "",

    "Q: Can I cancel my policy at any time?",
    "A: Most policies can be canceled at any time, subject to policy terms. Refund eligibility depends on the policy type and cancellation date.",

    "",

    "Q: What factors affect my insurance premium?",
    "A: Premiums may be influenced by age, location, claims history, coverage limits, deductibles, credit profile where permitted, and risk factors specific to the insured item.",

    "",

    "Q: How do I change my coverage limits?",
    "A: Contact your insurance advisor or use the customer portal to request coverage changes. A revised premium quote may apply.",

    "",

    "Q: What is liability insurance?",
    "A: Liability insurance helps cover costs if you are legally responsible for injuries or property damage caused to others.",

    "",

    "Q: How do I check my claim status?",
    "A: Claim status can be viewed online through the customer portal or by contacting our claims support team.",

    "",

    "Q: Is roadside assistance included in my policy?",
    "A: Roadside assistance is available on select auto insurance plans and may include towing, battery jump-starts, fuel delivery, and lockout assistance.",

    "",

    "Q: What should I do if my policy has expired?",
    "A: Contact us immediately to discuss renewal options. Some policies may require additional underwriting or inspections before reinstatement.",

    "",

    "Q: How can I contact customer support?",
    "A: Customer support is available via phone, email, live chat, and the mobile application during business hours."
    ]
    for line in lines:
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    print(f"Created sample PDF at {path}")

if __name__ == "__main__":
    make_pdf()
