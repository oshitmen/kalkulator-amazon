import streamlit as st

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Amazon DE - MalTec", page_icon="🛍️", layout="centered")

st.title("🛍️ Kalkulator Cen Amazon DE")
st.write("Wpisz koszty i oczekiwany zysk, aby wyliczyć sugerowaną cenę sprzedaży w Euro dla MFN i FBA.")

st.divider()

# Sekcja wprowadzania danych
st.subheader("1. Podstawowe dane")
col1, col2 = st.columns(2)

with col1:
    cost_pln = st.number_input("Koszt zakupu + fracht (PLN netto)", value=120.0, step=5.0)
    target_profit_pln = st.number_input("Oczekiwany zysk netto (PLN)", value=40.0, step=5.0)
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

# Logika przeliczania
def calc_price(logistics_eur):
    cost_eur = cost_pln / rate
    profit_eur = target_profit_pln / rate
    net_mult = (1.0 - (fee_pct/100) - (ppc_pct/100)) / (1.0 + (vat_pct/100))
    price = (cost_eur + logistics_eur + profit_eur) / net_mult
    vat = price - (price / (1.0 + (vat_pct/100)))
    fee = price * (fee_pct/100)
    ppc = price * (ppc_pct/100)
    return price, fee, ppc, vat

price_mfn, fee_mfn, ppc_mfn, vat_mfn = calc_price(mfn_shipping)
price_fba, fee_fba, ppc_fba, vat_fba = calc_price(fba_logistics)

st.divider()
st.subheader("📊 Wynik Kalkulacji")

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.info("### Model MFN (Własny)")
    st.markdown(f"Sugerowana cena: **€{price_mfn:.2f}**")
    st.caption(f"• Prowizja Amazon: €{fee_mfn:.2f}")
    st.caption(f"• Reklamy PPC: €{ppc_mfn:.2f}")
    st.caption(f"• Podatek VAT: €{vat_mfn:.2f}")

with res_col2:
    st.success("### Model FBA (Amazon)")
    st.markdown(f"Sugerowana cena: **€{price_fba:.2f}**")
    st.caption(f"• Prowizja Amazon: €{fee_fba:.2f}")
    st.caption(f"• Reklamy PPC: €{ppc_fba:.2f}")
    st.caption(f"• Podatek VAT: €{vat_fba:.2f}")

if fba_logistics < mfn_shipping:
    st.success("💡 **Wniosek:** Model FBA jest tańszy logistycznie! Możesz dać niższą cenę wyjściową lub zarobić więcej.")
else:
    st.warning("💡 **Wniosek:** Model MFN wychodzi taniej na logistyce dla tego produktu.")
