import streamlit as st
import requests

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Amazon & Wysyłek - MalTec", page_icon="🛍️", layout="centered")

# Cennik EuroHermes 2026 (Niemcy)
rates_eurohermes_de = {
    2.0: 3.93,
    5.0: 4.27,
    10.0: 4.55,
    15.0: 5.50,
    20.0: 5.83,
    25.0: 7.04,
    31.5: 7.61
}

def get_eurohermes_cost(weight_kg):
    if weight_kg <= 0:
        return 0.0, "Waga musi być większa niż 0 kg"
    for max_w in sorted(rates_eurohermes_de.keys()):
        if weight_kg <= max_w:
            return rates_eurohermes_de[max_w], f"EuroHermes do {max_w} kg"
    return 0.0, "Przekroczono limit 31.5 kg (paleta/wycena indyw.)"

# Funkcja pobierająca kurs EUR/PLN z NBP
@st.cache_data(ttl=3600)
def get_nbp_eur_rate():
    try:
        url = "https://api.nbp.pl/api/exchangerates/rates/a/eur/?format=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data["rates"][0]["mid"]
            effective_date = data["rates"][0]["effectiveDate"]
            return rate, effective_date
    except Exception:
        pass
    return 4.30, None

nbp_rate, nbp_date = get_nbp_eur_rate()

st.title("🛍️ Kompleksowy Kalkulator Amazon EU/PL")
st.write("Wpisz parametry produktu, wagę oraz koszty, aby wyliczyć optymalną cenę sprzedaży i koszty logistyki.")

st.divider()

# Sekcja 1: Rynek i Waluta
st.subheader("1. Wybór Rynku i Waluty Sprzedaży")
col_market, col_curr = st.columns(2)

with col_market:
    country = st.radio(
        "Wybierz docelowy rynek:",
        ["🇩🇪 Niemcy (19%)", "🇫🇷 Francja (20%)", "🇵🇱 Polska (23%)", "⚙️ Inny (Wpisz własny)"],
        index=0
    )

with col_curr:
    default_currency_index = 1 if "Polska" in country else 0
    currency = st.radio(
        "Waluta docelowej ceny sprzedaży:",
        ["EUR (€)", "PLN (zł)"],
        index=default_currency_index
    )

if "Niemcy" in country:
    vat_pct = 19.0
elif "Francja" in country:
    vat_pct = 20.0
elif "Polska" in country:
    vat_pct = 23.0
else:
    vat_pct = st.number_input("Wpisz własną stawkę VAT (%)", value=21.0, step=1.0)

symbol = "€" if "EUR" in currency else "zł"

st.divider()

# Sekcja 2: Dane produktu i koszty
st.subheader("2. Koszty zakupu, kurs i marża")
col1, col2 = st.columns(2)

with col1:
    cost_pln = st.number_input("Koszt zakupu + fracht (PLN netto)", value=120.0, step=5.0)
    target_margin_pct = st.number_input("Oczekiwana marża netto (%)", value=20.0, step=1.0)
    rate = st.number_input("Kurs EUR/PLN (Auto z NBP)", value=float(nbp_rate), step=0.01)
    if nbp_date:
        st.caption(f"🟢 Pobrano z NBP z dnia: {nbp_date} ({nbp_rate:.4f} PLN)")

with col2:
    # Wybór sposobu wprowadzania prowizji Amazon
    fee_type = st.radio(
        "Sposób wyliczania prowizji Amazon:",
        ["Procentowo (%)", f"Konkretna kwota ({symbol})"],
        horizontal=True
    )
    
    if fee_type == "Procentowo (%)":
        fee_pct = st.number_input("Prowizja Amazon (%)", value=15.0, step=0.5)
        fee_fixed_val = 0.0
    else:
        fee_pct = 0.0
        fee_fixed_val = st.number_input(f"Konkretna prowizja Amazon ({symbol})", value=3.50, step=0.5)

    ppc_pct = st.number_input("Budżet na reklamy PPC (%)", value=10.0, step=0.5)
    st.info(f"Podatek VAT: **{vat_pct:.0f}%** | Waluta ceny: **{currency}**")

st.divider()

# Sekcja 3: Logistyka i Cennik Kurierów
st.subheader("3. Koszty logistyki i kalkulator wagowy")

use_auto_mfn = st.checkbox("Automatycznie przelicz koszt MFN na podstawie wagi (EuroHermes DE)", value=True)

col3, col4 = st.columns(2)

with col3:
    if use_auto_mfn and "Niemcy" in country:
        weight_input = st.number_input("Waga paczki (kg)", value=4.5, step=0.5, min_value=0.1)
        calc_mfn_eur, msg_mfn = get_eurohermes_cost(weight_input)
        
        if "EUR" in currency:
            mfn_shipping = calc_mfn_eur
        else:
            mfn_shipping = calc_mfn_eur * rate
            
        st.caption(f"📦 Cennik EuroHermes: **{calc_mfn_eur:.2f} €** ({msg_mfn})")
    else:
        label_mfn = "Koszt własnego kuriera MFN (€)" if "EUR" in currency else "Koszt własnego kuriera MFN (zł)"
        default_mfn = 6.50 if "EUR" in currency else 25.00
        mfn_shipping = st.number_input(label_mfn, value=default_mfn, step=0.50)

with col4:
    label_fba = "Opłaty FBA (Fulfilment + Storage) (€)" if "EUR" in currency else "Opłaty FBA (Fulfilment + Storage) (zł)"
    default_fba = 4.95 if "EUR" in currency else 21.00
    fba_logistics = st.number_input(label_fba, value=default_fba, step=0.50)

# Logika przeliczania
def calc_price(logistics_val):
    if "EUR" in currency:
        cost_in_target_curr = cost_pln / rate
        logistics_in_target_curr = logistics_val
    else:
        cost_in_target_curr = cost_pln
        logistics_in_target_curr = logistics_val

    ppc_dec = ppc_pct / 100.0
    vat_dec = vat_pct / 100.0
    margin_dec = target_margin_pct / 100.0

    if fee_type == "Procentowo (%)":
        fee_dec = fee_pct / 100.0
        net_multiplier = (1.0 - fee_dec - ppc_dec - margin_dec) / (1.0 + vat_dec)
        
        if net_multiplier > 0:
            price = (cost_in_target_curr + logistics_in_target_curr) / net_multiplier
        else:
            price = 0.0
            
        fee = price * fee_dec
    else:
        # Kwotowa prowizja Amazon
        fee = fee_fixed_val
        net_multiplier = (1.0 - ppc_dec - margin_dec) / (1.0 + vat_dec)
        
        if net_multiplier > 0:
            price = (cost_in_target_curr + logistics_in_target_curr + fee) / net_multiplier
        else:
            price = 0.0

    vat = price - (price / (1.0 + vat_dec)) if price > 0 else 0.0
    ppc = price * ppc_dec
    
    net_sales = price / (1.0 + vat_dec)
    profit_in_target_curr = net_sales * margin_dec
    profit_pln = profit_in_target_curr * rate if "EUR" in currency else profit_in_target_curr

    return price, fee, ppc, vat, profit_pln

price_mfn, fee_mfn, ppc_mfn, vat_mfn, profit_mfn_pln = calc_price(mfn_shipping)
price_fba, fee_fba, ppc_fba, vat_fba, profit_fba_pln = calc_price(fba_logistics)

st.divider()
st.subheader("📊 Wynik Kalkulacji")

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.info("### Model MFN (Własny)")
    st.markdown(f"Sugerowana cena: **{price_mfn:.2f} {symbol}**")
    st.caption(f"• Zysk kwotowy: **{profit_mfn_pln:.2f} PLN**")
    st.caption(f"• Kurier MFN: {mfn_shipping:.2f} {symbol}")
    st.caption(f"• Prowizja Amazon: {fee_mfn:.2f} {symbol}")
    st.caption(f"• Reklamy PPC: {ppc_mfn:.2f} {symbol}")
    st.caption(f"• Podatek VAT ({vat_pct:.0f}%): {vat_mfn:.2f} {symbol}")

with res_col2:
    st.success("### Model FBA (Amazon)")
    st.markdown(f"Sugerowana cena: **{price_fba:.2f} {symbol}**")
    st.caption(f"• Zysk kwotowy: **{profit_fba_pln:.2f} PLN**")
    st.caption(f"• Opłaty FBA: {fba_logistics:.2f} {symbol}")
    st.caption(f"• Prowizja Amazon: {fee_fba:.2f} {symbol}")
    st.caption(f"• Reklamy PPC: {ppc_fba:.2f} {symbol}")
    st.caption(f"• Podatek VAT ({vat_pct:.0f}%): {vat_fba:.2f} {symbol}")

if fba_logistics < mfn_shipping:
    st.success("💡 **Wniosek:** Model FBA jest tańszy logistycznie! Pozwala uzyskać założoną marżę przy niższej cenie wyjściowej.")
else:
    st.warning("💡 **Wniosek:** Model MFN wychodzi taniej na logistyce dla tego produktu.")
