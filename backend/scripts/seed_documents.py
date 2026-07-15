import os
from pathlib import Path

docs = {
    "discount_policy.txt": """
Enterprise Operations - Discount & Pricing Policy

1. Standard Discounts
- Sales representatives may offer up to a 10% discount on Enterprise Software contracts without prior approval.
- Discounts between 11% and 20% require approval from the Regional Sales Director.
- Any discount exceeding 20% requires approval from the VP of Sales.

2. Cloud Infrastructure Pricing
- Cloud Infrastructure services have a strict maximum discount of 15% due to fixed hardware costs.
- Volume discounts are applied automatically for compute usage exceeding 100,000 core-hours per month.

3. End-of-Quarter Incentives
- During the final two weeks of Q4, sales representatives are authorized to increase standard discounts by an additional 5% to close pending deals.
""",

    "hr_handbook.txt": """
Enterprise Operations - Employee Handbook Excerpt

1. Remote Work Policy
- Employees are permitted to work remotely up to 3 days per week.
- Core hours (10:00 AM to 3:00 PM local time) require employees to be online and available for meetings.

2. Expense Reimbursement
- All business expenses must be submitted within 30 days of the transaction.
- Meals with clients have a maximum reimbursement limit of $150 per person.
- Flights must be booked in economy class unless the flight duration exceeds 8 hours, in which case business class is permitted with VP approval.
"""
}

def seed_documents():
    print("Generating sample knowledge base documents...")
    
    # Create sample directory
    sample_dir = Path("backend/scripts/sample_data")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, content in docs.items():
        path = sample_dir / filename
        path.write_text(content.strip(), encoding="utf-8")
        print(f"Created {path}")

    print("Sample documents generated. Upload them via the UI to populate the RAG database.")

if __name__ == "__main__":
    seed_documents()
