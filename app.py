import streamlit as st
import requests

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Amazon EU/PL - MalTec", page_icon="🛍️", layout="centered")

# Funkcja pobierająca aktualny kurs EUR/PLN z NBP
@st.cache_data(ttl=3600)  # Pamięć podręczna na 1 godzinę, aby nie obciążać serwera NBP
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
    return 4.30, None  # Wartość awaryjna

# Pobranie kursu NBP
nbp_rate, nbp_date = get_nbp_eur_rate()

st.title("🛍️ Kalkulator Cen Amazon EU / PL")
st.write("Wpisz koszty i oczekiwaną marżę netto, aby wyliczyć sugerowaną cenę sprzedaży w Euro lub PLN dla MFN i FBA.")

st.divider()

# Sekcja wyboru rynku i waluty
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

# Automatyczny dobór stawki VAT
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

# Sekcja wprowadzania danych
st.subheader("2. Podstawowe dane i marża")
col1, col2 = st.columns(2)

with col1:
    cost_pln = st.number_input("Koszt zakupu + fracht (PLN netto)", value=120.0, step=5.0)
    target_margin_pct = st.number_input("Oczekiwana marża netto (%)", value=20.0, step=1.0)
    
    # Pole kursu automatycznie pobierające wartość z NBP
    rate = st.number_input("Kurs EUR/PLN (Auto z NBP)", value=float(nbp_rate), step=0.01)
    if nbp_date:
        st.caption(f"🟢 Pobrano z NBP z dnia: {nbp_date} ({nbp_rate:.4f} PLN)")
    else:
        st.caption("🟡 Brak połączenia z NBP – użyto kursu domyślnego.")

with col2:
    fee_pct = st.number_input("Prowizja Amazon (%)", value=15.0, step=0.5)
    ppc_pct = st.number_input("Budżet na reklamy PPC (%)", value=10.0, step=0.5)
    st.info(f"Podatek VAT: **{vat_pct:.0f}%** | Waluta ceny: **{currency}**")

st.subheader("3. Koszty logistyki")
col3, col4 = st.columns(2)

if "EUR" in currency:
    label_mfn = "Koszt własnego kuriera MFN (€)"
    label_fba = "Opłaty FBA (Fulfilment + Storage) (€)"
    default_mfn = 6.50
    default_fba = 4.95
else:
    label_mfn = "Koszt własnego kuriera MFN (zł)"
    label_fba = "Opłaty FBA (Fulfilment + Storage) (zł)"
    default_mfn = 25.00
    default_fba = 21.00

with col3:
    mfn_shipping = st.number_input(label_mfn, value=default_mfn, step=0.50)

with col4:
    fba_logistics = st.number_input(label_fba, value=default_fba, step=0.50)

# Logika przeliczania cen
def calc_price(logistics_val):
    if "EUR" in currency:
        cost_in_target_curr = cost_pln / rate
        logistics_in_target_curr = logistics_val
    else:
        cost_in_target_curr = cost_pln
        logistics_in_target_curr = logistics_val

    fee_dec = fee_pct / 100.0
    ppc_dec = ppc_pct / 100.0
    vat_dec = vat_pct / 100.0
    margin_dec = target_margin_pct / 100.0

    net_multiplier = (1.0 - fee_dec - ppc_dec - margin_dec) / (1.0 + vat_dec)
    
    if net_multiplier > 0:
        price = (cost_in_target_curr + logistics_in_target_curr) / net_multiplier
    else:
        price = 0.0

    vat = price - (price / (1.0 + vat_dec)) if price > 0 else 0.0
    fee = price * fee_dec
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
    st.caption(f"• Prowizja Amazon: {fee_mfn:.2f} {symbol}")
    st.caption(f"• Reklamy PPC: {ppc_mfn:.2f} {symbol}")
    st.caption(f"• Podatek VAT ({vat_pct:.0f}%): {vat_mfn:.2f} {symbol}")

with res_col2:
    st.success("### Model FBA (Amazon)")
    st.markdown(f"Sugerowana cena: **{price_fba:.2f} {symbol}**")
    st.caption(f"• Zysk kwotowy: **{profit_fba_pln:.2f} PLN**")
    st.caption(f"• Prowizja Amazon: {fee_fba:.2f} {symbol}")
    st.caption(f"• Reklamy PPC: {ppc_fba:.2f} {symbol}")
    st.caption(f"• Podatek VAT ({vat_pct:.0f}%): {vat_fba:.2f} {symbol}")

if fba_logistics < mfn_shipping:
    st.success("💡 **Wniosek:** Model FBA jest tańszy logistycznie! Pozwala uzyskać założoną marżę przy niższej cenie wyjściowej.")
else:
    st.warning("💡 **Wniosek:** Model MFN wychodzi taniej na logistyce dla tego produktu.")
