import re
from datetime import datetime
from fastapi import APIRouter
from ..schemas.transaction_schema import SmsParseRequest, SmsParseResponse

router = APIRouter(prefix="/sms", tags=["SMS Money Extractor"])

def detect_bank_name(text: str) -> str:
    lower = text.lower()
    if "icici" in lower:
        return "ICICI Bank"
    if "hdfc" in lower:
        return "HDFC Bank"
    if "sbi" in lower or "state bank" in lower:
        return "SBI"
    if "axis" in lower:
        return "Axis Bank"
    if "kotak" in lower:
        return "Kotak Bank"
    if "paytm" in lower:
        return "Paytm Bank"
    if "indusind" in lower or "indus" in lower:
        return "IndusInd Bank"
    if "pnb" in lower or "punjab" in lower:
        return "PNB"
    if "bob" in lower or "baroda" in lower:
        return "Bank of Baroda"
    if "canara" in lower:
        return "Canara Bank"
    if "yes bank" in lower or "yesbk" in lower:
        return "Yes Bank"
    if "idfc" in lower:
        return "IDFC First"
    if "union" in lower:
        return "Union Bank"
    if "federal" in lower:
        return "Federal Bank"
    if "rbl" in lower:
        return "RBL Bank"
    return "Bank Account"

def detect_payment_method(text: str) -> str:
    lower = text.lower()
    if "upi" in lower or "vpa" in lower or "gpay" in lower or "phonepe" in lower or "paytm" in lower:
        return "UPI"
    if "debit card" in lower or ("card" in lower and "debit" in lower):
        return "Debit Card"
    if "credit card" in lower or ("card" in lower and "credit" in lower):
        return "Credit Card"
    if "atm" in lower or "cash withdrawal" in lower or "withdrawn" in lower:
        return "ATM"
    if "imps" in lower:
        return "IMPS"
    if "neft" in lower:
        return "NEFT"
    if "rtgs" in lower:
        return "RTGS"
    if "netbanking" in lower or "net banking" in lower or "transfer" in lower:
        return "Bank Transfer"
    return "Online"

def detect_category(text: str, tx_type: str, merchant: str) -> str:
    combined = f"{merchant} {text}".lower()
    if tx_type == "credit":
        if any(w in combined for w in ["salary", "payroll", "wages", "tech corp", "technologies", "corp"]):
            return "salary"
        if any(w in combined for w in ["refund", "cashback", "reversal"]):
            return "refunds"
        if any(w in combined for w in ["dividend", "interest", "mutual fund", "stocks", "zerodha", "groww"]):
            return "investment"
        if any(w in combined for w in ["freelance", "client", "invoice", "payout"]):
            return "freelance"
        return "transfer"

    # Debits
    if any(w in combined for w in ["swiggy", "zomato", "starbucks", "mcdonalds", "kfc", "dominos", "pizza", "restaurant", "cafe", "dine", "food", "eat"]):
        return "foodAndDining"
    if any(w in combined for w in ["blinkit", "zepto", "instamart", "bigbasket", "grocery", "supermarket", "dmart", "fruits", "vegetables"]):
        return "groceries"
    if any(w in combined for w in ["amazon", "flipkart", "myntra", "ajio", "shopping", "retail", "zara", "h&m", "purchase"]):
        return "shopping"
    if any(w in combined for w in ["uber", "ola", "rapido", "petrol", "fuel", "flight", "indigo", "air india", "makemytrip", "irctc", "train", "metro", "toll"]):
        return "travel"
    if any(w in combined for w in ["netflix", "spotify", "prime video", "hotstar", "movie", "bookmyshow", "cinema", "gaming", "pvr"]):
        return "entertainment"
    if any(w in combined for w in ["bescom", "electricity", "water", "broadband", "wifi", "airtel", "jio", "vi", "recharge", "utility", "gas", "bill"]):
        return "billsAndUtilities"
    if any(w in combined for w in ["pharmacy", "apollo", "1mg", "hospital", "doctor", "health", "clinic", "medplus"]):
        return "healthAndMedical"
    if any(w in combined for w in ["transfer", "sent", "vpa", "upi"]):
        return "transfer"
    return "other"

@router.post("/parse", response_model=SmsParseResponse)
def parse_sms_endpoint(req: SmsParseRequest):
    text = req.sms_text.strip()
    if not text:
        return SmsParseResponse(is_success=False, error_message="Empty SMS content")

    clean_text = text.replace("\n", " ").replace("\r", " ").strip()
    lower = clean_text.lower()

    # 1. Type
    is_debit = any(w in lower for w in [
        "debited", "debit", "dr.", "spent", "paid to", "payment of", "payment to",
        "withdrawn", "sent to", "transfer to", "transferred to", "purchase at", "used at", "deducted"
    ])
    is_credit = any(w in lower for w in [
        "credited", "credit of", "received", "deposited", "refund", "cashback", "salary", "cr.", "added to"
    ])
    
    if is_credit and not is_debit:
        tx_type = "credit"
    else:
        tx_type = "debit"

    # 2. Amount Extraction (Robust multi-pattern)
    amount = None

    # 2.1 Verb before amount
    verb_before_m = re.search(
        r'(?:debited|credited|spent|paid|transferred|withdrawn|sent|refunded|deducted|payment\s+of|txn\s+of|purchase\s+of|transfer\s+of)\s+(?:by|for|with|of|amount|amt|is)?\s*(?:(?:RS|INR|₹|\$|USD)\.?\s*)?([0-9,]+(?:\.[0-9]{1,2})?)(?:\s*/-)?',
        clean_text,
        re.IGNORECASE
    )
    if verb_before_m:
        try:
            val = float(verb_before_m.group(1).replace(",", ""))
            if val > 0:
                amount = val
        except ValueError:
            pass

    # 2.2 Amount before verb
    if not amount:
        verb_after_m = re.search(
            r'(?:(?:RS|INR|₹|\$|USD)\.?\s*)([0-9,]+(?:\.[0-9]{1,2})?)(?:\s*/-)?\s*(?:is|has been|was)?\s*(?:debited|credited|spent|paid|transferred|withdrawn|sent|refunded|deducted)',
            clean_text,
            re.IGNORECASE
        )
        if verb_after_m:
            try:
                val = float(verb_after_m.group(1).replace(",", ""))
                if val > 0:
                    amount = val
            except ValueError:
                pass

    # 2.3 Currency matches filtering out immediate balance context
    if not amount:
        for m in re.finditer(r'(?:(?:RS|INR|₹|\$|USD)\.?\s*)([0-9,]+(?:\.[0-9]{1,2})?)(?:\s*/-)?', clean_text, re.IGNORECASE):
            s_idx = m.start()
            e_idx = m.end()
            start_pref = max(0, s_idx - 30)
            imm_before = clean_text[start_pref:s_idx].lower()
            end_suff = min(len(clean_text), e_idx + 20)
            imm_after = clean_text[e_idx:end_suff].lower()

            is_balance = any(k in imm_before for k in ["bal", "limit", "avl", "available"]) or any(k in imm_after for k in ["balance", "bal"])
            if not is_balance:
                try:
                    val = float(m.group(1).replace(",", ""))
                    if val > 0:
                        amount = val
                        break
                except ValueError:
                    pass

    # 2.4 Fallback to any currency match
    if not amount:
        fallback_m = re.search(r'(?:(?:RS|INR|₹|\$|USD)\.?\s*)([0-9,]+(?:\.[0-9]{1,2})?)', clean_text, re.IGNORECASE)
        if fallback_m:
            try:
                val = float(fallback_m.group(1).replace(",", ""))
                if val > 0:
                    amount = val
            except ValueError:
                pass

    if not amount:
        return SmsParseResponse(is_success=False, type=tx_type, error_message="Could not extract valid amount from SMS")

    # 3. Bank & Account Information
    bank_name = detect_bank_name(clean_text)
    payment_method = detect_payment_method(clean_text)

    account_info = f"{bank_name} Account"
    acc_m = re.search(
        r'(?:Debit\s*Card|Credit\s*Card|Card|A/C|Acct|Account|A/c|SB\s*A/c)\s*(?:ending\s*(?:with|in)?|no\.?|is)?\s*([X\d*]{3,16}|\d{4})',
        clean_text,
        re.IGNORECASE
    )
    if acc_m:
        raw_digits = re.sub(r'[^0-9]', '', acc_m.group(1))
        ending = raw_digits[-4:] if len(raw_digits) >= 4 else raw_digits
        is_card = "card" in clean_text.lower()
        type_lbl = "Card" if is_card else "A/C"
        account_info = f"{bank_name} {type_lbl} XX{ending}"

    # 4. Merchant / Sender / Receiver
    merchant = None
    if tx_type == "credit":
        merchant_patterns = [
            r'(?:by|from|received from|credited by)\s+([A-Za-z0-9\s&.-]{3,35}?)(?=\s+(?:on|UPI|Ref|Avl|Bal|SALARY|using|dated|via|\.|$))',
            r'(?:towards|for)\s+([A-Za-z0-9\s&.-]{3,30}?)(?=\s+(?:on|UPI|Ref|Avl|Bal|using|dated|via|\.|$))',
            r'UPI/(?:[0-9]+/)?([A-Za-z0-9\s&.-]{3,24})',
        ]
    else:
        merchant_patterns = [
            r'(?:transaction\s+at|txn\s+at|spent\s+at|used\s+at)\s+([A-Za-z0-9\s&.-]{3,30}?)(?=\s+(?:on|UPI|Ref|Avl|Bal|using|dated|via|\.|$))',
            r'(?:transfer to|transferred to|vpa|paid to|sent to)\s+([A-Za-z0-9\s&.-]{3,30}?)(?=\s+(?:Ref|Bal|Avl|UPI|on|via|\.|$))',
            r'(?:to|at|towards|for)\s+([A-Za-z0-9\s&.-]{3,30}?)(?=\s+(?:on|UPI|Ref|Avl|Bal|using|dated|with|value|via|\.|$))',
            r'UPI/(?:[0-9]+/)?([A-Za-z0-9\s&.-]{3,24})',
        ]

    ignored_prefixes = ("your", "a/c", "acct", "account", "rs", "inr", "card", "transaction", "debit", "credit", "sb a/c", "bank")
    for pat in merchant_patterns:
        m = re.search(pat, clean_text, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            cand_clean = re.sub(r'^(UPI/|VPA/|to\s+|at\s+|towards\s+|from\s+|by\s+)', '', cand, flags=re.IGNORECASE).strip()
            if cand_clean and not cand_clean.lower().startswith(ignored_prefixes):
                merchant = cand_clean
                break

    if not merchant:
        merchant = "Debit Payment" if tx_type == "debit" else "Direct Credit"

    # 5. Reference / UTR ID
    ref_number = None
    ref_m = re.search(r'(?:UPI\s*Ref(?:\s*No)?|Txn\s*ID|Txn\s*No|Ref\s*No|Ref\s*ID|Reference|Ref|UTR)[:\s/]+([A-Za-z0-9]+)', clean_text, re.IGNORECASE)
    if ref_m:
        ref_number = ref_m.group(1)

    # 6. Available Balance After
    balance_after = None
    bal_m = re.search(r'(?:Avl Bal|Bal|Available Balance|Available limit|Avail Limit|Total Bal)[:\s]*(?:Rs\.?|INR|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)', clean_text, re.IGNORECASE)
    if bal_m:
        try:
            balance_after = float(bal_m.group(1).replace(",", ""))
        except ValueError:
            pass

    # 7. Category
    category = detect_category(clean_text, tx_type, merchant)

    return SmsParseResponse(
        is_success=True,
        amount=amount,
        type=tx_type,
        merchant=merchant,
        bank_name=bank_name,
        account_info=account_info,
        payment_method=payment_method,
        ref_number=ref_number,
        balance_after=balance_after,
        date=datetime.now(),
        category=category,
    )

