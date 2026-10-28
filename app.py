import pandas as pd
import streamlit as st

st.set_page_config(page_title="Payment Reconciliation", page_icon="↔", layout="wide")
INTERNAL_SAMPLE = pd.DataFrame([
    {"reference":"PAY-1001","amount":49.99,"date":"2026-10-20"},
    {"reference":"PAY-1002","amount":120.00,"date":"2026-10-20"},
    {"reference":"PAY-1003","amount":15.50,"date":"2026-10-21"},
    {"reference":"PAY-1004","amount":230.00,"date":"2026-10-21"},
    {"reference":"PAY-1005","amount":72.25,"date":"2026-10-22"},
])
PARTNER_SAMPLE = pd.DataFrame([
    {"reference":"PAY-1001","amount":49.99,"date":"2026-10-20"},
    {"reference":"PAY-1002","amount":119.00,"date":"2026-10-20"},
    {"reference":"PAY-1003","amount":15.50,"date":"2026-10-21"},
    {"reference":"PAY-1006","amount":18.00,"date":"2026-10-22"},
    {"reference":"PAY-1005","amount":72.25,"date":"2026-10-22"},
])
REQUIRED = {"reference", "amount", "date"}

def load_csv(upload, sample):
    return pd.read_csv(upload) if upload is not None else sample.copy()

def validate(df, label):
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"{label} CSV is missing columns: {', '.join(sorted(missing))}")
    df = df.copy()
    df["reference"] = df["reference"].astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").round(2)
    df["date"] = df["date"].astype(str)
    if df["reference"].eq("").any() or df["amount"].isna().any():
        raise ValueError(f"{label} has blank references or non-numeric amounts.")
    if df["reference"].duplicated().any():
        duplicates = df.loc[df["reference"].duplicated(), "reference"].tolist()
        raise ValueError(f"{label} contains duplicate references: {', '.join(duplicates[:5])}")
    return df

def reconcile(internal, partner):
    left = internal.rename(columns={"amount":"internal_amount","date":"internal_date"})
    right = partner.rename(columns={"amount":"partner_amount","date":"partner_date"})
    merged = left.merge(right, on="reference", how="outer", indicator=True)
    def classify(row):
        if row["_merge"] == "left_only": return "Missing from partner"
        if row["_merge"] == "right_only": return "Missing internally"
        if round(row["internal_amount"], 2) != round(row["partner_amount"], 2): return "Amount mismatch"
        return "Matched"
    merged["result"] = merged.apply(classify, axis=1)
    return merged.drop(columns=["_merge"]).sort_values(["result", "reference"])

st.markdown("<style>.block-container{padding-top:2rem;max-width:1400px}[data-testid='stMetric']{background:#f6f8fb;border:1px solid #e3e8f0;padding:16px;border-radius:12px}</style>", unsafe_allow_html=True)
st.title("↔ Payment Reconciliation Analytics")
st.caption("Compare internal payment records with bank or partner remittances.")
st.warning("Demo tool only. Sample data is fictional. Do not upload confidential customer or financial records to a public app.")
with st.sidebar:
    st.header("Data sources")
    internal_file = st.file_uploader("Internal payments CSV", type=["csv"], key="internal")
    partner_file = st.file_uploader("Partner remittance CSV", type=["csv"], key="partner")
    st.caption("Leave uploads empty to use the included sample datasets.")
    st.markdown("**Required columns**")
    st.code("reference, amount, date", language="text")
try:
    internal = validate(load_csv(internal_file, INTERNAL_SAMPLE), "Internal")
    partner = validate(load_csv(partner_file, PARTNER_SAMPLE), "Partner")
    results = reconcile(internal, partner)
except Exception as exc:
    st.error(str(exc))
    st.stop()
counts = results["result"].value_counts()
matched = int(counts.get("Matched", 0))
exceptions = len(results) - matched
c1, c2, c3, c4 = st.columns(4)
c1.metric("Internal records", f"{len(internal):,}")
c2.metric("Partner records", f"{len(partner):,}")
c3.metric("Matched", f"{matched:,}")
c4.metric("Exceptions", f"{exceptions:,}")
st.subheader("Reconciliation overview")
left, right = st.columns(2)
left.metric("Internal total", f"€{internal['amount'].sum():,.2f}")
right.metric("Partner total", f"€{partner['amount'].sum():,.2f}", delta=f"€{partner['amount'].sum()-internal['amount'].sum():,.2f} difference")
st.subheader("Results")
options = ["All", "Matched", "Missing from partner", "Missing internally", "Amount mismatch"]
selected = st.selectbox("Filter results", options)
view = results if selected == "All" else results[results["result"] == selected]
st.dataframe(view, use_container_width=True, hide_index=True)
st.download_button("Download current results as CSV", data=view.to_csv(index=False).encode("utf-8"),
                   file_name="reconciliation_results.csv", mime="text/csv")
st.subheader("Exception summary")
if exceptions:
    st.dataframe(results[results["result"] != "Matched"], use_container_width=True, hide_index=True)
else:
    st.success("No reconciliation exceptions found.")
