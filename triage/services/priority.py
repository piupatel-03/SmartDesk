def get_priority(subject, description,category):
    text = f"{subject} {description}".lower()

    if "payment failed" in text:
        return "High"

    if "urgent" in text :
        return "High"

    if "not working" in text:
        return "High"

    if "refund" in text:
        return "High"

    if category in ["Payment", "Refund"]:
        return "Medium"

    return "Low"

