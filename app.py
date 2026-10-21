import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Mubarak Mutual Fund", page_icon="💰", layout="wide")

# Title and Header
st.title("💰 Mubarak Mutual Emergency Solidarity Fund")
st.markdown("### Ledger Management & Visibility Dashboard")

# --- USER AUTHENTICATION / INTERFACE MODE ---
st.sidebar.header("User Access Mode")
user_role = st.sidebar.radio("Identify your role:", ["Member (View Only)", "Abu Bakar / Khawar (Admin Mode)"])

# --- CORE MEMBER LIST ---
members_list = [
    "Waheed (CMEA)", "Khawar Rashid (MEA(M)-III)", "Sajjad Ali (MEA(M)-IV)", 
    "Tahir Naveed Anjum (MEA(M)-IV)", "Kamran Ahmed Pannu (MEA(M)-IV)", 
    "Ali Hassan (MEA(H)-IV)", "Muhammad Farhan (MEA(M)-IV)", 
    "RANA GHULAM ALI (MEA(M)-IV)", "Ehsan Zaheer (LMEM(M))", "Abu Bakar (LMEM(M))"
]

# Initialize session state variables if they don't exist
if "seed_capital" not in st.session_state:
    st.session_state.seed_capital = 50000
    st.session_state.seed_returned = False

if "ledger_df" not in st.session_state:
    data = {
        "Member Name": members_list,
        "Total Contributions Paid (₹)": [0] * 10,
        "Active Member Loan Balance (₹)": [0] * 10,
        "Next Member Repayment Due (₹)": [0] * 10,
        "Status": ["Active"] * 10
    }
    st.session_state.ledger_df = pd.DataFrame(data)

# Initialize separate tracking database for Non-Member Loans
if "external_loans_df" not in st.session_state:
    ext_data = {
        "Non-Member Name": [],
        "Sponsoring Member (Guarantor)": [],
        "Original Loan Amount (₹)": [],
        "Remaining Balance (₹)": [],
        "Mandatory Monthly Payment (₹)": []
    }
    st.session_state.external_loans_df = pd.DataFrame(ext_data)

# --- CALCULATING OVERALL METRICS ---
base_collections = st.session_state.ledger_df["Total Contributions Paid (₹)"].sum()
outstanding_member_loans = st.session_state.ledger_df["Active Member Loan Balance (₹)"].sum()
outstanding_ext_loans = st.session_state.external_loans_df["Remaining Balance (₹)"].sum() if not st.session_state.external_loans_df.empty else 0

# Business logic for Seed Capital Return
if base_collections >= 100000 and not st.session_state.seed_returned:
    st.session_state.seed_capital = 0
    st.session_state.seed_returned = True

current_pool = base_collections + (50000 if not st.session_state.seed_returned else 0) - outstanding_member_loans - outstanding_ext_loans

# --- METRIC DISPLAY DASHBOARD ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Available Cash Pool", value=f"₹{current_pool:,}")
with col2:
    st.metric(label="Total Member Deposits", value=f"₹{base_collections:,}")
with col3:
    st.metric(label="Outstanding External Loans", value=f"₹{int(outstanding_ext_loans):,}")
with col4:
    status_text = "Returned to Khawar/Ali" if st.session_state.seed_returned else "Active Pool Support"
    st.metric(label="Seed Capital Balance", value=f"₹{st.session_state.seed_capital:,}", delta=status_text)

st.markdown("---")

# --- ADMIN PANEL FOR ABU BAKAR ---
if user_role == "Abu Bakar / Khawar (Admin Mode)":
    st.subheader("🛠️ Treasurer Admin Controls (Abu Bakar View)")
    
    admin_action = st.selectbox("Select Action:", ["Record Monthly Payment / Repayment", "Issue New Member Loan", "Issue External Non-Member Loan"])
    
    if admin_action == "Record Monthly Payment / Repayment":
        pay_category = st.radio("Who is paying?", ["Internal Group Member", "External Non-Member Loan Payment"])
        
        if pay_category == "Internal Group Member":
            with st.form("payment_form"):
                selected_member = st.selectbox("Select Member:", members_list)
                pay_type = st.radio("Payment Type", ["Standard Contribution Only (₹1,000)", "Contribution + Loan Repayment"])
                extra_amount = st.number_input("Enter Loan Repayment Amount if applicable (₹):", min_value=0, step=500)
                
                submit_payment = st.form_submit_button("Submit Member Payment Entry")
                if submit_payment:
                    idx = st.session_state.ledger_df[st.session_state.ledger_df["Member Name"] == selected_member].index
                    st.session_state.ledger_df.at[idx, "Total Contributions Paid (₹)"] += 1000
                    if pay_type == "Contribution + Loan Repayment" and extra_amount > 0:
                        current_loan = st.session_state.ledger_df.at[idx, "Active Member Loan Balance (₹)"]
                        st.session_state.ledger_df.at[idx, "Active Member Loan Balance (₹)"] = max(0, current_loan - extra_amount)
                    st.success(f"Successfully recorded transaction for {selected_member}!")
                    st.sidebar.info("Page updated.")
                    st.rerun()
                    
        elif pay_category == "External Non-Member Loan Payment":
            if st.session_state.external_loans_df.empty:
                st.warning("No active non-member loans exist to record payments against.")
            else:
                with st.form("ext_payment_form"):
                    selected_ext = st.selectbox("Select Non-Member Borrower:", st.session_state.external_loans_df["Non-Member Name"].tolist())
                    recovered_amt = st.number_input("Amount Received (Min ₹5,000 per SOP):", min_value=1000, step=500)
                    
                    submit_ext_pay = st.form_submit_button("Submit External Payment")
                    if submit_ext_pay:
                        idx = st.session_state.external_loans_df[st.session_state.external_loans_df["Non-Member Name"] == selected_ext].index
                        current_bal = st.session_state.external_loans_df.at[idx, "Remaining Balance (₹)"].values[0]
                        new_bal = max(0, current_bal - recovered_amt)
                        st.session_state.external_loans_df.at[idx, "Remaining Balance (₹)"] = new_bal
                        
                        # Clean out completed loans
                        if new_bal == 0:
                            st.session_state.external_loans_df = st.session_state.external_loans_df[st.session_state.external_loans_df["Non-Member Name"] != selected_ext]
                            st.success(f"Loan fully cleared by {selected_ext}!")
                        else:
                            st.success(f"Recorded ₹{recovered_amt:,} paid by {selected_ext}. Remaining: ₹{new_bal:,}")
                        st.rerun()

    elif admin_action == "Issue New Member Loan":
        with st.form("loan_form"):
            borrower = st.selectbox("Select Borrowing Member:", members_list)
            loan_amount = st.number_input("Loan Amount (₹):", min_value=1000, max_value=50000, step=1000)
            
            submit_loan = st.form_submit_button("Approve & Disburse Loan")
            if submit_loan:
                if loan_amount > current_pool:
                    st.error("Insufficient funds in cash pool to cover this loan amount!")
                else:
                    idx = st.session_state.ledger_df[st.session_state.ledger_df["Member Name"] == borrower].index
                    st.session_state.ledger_df.at[idx, "Active Member Loan Balance (₹)"] += loan_amount
                    
                    if loan_amount > 20000:
                        st.session_state.ledger_df.at[idx, "Next Member Repayment Due (₹)"] = 3000
                    else:
                        st.session_state.ledger_df.at[idx, "Next Member Repayment Due (₹)"] = 2000
                        
                    st.success(f"Loan of ₹{loan_amount:,} assigned to {borrower}. Next month is set as an empty grace month.")
                    st.rerun()

    elif admin_action == "Issue External Non-Member Loan":
        with st.form("ext_loan_form"):
            ext_borrower = st.text_input("Enter Non-Member Full Name:")
            sponsor = st.selectbox("Select Sponsoring Member (Guarantor liable for 100% Return):", members_list)
            ext_loan_amount = st.number_input("Loan Amount (Max ₹15,000 per SOP):", min_value=1000, max_value=15000, step=1000)
            
            submit_ext_loan = st.form_submit_button("Issue Non-Member Loan")
            if submit_ext_loan:
                if ext_loan_amount > current_pool:
                    st.error("Insufficient funds in cash pool!")
                elif not ext_borrower.strip():
                    st.error("Please enter a valid name for the non-member borrower.")
                else:
                    new_row = {
                        "Non-Member Name": ext_borrower,
                        "Sponsoring Member (Guarantor)": sponsor,
                        "Original Loan Amount (₹)": ext_loan_amount,
                        "Remaining Balance (₹)": ext_loan_amount,
                        "Mandatory Monthly Payment (₹)": 5000
                    }
                    st.session_state.external_loans_df = pd.concat([st.session_state.external_loans_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"External loan of ₹{ext_loan_amount:,} issued to {ext_borrower}. Sponsored by {sponsor}.")
                    st.rerun()

# --- PUBLIC LEDGER VIEWS FOR ALL MEMBERS ---
st.subheader("📋 Live Group Ledger Accounts")
st.dataframe(st.session_state.ledger_df, use_container_width=True, hide_index=True)

st.subheader("👤 Active Non-Member External Loans")
if st.session_state.external_loans_df.empty:
    st.info("No active external loans are currently drawn from the fund.")
else:
    st.dataframe(st.session_state.external_loans_df, use_container_width=True, hide_index=True)

st.info("⚠️ Liability reminder: Sponsoring members carry full out-of-pocket accountability if an external borrower misses their ₹5,000 monthly obligation.")
