# Payment Reconciliation Analytics

Streamlit data app comparing internal payment records with bank/partner remittance exports, flagging matched and unmatched transactions, and exporting exception reports.

## Features
- Upload two CSV files or use fictional sample data
- Match by reference and amount
- Summarize matched, missing, and amount-mismatch records
- Download results as CSV
- Input validation

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## CSV format
Both files need `reference`, `amount`, and `date` columns. Amounts must be numeric and in the same currency. Duplicate references are rejected. The app uses deterministic matching and does not infer that unrelated transactions are equivalent.

Sample data is fictional. Do not upload confidential financial or personal data to a public deployment.
