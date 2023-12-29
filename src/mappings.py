def acceptance_brand_to_card_brand(brand: str) -> str:
    if brand == "MCC":
        return "MASTERCARD"
    if brand == "DMC":
        return "DEBIT MASTERCARD"
    if brand == "M":
        return "MAESTRO"
    if brand == "CIR":
        return "CIRRUS"
    if brand == "PVL":
        return "PRIVATE LABEL"
    return "UNKNOWN"
