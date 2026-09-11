import re

def extract_value(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None

def parse_medical_report(text):
    data = {}

    data["glucose"] = extract_value(
        [r"glucose[:\s]+(\d+\.?\d*)", r"blood\s*sugar[:\s]+(\d+\.?\d*)"],
        text
    )

    data["blood_pressure"] = extract_value(
        [r"blood\s*pressure[:\s]+(\d+)", r"bp[:\s]+(\d+)"],
        text
    )

    data["chol"] = extract_value(
        [r"cholesterol[:\s]+(\d+\.?\d*)"],
        text
    )

    data["bmi"] = extract_value(
        [r"bmi[:\s]+(\d+\.?\d*)"],
        text
    )

    data["age"] = extract_value(
        [r"age[:\s]+(\d+)"],
        text
    )

    return data
