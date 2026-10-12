#!/usr/bin/env python3
"""CampusVoice Synthetic Dataset Generator.

Generates:
1. data/train_labeled.csv: 600 labeled rows for Glue MLlib text classification.
2. data/sample_feedback.csv: 300 raw student feedback rows with fake PII for pipeline testing.

Deterministic execution using random.seed(42).
No third-party dependencies (pure standard library).
"""

import csv
import os
import random
from datetime import datetime, timedelta

# Fix seed for strict reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

CATEGORIES = [
    "HOSTEL",
    "FACULTY",
    "LABS",
    "CANTEEN",
    "INFRASTRUCTURE",
    "ADMIN",
    "OTHER",
]

DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"]
YEARS = [1, 2, 3, 4]

# Indian names pool for synthetic PII
FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Deepak", "Divya", "Gaurav",
    "Ishaan", "Kavya", "Manish", "Neha", "Nikhil", "Pooja", "Pranav", "Priya",
    "Rahul", "Rhea", "Rohan", "Sanjay", "Shreya", "Siddharth", "Sneha", "Tanvi",
    "Varun", "Vikas", "Vikram", "Yash", "Meera", "Karan"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta", "Singh",
    "Kumar", "Joshi", "Chopra", "Rao", "Das", "Bose", "Mehta", "Kulkarni",
    "Deshmukh", "Menon", "Chatterjee", "Mishra"
]

EMAIL_DOMAINS = ["example.com", "campusmail.org", "testuniv.edu", "mymail.in"]

# Templates for training data (diverse positive and negative feedback)
CATEGORY_TEMPLATES = {
    "HOSTEL": [
        "The hostel water supply is frequently interrupted in Block {block}, especially during morning peak hours.",
        "Geyser and hot water facilities in the hostel washrooms have not been functional for two weeks.",
        "The hostel mess food quality is {qual_neg}, with cold chapatis and repetitive vegetable curry.",
        "Hostel warden was very {qual_pos} and promptly resolved the electrical tripping issue in our wing.",
        "Cleanliness in the hostel corridors and common bathrooms is maintained well by the housekeeping staff.",
        "Hostel room locks and window latches in wing {block} need urgent repairs for security.",
        "The night curfew and gate entry register process in the hostel is overly restrictive and stressful.",
        "Good ventilation and spacious study tables provided in the newly renovated hostel rooms.",
        "Drinking water coolers on the second floor of the hostel are leaking and unhygienic.",
        "Hostel laundry service is punctual and clothes are returned properly cleaned and pressed.",
        "Loud noise in the hostel common room during quiet hours disrupts examination preparation.",
        "The hostel mess committee took student suggestions and noticeably improved Sunday lunch quality."
    ],
    "FACULTY": [
        "The professor explains core data structures concepts with {qual_pos} clarity and real-world examples.",
        "Lectures in signal processing move too quickly and there is inadequate time for solving doubts.",
        "Faculty members in our department are very approachable and guide us patiently through research papers.",
        "The course instructor rarely uploads lecture notes and presentations on the university portal.",
        "Evaluation of mid-term examinations was inconsistent and lacks transparent feedback on marks deducted.",
        "Our mathematics professor conducts helpful remedial sessions before semester finals.",
        "Guest lectures arranged by the department faculty provided excellent industry perspective.",
        "The lecturer merely reads slides from textbooks without demonstrating practical implementation.",
        "Faculty mentorship during the capstone mini-project has been exceptionally supportive and insightful.",
        "Attendance policies are enforced too strictly even when genuine medical certificates are submitted.",
        "Clear rubric provided for assignments helped us understand expectations and scoring criteria.",
        "The teacher encouraged classroom discussions and encouraged questions from all students."
    ],
    "LABS": [
        "Digital electronics lab equipment like function generators and oscilloscopes are broken or uncalibrated.",
        "Computer lab systems have updated GPU drivers and smooth development environments for machine learning.",
        "Internet connectivity in the programming lab keeps disconnecting during timed coding assessments.",
        "Lab assistants are very knowledgeable and help troubleshoot circuit connection errors promptly.",
        "Chemistry lab safety goggles and glassware are worn out and need immediate replacement.",
        "The new microcontrollers and FPGA development boards received in the lab are top notch.",
        "Software licenses for simulation tools expired three weeks ago and have still not been renewed.",
        "Air conditioning in the computer laboratory was not working, making the room uncomfortably hot.",
        "Comprehensive lab manuals with step-by-step experiment instructions made the practicals easy to follow.",
        "Not enough working desktop machines available, forcing three students to share a single computer.",
        "The robotics lab has excellent 3D printers and soldering stations for hands-on prototyping.",
        "Lab examination questions were well-structured and tested actual practical problem-solving."
    ],
    "CANTEEN": [
        "Canteen food prices have increased significantly while serving portions have become smaller.",
        "Fresh fruit juices and south Indian breakfast items in the central canteen are {qual_pos} and affordable.",
        "Drinking water dispensers in the canteen area are unhygienic and look poorly maintained.",
        "Long queues and malfunctioning UPI payment scanners cause huge delays during the lunch break.",
        "The canteen seating area is overcrowded and tables are rarely wiped between student meals.",
        "Snack options like sandwiches and samosas served in the evening canteen are always hot and fresh.",
        "Food hygiene standards need inspection as several students reported mild stomach upsets.",
        "Great variety of healthy vegetarian options and salads introduced in the cafeteria menu.",
        "Tea and coffee served at the campus kiosk are consistently excellent and reasonably priced.",
        "Packaged drinking water and snacks are sold above maximum retail price in the campus canteen.",
        "Friendly and polite canteen staff who manage the heavy rush hours efficiently.",
        "The canteen food is excessively oily and spices are overpowering in the thali meals."
    ],
    "INFRASTRUCTURE": [
        "Campus Wi-Fi connectivity in academic buildings has high latency and drops connections frequently.",
        "Classroom projector in hall {block} has dim projection and flickering display issues.",
        "Central library offers a quiet, air-conditioned study environment with extensive digital journal access.",
        "Washrooms on the third floor of the engineering block are frequently out of running water.",
        "Ramps and elevators for physically challenged students are well-maintained across all major blocks.",
        "Power backup failed during afternoon lectures, leaving classrooms without fans in summer heat.",
        "Auditorium sound system and acoustic panels created an impressive experience during cultural events.",
        "Water purifier on the ground floor dispenses warm and muddy-looking drinking water.",
        "Spacious benches, charging sockets at every desk, and good acoustics in the new lecture halls.",
        "Campus pathways are dimly lit at night, posing safety concerns for students returning late from labs.",
        "The sports complex badminton courts and gym equipment are well-kept and open convenient hours.",
        "Broken desks and loose electrical wires in classroom {block} require immediate repair."
    ],
    "ADMIN": [
        "Administrative office staff are unhelpful and make students visit multiple counters for fee receipts.",
        "Online exam registration and hall ticket download portal was smooth and worked without glitches.",
        "Scholarship disbursement process has been delayed by over four months without clear status updates.",
        "Student helpdesk responded within twenty-four hours and corrected the spelling on my marksheet.",
        "Long turnaround time for issuing bonafide certificates needed for passport and education loan applications.",
        "Accounts section does not accept digital payments for fine payments, insisting on manual challans.",
        "Transparent academic calendar with clear exam schedules and holiday dates published well in advance.",
        "Library card renewal process was tedious due to server downtime in the administration server.",
        "College administration handled the bus pass distribution smoothly through class coordinators.",
        "Hostel caution deposit refund takes more than a semester to process after graduating.",
        "Admission office personnel patiently guided applicants and resolved documentation queries.",
        "Grievance redressal portal does not acknowledge complaints or provide tracking ticket numbers."
    ],
    "OTHER": [
        "College annual technical symposium was well-organized with competitive hackathons and great prizes.",
        "College bus transport service on route {block} is consistently late due to poor schedule planning.",
        "Campus placement training cell conducted helpful mock interviews and resume critique sessions.",
        "Two-wheeler parking lot is disorganized and vehicles often suffer scratches due to overcrowding.",
        "Extracurricular clubs and cultural societies receive ample support and funding from management.",
        "General atmosphere on campus is welcoming and encourages inter-departmental student collaboration.",
        "Sports equipment like basketballs and cricket kits are insufficient during afternoon practice sessions.",
        "Overall college experience has been rewarding, though small operational bottlenecks remain.",
        "Campus greenery, lawns, and tree cover make the institute environment peaceful and pleasant.",
        "Bus drivers often drive rashly and overcrowd the college buses during return evening trips.",
        "Blood donation camp and NSS social outreach activities were conducted with commendable enthusiasm.",
        "Lack of designated recycling bins on campus leads to plastic waste accumulating near benches."
    ]
}


def generate_train_dataset(total_rows=600):
    """Generate balanced training dataset with 600 rows."""
    rows_per_category = total_rows // len(CATEGORIES)
    remainder = total_rows % len(CATEGORIES)

    qual_pos_list = ["excellent", "great", "outstanding", "satisfactory", "pleasant", "good"]
    qual_neg_list = ["terrible", "substandard", "poor", "unacceptable", "disappointing", "mediocre"]
    blocks = ["A", "B", "C", "D", "E", "101", "204", "302"]

    records = []
    for idx, category in enumerate(CATEGORIES):
        target_count = rows_per_category + (1 if idx < remainder else 0)
        templates = CATEGORY_TEMPLATES[category]

        for _ in range(target_count):
            tpl = random.choice(templates)
            text = tpl.format(
                block=random.choice(blocks),
                qual_pos=random.choice(qual_pos_list),
                qual_neg=random.choice(qual_neg_list)
            )
            records.append({"feedback_text": text, "category": category})

    # Shuffle deterministically
    random.shuffle(records)
    return records


def generate_sample_feedback_dataset(total_rows=300, pii_fraction=0.40):
    """Generate sample_feedback.csv adhering to the Section 5 data contract."""
    start_date = datetime(2026, 4, 1)
    end_date = datetime(2026, 9, 30)
    day_span = (end_date - start_date).days

    records = []
    num_pii_rows = int(total_rows * pii_fraction)

    # Determine which indices will have embedded PII
    pii_indices = set(random.sample(range(total_rows), num_pii_rows))

    for i in range(total_rows):
        feedback_id = f"FB-2026-{i+1:04d}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        clean_email_name = f"{first_name.lower()}.{last_name.lower()}{random.randint(10, 99)}"
        email = f"{clean_email_name}@{random.choice(EMAIL_DOMAINS)}"

        # Valid 10-digit Indian phone number
        phone_digits = f"{random.choice(['9', '8', '7', '6'])}{random.randint(100000000, 999999999)}"
        phone = f"+91 {phone_digits}"

        department = random.choice(DEPARTMENTS)
        year = random.choice(YEARS)

        # Spread feedback_date across 6 months
        rand_days = random.randint(0, day_span)
        feedback_date = (start_date + timedelta(days=rand_days)).strftime("%Y-%m-%d")

        # Pick base feedback category and template
        category = random.choice(CATEGORIES)
        tpl = random.choice(CATEGORY_TEMPLATES[category])
        base_text = tpl.format(
            block=random.choice(["A", "B", "C", "D", "101", "204"]),
            qual_pos="satisfactory",
            qual_neg="poor"
        )

        has_pii = i in pii_indices

        if has_pii:
            pii_type = random.choice(["intro", "contact", "signature", "hostel_address", "phone_only"])
            if pii_type == "intro":
                feedback_text = (
                    f"I am {full_name} from {department} year {year}. "
                    f"{base_text} Please resolve this issue soon."
                )
            elif pii_type == "contact":
                feedback_text = (
                    f"{base_text} For further clarification, kindly contact me at {email} "
                    f"or call on {phone_digits}."
                )
            elif pii_type == "signature":
                feedback_text = (
                    f"{base_text} Sincerely, {full_name}, Phone: {phone}."
                )
            elif pii_type == "hostel_address":
                feedback_text = (
                    f"My name is {full_name} staying in Room {random.randint(101, 420)}, Block B Hostel. "
                    f"{base_text} Reach me at {email}."
                )
            else: # phone_only
                feedback_text = (
                    f"{base_text} You can reach student {first_name} at +91-{phone_digits}."
                )
        else:
            feedback_text = base_text

        records.append({
            "feedback_id": feedback_id,
            "student_name": full_name,
            "email": email,
            "phone": phone,
            "department": department,
            "year": year,
            "feedback_text": feedback_text,
            "feedback_date": feedback_date
        })

    return records


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    train_path = os.path.join(script_dir, "train_labeled.csv")
    sample_path = os.path.join(script_dir, "sample_feedback.csv")

    print(f"Generating synthetic datasets using random seed {RANDOM_SEED}...")

    # 1. Generate train_labeled.csv (600 rows)
    train_data = generate_train_dataset(total_rows=600)
    with open(train_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["feedback_text", "category"])
        writer.writeheader()
        writer.writerows(train_data)

    # Verify counts
    category_counts = {}
    for row in train_data:
        cat = row["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\n[+] train_labeled.csv generated (Total rows: 600)")
    print("Class distribution:")
    for cat, count in sorted(category_counts.items()):
        print(f"  - {cat:15s}: {count} rows")
        assert count >= 50, f"Class {cat} has fewer than 50 rows!"

    # 2. Generate sample_feedback.csv (300 rows)
    sample_data = generate_sample_feedback_dataset(total_rows=300, pii_fraction=0.40)
    with open(sample_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "feedback_id", "student_name", "email", "phone",
            "department", "year", "feedback_text", "feedback_date"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)

    # Analyze sample data
    dept_counts = {}
    dates = []
    embedded_pii_count = 0
    for row in sample_data:
        dept = row["department"]
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
        dates.append(row["feedback_date"])
        # Check if text contains names, emails, or phone indicators
        txt = row["feedback_text"]
        if "@" in txt or any(digit in txt for digit in ["+91", "Phone:", "Room "]) or row["student_name"] in txt:
            embedded_pii_count += 1

    print(f"\n[+] sample_feedback.csv generated (Total rows: {len(sample_data)})")
    print(f"Rows containing embedded PII in feedback_text: {embedded_pii_count} ({embedded_pii_count/len(sample_data)*100:.1f}%)")
    print(f"Date range: {min(dates)} to {max(dates)}")
    print("Department distribution:")
    for dept, count in sorted(dept_counts.items()):
        print(f"  - {dept:6s}: {count} rows")

    print("\nAcceptance verification: SUCCESS.")


if __name__ == "__main__":
    main()
