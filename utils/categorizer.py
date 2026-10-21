def auto_categorize_expense(merchant_name):
    name = merchant_name.lower() if merchant_name else ""
    if any(k in name for k in ["seed", "fertilizer", "kisan", "crop", "pesticide", "inputs"]):
        return "Agri Inputs", 0.95
    elif any(k in name for k in ["textile", "inventory", "shop", "commercial", "electricity", "bill"]):
        return "Business Shop", 0.92
    elif any(k in name for k in ["emi", "loan", "debt", "sbi", "interest", "bank"]):
        return "Loans & Debt", 0.94
    else:
        return "Household", 0.70