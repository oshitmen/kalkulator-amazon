import streamlit as st

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Amazon DE - MalTec", page_icon="🛍️", layout="centered")

st.title("🛍️ Kalkulator Cen Amazon DE")
st.write("Wpisz koszty i oczekiwaną marżę netto, aby wyliczyć sugerowaną cenę sprzedaży w Euro dla MFN i FBA.")

st.divider()

# Sekcja wprowadzania danych
st.subheader("1. Podstawowe dane")
col1, col2 = st.columns(2)

with col1:
    cost_pln = st.number_input("Koszt zakupu + fracht (PLN netto)", value=120.0, step=5.0)
    target_margin_pct = st.number_input("Oczekiwana marża netto (%)", value=20.0, step=1.0)
    rate = st.number_input("Kurs EUR/PLN", value=4.30, step=0.01)

with col2:
    fee_pct = st.number_input("Prowizja Amazon (%)", value=15.0, step=0.5)
    ppc_pct = st.number_input("Budżet na reklamy PPC (%)", value=10.0, step=0.5)
    vat_pct = st.number_input("Stawka VAT w DE (%)", value=19.0, step=1.0)

st.subheader("2. Koszty logistyki")
col3, col4 = st.columns(2)

with col3:
    mfn_shipping = st.number_input("Koszt własnego kuriera MFN (€)", value=6.50, step=0.10)

with col4:
    fba_logistics = st.number_input("Opłaty FBA (Fulfilment + Storage) (€)", value=4.95, step=0.10)

# Logika przeliczania z oczekiwaną marżą netto
def calc_price(logistics_eur):
    cost_eur = cost_pln / rate
    fee_dec = fee_pct / 100.0
    ppc_dec = ppc_pct / 100.0
    vat_dec = vat_pct / 100.0
    margin_dec = target_margin_pct / 100.0

    # Przelicznik uwzględniający marżę netto, prowizję, PPC oraz VAT
    net_multiplier = (1.0 - fee_dec - ppc_dec - margin_dec) / (1.0 + vat_dec)
    
    # Wyliczenie ceny brutto w EUR
    if net_multiplier > 0:
        price = (cost_eur + logistics_eur) / net_multiplier
    else:
        price = 0.0

    vat = price - (price / (1.0 + vat_dec)) if price > 0 else 0.0
    fee = price * fee_dec
    ppc = price * ppc_dec
    
    # Wyliczenie realnego zysku kwotowego w PLN do podglądu
    net_sales_eur = price / (1.0 + vat_dec)
    profit_eur = net_sales_eur * margin_dec
    profit_pln = profit_eur * rate

    return price, fee, ppc, vat, profit_pln

price_mfn, fee_mfn, ppc_mfn, vat_mfn, profit_mfn_pln = calc_price(mfn_shipping)
price_fba, fee_fba, ppc_fba, vat_fba, profit_fba_pln = calc_price(fba_logistics)

st.divider()
st.subheader("📊 Wynik Kalkulacji")

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.info("### Model MFN (Własny)")
    st.markdown(f"Sugerowana cena: **€{price_mfn:.2f}**")
    st.caption(f"• Zysk kwotowy: **{profit_mfn_pln:.2f} PLN**")
    st.caption(f"• Prowizja Amazon: €{fee_mfn:.2f}")
    st.caption(f"• Reklamy PPC: €{ppc_mfn:.2f}")
    st.caption(f"• Podatek VAT: €{vat_mfn:.2f}")

with res_col2:
    st.success("### Model FBA (Amazon)")
    st.markdown(f"Sugerowana cena: **€{price_fba:.2f}**")
    st.caption(f"• Zysk kwotowy: **{profit_fba_pln:.2f} PLN**")
    st.caption(f"• Prowizja Amazon: €{fee_fba:.2f}")
    st.caption(f"• Reklamy PPC: €{ppc_fba:.2f}")
    st.caption(f"• Podatek VAT: €{vat_fba:.2f}")

if fba_logistics < mfn_shipping:
    st.success("💡 **Wniosek:** Model FBA jest tańszy logistycznie! Pozwala uzyskać założoną marżę przy niższej cenie wyjściowej.")
else:
    st.warning("💡 **Wniosek:** Model MFN wychodzi taniej na logistyce dla tego produktu.")
