# data.py
import pandas as pd
import numpy as np

# Uygulamada SADECE bunlar olacak (kural)
REQUIRED_COLS = [
    "Ünite",
    "Sipariş No",
    "Paket şekli",
    "Item No.",
    "Açıklama",
    "Adet",
    "Net Ağırlık (Kg)",
    "Brüt Ağırlık (Kg)",
    "BOY",
    "EN",
    "YÜKSEKLİK",
    "Tartım Şekli",
]

MISSING_TEXT = "girilmemiş değer"


def _normalize_colname(c: str) -> str:
    if c is None:
        return ""
    c = str(c).replace("\n", " ").strip()
    c = " ".join(c.split())  # fazla boşlukları temizle
    return c


def _first_existing_col(cols, target: str):
    """Excel'de aynı başlık birden fazla gelebiliyor (BOY, EN, YÜKSEKLİK vb).
    İlk eşleşeni seçer.
    """
    target_n = _normalize_colname(target)
    for c in cols:
        if _normalize_colname(c) == target_n:
            return c
    return None


def _to_numeric_safe(series: pd.Series):
    """Virgül/nokta karışık sayı formatını güvenli sayıya çevirir."""
    if series is None:
        return series
    s = series.astype(str)
    s = s.replace({"nan": np.nan, "None": np.nan, "NaT": np.nan})
    # TR format: 21.900,00 -> 21900.00
    s = s.str.replace(".", "", regex=False)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def read_all_sheets(path: str) -> pd.DataFrame:
    """Tüm sheet'leri okur, tek ana tablo yapar."""
    xls = pd.ExcelFile(path)
    frames = []
    for sh in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sh, dtype=object)
        df.columns = [_normalize_colname(c) for c in df.columns]
        frames.append(df)
    big = pd.concat(frames, ignore_index=True)
    return big


def build_clean_table(excel_path: str) -> pd.DataFrame:
    """
    - Tüm sheet'leri okur
    - Sadece REQUIRED_COLS kalır
    - Aynı kolon başlığı birden fazla varsa ilkini alır
    - Tamamen boş satırları siler (ama satırda boş hücre varsa silmez)
    - Boş hücrelere 'girilmemiş değer' yazar (sayısallarda sonradan hesap için numeric copy de üretilebilir)
    """
    raw = read_all_sheets(excel_path)

    # Kolon adlarını normalize et (zaten ettik ama garanti)
    raw.columns = [_normalize_colname(c) for c in raw.columns]

    # REQUIRED_COLS için mapping: her hedef kolonun excel'deki ilk karşılığını seç
    selected = {}
    for col in REQUIRED_COLS:
        exist = _first_existing_col(raw.columns, col)
        if exist is not None:
            selected[col] = raw[exist]
        else:
            selected[col] = pd.Series([np.nan] * len(raw), index=raw.index)

    df = pd.DataFrame(selected)

    # Tamamen boş satırlar (tüm alanlar NaN) silinsin
    df = df.dropna(how="all").reset_index(drop=True)

    # Boşlara 'girilmemiş değer' yaz (satır silme yok!)
    df = df.replace({None: np.nan})
    for c in df.columns:
        df[c] = df[c].where(~df[c].isna(), MISSING_TEXT)

    # Sayısal kolonları ayrıca numeric'e çevirelim (özet hesapları için)
    # (Ekranda yine metin görünebilir; hesapta numeric kullanacağız)
    df["_net_num"] = _to_numeric_safe(df["Net Ağırlık (Kg)"].replace(MISSING_TEXT, np.nan))
    df["_brut_num"] = _to_numeric_safe(df["Brüt Ağırlık (Kg)"].replace(MISSING_TEXT, np.nan))
    df["_adet_num"] = _to_numeric_safe(df["Adet"].replace(MISSING_TEXT, np.nan))

    # Ünite ve Sipariş No temizliği
    df["Ünite"] = df["Ünite"].astype(str).str.strip()
    df["Sipariş No"] = df["Sipariş No"].astype(str).str.replace("\n", " ", regex=False).str.strip()

    return df
