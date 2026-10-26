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
st.write("Wpisz parametry produktu, wagę oraz koszty, aby wyliczyć optymalną cenę sprzedaży lub sprawdzić marżę produktową.")

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

# Sekcja 2: Tryb kalkulacji i parametry
st.subheader("2. Tryb kalkulacji, koszty i prowizje")

calc_mode = st.radio(
    "Co chcesz wyliczyć?",
    ["Sugerowaną cenę (na podstawie oczekiwanej marży produktowej)", "Marżę produktową (na podstawie konkretnej ceny wyjściowej)"],
    horizontal=False
)

col1, col2 = st.columns(2)

with col1:
    cost_pln = st.number_input("Koszt zakupu + fracht (PLN netto)", value=120.0, step=5.0)
    
    if calc_mode == "Sugerowaną cenę (na podstawie oczekiwanej marży produktowej)":
        target_margin_pct = st.number_input("Oczekiwana marża produktowa (%)", value=30.0, step=1.0, help="(Cena netto - Koszt netto) / Cena netto")
        given_price = 0.0
    else:
        given_price = st.number_input(f"Konkretna cena wyjściowa na Amazon ({symbol})", value=49.99, step=1.0)
        target_margin_pct = 0.0

    rate = st.number_input("Kurs EUR/PLN (Auto z NBP)", value=float(nbp_rate), step=0.01)
    if nbp_date:
        st.caption(f"🟢 Pobrano z NBP z dnia: {nbp_date} ({nbp_rate:.4f} PLN)")

with col2:
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
st.subheader("3. Koszty logistyki, FBA i opłaty sezonowe")

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
        label_mfn = f"Koszt własnego kuriera MFN ({symbol})"
        default_mfn = 6.50 if "EUR" in currency else 25.00
        mfn_shipping = st.number_input(label_mfn, value=default_mfn, step=0.50)

with col4:
    label_fba = f"Podstawowa opłata FBA (Fulfilment) ({symbol})"
    default_fba = 4.95 if "EUR" in currency else 21.00
    fba_base_cost = st.number_input(label_fba, value=default_fba, step=0.50)

    # Opcje dopłat FBA
    st.markdown("**Ustawienia dopłat FBA:**")
    enable_seasonal_fee = st.checkbox("Dopłata sezonowa FBA (15.10.2026 – 14.01.2027)", value=("Niemcy" in country))
    
    default_seasonal_val = 0.27 if "EUR" in currency else (0.27 * nbp_rate)
    if enable_seasonal_fee:
        seasonal_fee_val = st.number_input(f"Wysokość dopłaty sezonowej ({symbol})", value=float(f"{default_seasonal_val:.2f}"), step=0.05)
    else:
        seasonal_fee_val = 0.0

    enable_fuel_surcharge = st.checkbox("Dopłata paliwowo-logistyczna FBA", value=True)
    if enable_fuel_surcharge:
        fuel_surcharge_pct = st.number_input("Stawka dopłaty paliwowej (%)", value=2.0, step=0.1, help="Stawka aktualizowana do 2,0%.")
    else:
        fuel_surcharge_pct = 0.0

# Kalkulacja całkowitej opłaty FBA
fba_fuel_fee = fba_base_cost * (fuel_surcharge_pct / 100.0)
total_fba_logistics = fba_base_cost + seasonal_fee_val + fba_fuel_fee

if enable_seasonal_fee or enable_fuel_surcharge:
    st.caption(f"ℹ️ **Łączny koszt FBA:** {total_fba_logistics:.2f} {symbol} (Podstawa: {fba_base_cost:.2f} | Sezonowa: {seasonal_fee_val:.2f} | Paliwo {fuel_surcharge_pct:.1f}%: {fba_fuel_fee:.2f})")

# Logika przeliczania według nowego wzoru marży produktowej:
# Marża = (Cena netto - Koszt netto) / Cena netto
def calc_metrics(logistics_val):
    if "EUR" in currency:
        cost_in_target_curr = cost_pln / rate
    else:
        cost_in_target_curr = cost_pln

    logistics_in_target_curr = logistics_val
    vat_dec = vat_pct / 100.0
    ppc_dec = ppc_pct / 100.0

    if calc_mode == "Sugerowaną cenę (na podstawie oczekiwanej marży produktowej)":
        margin_dec = target_margin_pct / 100.0
        
        # Zgodnie ze wzorem: margin = (net_sales - cost) / net_sales => net_sales = cost / (1 - margin)
        if margin_dec >= 1.0:
            margin_dec = 0.99  # zabezpieczenie przed dzieleniem przez zero
            
        net_sales = cost_in_target_curr / (1.0 - margin_dec)
        
        # Cena brutto musi pokryć net_sales, ale uwzględnić też pozostałe koszty (logistyka, prowizja, PPC) pokrywane z przychodu
        # Przychód netto ze sprzedaży (net_sales) musi być na tyle wysoki, by po odjęciu prowizji i PPC oraz logistyki spiąć budżet, 
        # LUB traktujemy marżę jako narzut na koszt zakupu, a koszty operacyjne doliczamy do ceny:
        # Cena brutto = (net_sales + logistics_in_target_curr + fee + ppc_costs) * (1 + vat_dec) ? 
        # Sprawdźmy standardowe podejście handlowe: 
        # Skoro net_sales = cost / (1 - margin), to cena netto ma pokryć koszt i dać marżę. 
        # Dodatkowo logistyka, prowizja i PPC to koszty dodatkowe. 
        # Rozwiążmy to równanie liniowe dla ceny brutto (price):
        # net_sales = price / (1 + vat_dec)
        # fee = price * (fee_pct / 100.0) lub fee_fixed_val
        # ppc = price * ppc_dec
        # net_sales - cost = margin * net_sales  =>  net_sales * (1 - margin) = cost  =>  net_sales = cost / (1 - margin)
        # Z drugiej strony z bilansu przychodów netto: net_sales = cost + logistics + fee_netto + ppc_netto + zysk? 
        # Najprościej: Cena netto (net_sales) = (Koszt zakupu + Logistyka) / (1 - Marża - Prowizja% - PPC%) [jeśli prowizja i PPC są % od ceny netto]
        # Ponieważ prowizja i PPC są zwykle od ceny brutto, przeliczmy to precyzyjnie:
        
        fee_dec = (fee_pct / 100.0) if fee_type == "Procentowo (%)" else 0.0
        fixed_fee = fee_fixed_val if fee_type != "Procentowo (%)" else 0.0

        # Równanie na cenę brutto (price):
        # net_sales = price / (1 + vat_dec)
        # cost = net_sales * (1 - margin_dec) -> cost = (price / (1 + vat_dec)) * (1 - margin_dec)
        # Ale z drugiej strony cenę tworzą koszty: 
        # price / (1 + vat_dec) [net_sales] = cost + logistics + fee + ppc ...
        # Skoro net_sales = cost / (1 - margin_dec), to:
        # (price / (1 + vat_dec)) = cost / (1 - margin_dec) + logistics + (price * fee_dec + fixed_fee) + (price * ppc_dec)
        # Przekształcamy do wyznaczenia price:
        # price * ( 1/(1+vat_dec) - fee_dec - ppc_dec ) = (cost / (1 - margin_dec)) + logistics + fixed_fee
        
        denominator = (1.0 / (1.0 + vat_dec)) - fee_dec - ppc_dec
        if denominator > 0:
            price = ((cost_in_target_curr / (1.0 - margin_dec)) + logistics_in_target_curr + fixed_fee) / denominator
        else:
            price = 0.0

        vat = price - (price / (1.0 + vat_dec)) if price > 0 else 0.0
        net_sales = price / (1.0 + vat_dec) if price > 0 else 0.0
        fee = (price * fee_dec) if fee_type == "Procentowo (%)" else fixed_fee
        ppc = price * ppc_dec
        
        calculated_margin_pct = target_m_pct = target_margin_pct

    else:
        price = given_price
        vat = price - (price / (1.0 + vat_dec)) if price > 0 else 0.0
        net_sales = price / (1.0 + vat_dec) if price > 0 else 0.0

        if fee_type == "Procentowo (%)":
            fee = price * (fee_pct / 100.0)
        else:
            fee = fee_fixed_val

        ppc = price * ppc_dec

        # Wyliczenie marży produktowej ze wzoru użytkownika: (cena sprzedaży netto - cena zakupu netto) / cena sprzedaży netto
        if net_sales > 0:
            calculated_margin_pct = ((net_sales - cost_in_target_curr) / net_sales) * 100.0
        else:
            calculated_margin_pct = 0.0

    # Kwotowy zysk netto operacyjny po wszystkich kosztach
    profit_in_target_curr = net_sales - cost_in_target_curr - logistics_in_target_curr - fee - ppc
    profit_pln = profit_in_target_curr * rate if "EUR" in currency else profit_in_target_curr

    return price, fee, ppc, vat, profit_in_target_curr, profit_pln, calculated_margin_pct

p_mfn, fee_mfn, ppc_mfn, vat_mfn, prof_mfn_curr, prof_mfn_pln, margin_mfn = calc_metrics(mfn_shipping)
p_fba, fee_fba, ppc_fba, vat_fba, prof_fba_curr, prof_fba_pln, margin_fba = calc_metrics(total_fba_logistics)

st.divider()
st.subheader("📊 Wynik Kalkulacji")

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.info("### Model MFN (Własny)")
    if calc_mode == "Sugerowaną cenę (na podstawie oczekiwanej marży produktowej)":
        st.markdown(f"Sugerowana cena: **{p_mfn:.2f} {symbol}**")
    else:
        st.markdown(f"Cena sprzedaży: **{p_mfn:.2f} {symbol}**")
    
    st.markdown(f"• **Marża produktowa: {margin_mfn:.2f}%**")
    st.caption(f"• Zysk operacyjny: **{prof_mfn_pln:.2f} PLN** ({prof_mfn_curr:.2f} {symbol})")
    st.caption(f"• Kurier MFN: {mfn_shipping:.2f} {symbol}")
    st.caption(f"• Prowizja Amazon: {fee_mfn:.2f} {symbol}")
    st.caption(f"• Reklamy PPC: {ppc_mfn:.2f} {symbol}")
    st.caption(f"• Podatek VAT ({vat_pct:.0f}%): {vat_mfn:.2f} {symbol}")

with res_col2:
    st.success("### Model FBA (Amazon)")
    if calc_mode == "Sugerowaną cenę (na podstawie oczekiwanej marży produktowej)":
        st.markdown(f"Sugerowana cena: **{p_fba:.2f} {symbol}**")
    else:
        st.markdown(f"Cena sprzedaży: **{p_fba:.2f} {symbol}**")
        
    st.markdown(f"• **Marża produktowa: {margin_fba:.2f}%**")
    st.caption(f"• Zysk operacyjny: **{prof_fba_pln:.2f} PLN** ({prof_fba_curr:.2f} {symbol})")
    st.caption(f"• Opłaty FBA łącznie: **{total_fba_logistics:.2f} {symbol}**")
    st.caption(f"  └ Podstawa: {fba_base_cost:.2f} | Sezonowa: {seasonal_fee_val:.2f} | Paliwo ({fuel_surcharge_pct:.1f}%): {fba_fuel_fee:.2f} {symbol}")
    st.caption(f"• Prowizja Amazon: {fee_fba:.2f} {symbol}")
    st.caption(f"• Reklamy PPC: {ppc_fba:.2f} {symbol}")
    st.caption(f"• Podatek VAT ({vat_pct:.0f}%): {vat_fba:.2f} {symbol}")

if total_fba_logistics < mfn_shipping:
    st.success("💡 **Wniosek:** Model FBA jest tańszy logistycznie dla tego produktu!")
else:
    st.warning("💡 **Wniosek:** Model MFN jest tańszy logistycznie dla tego produktu!")
