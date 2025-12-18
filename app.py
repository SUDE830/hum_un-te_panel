# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

from data import build_clean_table, REQUIRED_COLS

EXCEL_PATH = "data/hum_data.xlsx"
LOGO_PATH = "assets/hum_logo.png"

st.set_page_config(
    page_title="HUM Ekipman & Sipariş Arama",
    page_icon="🔎",
    layout="wide",
)

# ---------------- DATA ----------------
@st.cache_data(show_spinner="Veriler yükleniyor...")
def load_data():
    return build_clean_table(EXCEL_PATH)

df = load_data()

# ---------------- STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "ekipman"
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None

def go(page):
    st.session_state.page = page

# ---------------- HEADER ----------------
c1, c2 = st.columns([1, 5])
with c1:
    st.image(LOGO_PATH, width=120)
with c2:
    st.markdown("## HUM Ekipman & Sipariş Arama Paneli")
    st.caption("Excel dosyası içinde aranan ekipmanı saniyeler içinde bulun")

m1, m2, m3, m4 = st.columns(4)
m1.button("🔎 Ekipman Arama", on_click=go, args=("ekipman",), use_container_width=True)
m2.button("📦 Siparişler", on_click=go, args=("siparisler",), use_container_width=True)
m3.button("📊 Analiz", on_click=go, args=("analiz",), use_container_width=True)
m4.button("❓ Yardım", on_click=go, args=("yardim",), use_container_width=True)

st.divider()

# ======================================================
# 🔎 EKİPMAN ARAMA + DETAY (3. MADDE)
# ======================================================
def page_equipment():
    st.subheader("🔎 Ekipman Arama")

    q = st.text_input(
        "Ara (Ünite / Sipariş No / Item No / Açıklama)",
        placeholder="Örn: HSB480, OR 006-2016, Toaster, 40 D 652"
    )

    col1, col2 = st.columns(2)
    unit_sel = col1.selectbox(
        "Ünite Seç",
        ["Tümü"] + sorted(df["Ünite"].unique().tolist())
    )
    order_sel = col2.selectbox(
        "Sipariş No Seç",
        ["Tümü"] + sorted(df["Sipariş No"].unique().tolist())
    )

    filtered = df.copy()

    if unit_sel != "Tümü":
        filtered = filtered[filtered["Ünite"] == unit_sel]
    if order_sel != "Tümü":
        filtered = filtered[filtered["Sipariş No"] == order_sel]
    if q:
        q = q.lower()
        filtered = filtered[
            filtered["Ünite"].str.lower().str.contains(q) |
            filtered["Sipariş No"].str.lower().str.contains(q) |
            filtered["Item No."].str.lower().str.contains(q) |
            filtered["Açıklama"].str.lower().str.contains(q)
        ]

    st.markdown("### 📌 Özet")
    a, b, c = st.columns(3)
    a.metric("Toplam Kayıt", len(filtered))
    b.metric("Toplam Net (Kg)", f"{filtered['_net_num'].sum():,.2f}")
    c.metric("Toplam Brüt (Kg)", f"{filtered['_brut_num'].sum():,.2f}")

    st.markdown("### 📋 Sonuçlar (Satır Seç → Detay Gör)")
    st.dataframe(
        filtered[REQUIRED_COLS],
        use_container_width=True,
        height=420
    )

    st.markdown("### 🔍 Ekipman Detayı")
    idx = st.number_input(
        "Detay görmek için tablodaki satır index numarasını gir",
        min_value=0,
        max_value=len(filtered)-1 if len(filtered) > 0 else 0,
        step=1
    )

    if len(filtered) > 0:
        row = filtered.iloc[int(idx)]
        st.success(f"**{row['Açıklama']}**")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Ünite:** {row['Ünite']}")
        c2.write(f"**Sipariş No:** {row['Sipariş No']}")
        c3.write(f"**Item No:** {row['Item No.']}")

        st.write(
            f"""
            **Net Ağırlık:** {row['Net Ağırlık (Kg)']} kg  
            **Brüt Ağırlık:** {row['Brüt Ağırlık (Kg)']} kg  
            **Ölçüler (B×E×Y):** {row['BOY']} × {row['EN']} × {row['YÜKSEKLİK']}  
            **Tartım Şekli:** {row['Tartım Şekli']}
            """
        )

# ======================================================
# 📦 SİPARİŞLER
# ======================================================
def page_orders():
    st.subheader("📦 Siparişler")

    order = st.selectbox(
        "Sipariş Seç",
        sorted(df["Sipariş No"].unique())
    )

    odf = df[df["Sipariş No"] == order]

    a, b, c = st.columns(3)
    a.metric("Ekipman Sayısı", len(odf))
    b.metric("Toplam Net (Kg)", f"{odf['_net_num'].sum():,.2f}")
    c.metric("Toplam Brüt (Kg)", f"{odf['_brut_num'].sum():,.2f}")

    st.dataframe(odf[REQUIRED_COLS], use_container_width=True)

# ======================================================
# 📊 ANALİZ
# ======================================================
def page_analysis():
    st.subheader("📊 Analiz")

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(
            df.groupby("Ünite")["_brut_num"].sum().reset_index(),
            x="Ünite",
            y="_brut_num",
            title="Ünite Bazlı Toplam Brüt Ağırlık (Kg)"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        top10 = df.sort_values("_brut_num", ascending=False).head(10)
        fig2 = px.bar(
            top10,
            x="Açıklama",
            y="_brut_num",
            title="En Ağır 10 Ekipman"
        )
        st.plotly_chart(fig2, use_container_width=True)

# ======================================================
# ❓ YARDIM
# ======================================================
def page_help():
    st.subheader("❓ Yardım & Kullanım Rehberi")

    st.markdown("""
### Bu uygulama ne işe yarar?
- HUM içindeki **tüm ekipmanları ve siparişleri**
- Excel karışıklığı olmadan
- Tek ekrandan hızlıca bulmanızı sağlar

### Nasıl arama yaparım?
- Arama kutusuna **ünite / sipariş / item / açıklama** yazabilirsiniz
- Ünite ve Sipariş filtreleri birlikte çalışır

### “girilmemiş değer” ne demek?
- Excel dosyasında o bilgi **hiç girilmemiş**
- Uygulama veriyi silmez, bilerek gösterir

### Bu bir Excel aracı mı?
❌ Hayır  
✅ HUM içi **web uygulaması**
""")

# ---------------- ROUTER ----------------
if st.session_state.page == "ekipman":
    page_equipment()
elif st.session_state.page == "siparisler":
    page_orders()
elif st.session_state.page == "analiz":
    page_analysis()
elif st.session_state.page == "yardim":
    page_help()
