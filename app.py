import streamlit as st
import pandas as pd
import gspread
from datetime import date

# ==============================================================================
# BLOCK 1: PAGE CONFIGURATION & INTERFACE SETUP
# Configure Streamlit page layout and title
# ==============================================================================
st.set_page_config(page_title="Personal Finance Manager", layout="wide")
st.title("💸 Personal Finance Manager")

# ==============================================================================
# BLOCK 2: CONNECT TO GOOGLE SHEETS VIA GSPREAD
# Load Google Cloud credentials from Streamlit Secrets and connect to your Google Drive spreadsheet
# ==============================================================================
@st.cache_resource
def get_google_sheet():
    # Use service account credentials stored in Streamlit secrets
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    
    # Open the Google Sheet by its title in Google Drive
    spreadsheet = gc.open("Gestión de Finanzas Personales")
    return spreadsheet

try:
    spreadsheet = get_google_sheet()
    sheet_trans = spreadsheet.worksheet("Transacciones")
    sheet_cat = spreadsheet.worksheet("Categorías")
    st.sidebar.success("Connected to Google Drive Sheet!")
except Exception as e:
    st.sidebar.error("Failed to connect to Google Sheets. Check your credentials.")
    st.stop()

# ==============================================================================
# BLOCK 3: FETCH CATEGORIES AND PAYMENT METHODS FROM SHEET
# Dynamically pull the drop-down lists from the "Categorías" tab
# ==============================================================================
try:
    cat_data = sheet_cat.get_all_values()
    # Read categories from column A (skipping header)
    CATEGORIES = [row[0] for row in cat_data[1:] if len(row) > 0 and row[0] != ""]
    # Read payment methods from column B (skipping header)
    PAYMENT_METHODS = [row[1] for row in cat_data[1:] if len(row) > 1 and row[1] != ""]
except Exception:
    # Fallback lists matching your Google Sheet structure
    CATEGORIES = ["Alimentación", "Transporte", "Servicios", "Gastos casa", "comer por fuera", "Suscripciones/Débitos Automáticos", "salud"]
    PAYMENT_METHODS = ["Tarjeta de Crédito cba 1", "Tarjeta de Crédito cba 2", "Tarjeta de Crédito nab", "Tarjeta de Débito", "Efectivo", "retiro casa"]

# ==============================================================================
# BLOCK 4: NAVIGATION TABS SETUP
# Define tabs for Daily Logging, File Uploading, and Viewing Data
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["📝 Daily Entry", "📂 Import Bank Statement", "📊 View Transactions"])

# ==============================================================================
# BLOCK 5: DAILY MANUAL ENTRY FORM
# Form to input single transactions and append them to the Google Sheet
# ==============================================================================
with tab1:
    st.subheader("Log a New Expense")
    with st.form("manual_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        # Input fields matching the Google Sheet columns
        entry_date = col1.date_input("Date", value=date.today())
        amount = col2.number_input("Amount", min_value=0.0, format="%.2f")
        merchant = col1.text_input("Merchant / Location")
        description = col2.text_input("Description")
        payment_method = col1.selectbox("Payment Method", PAYMENT_METHODS)
        category = col2.selectbox("Category", CATEGORIES)
        
        submit_button = st.form_submit_button("Save Expense")
        
        if submit_button:
            # Prepare row values in exact order:
            # [Fecha, Monto, Comercio / Lugar, Descripción, Método de Pago, Categoría, Origen (Manual / Banco)]
            new_row = [
                entry_date.strftime("%Y-%m-%d"),
                amount,
                merchant,
                description,
                payment_method,
                category,
                "Manual"
            ]
            
            # Append row to the "Transacciones" worksheet
            sheet_trans.append_row(new_row)
            st.success("Expense successfully saved to Google Sheets!")

# ==============================================================================
# BLOCK 6: IMPORT BANK STATEMENTS (EXCEL / CSV)
# Upload CSV or Excel bank files and save entries directly to Google Sheets
# ==============================================================================
with tab2:
    st.subheader("Upload Bank Statement (CSV / Excel)")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_bank = pd.read_csv(uploaded_file)
            else:
                df_bank = pd.read_excel(uploaded_file)
            
            st.write("File Preview:", df_bank.head())
            st.info("Map your bank file columns to match your Google Sheet structure before saving.")
        except Exception as err:
            st.error(f"Error reading file: {err}")

# ==============================================================================
# BLOCK 7: VIEW ALL TRANSACTIONS
# Fetch all current records from the Google Sheet and display as a DataFrame
# ==============================================================================
with tab3:
    st.subheader("Transaction History (Google Drive)")
    records = sheet_trans.get_all_records()
    df_transactions = pd.DataFrame(records)
    st.dataframe(df_transactions, use_container_width=True)