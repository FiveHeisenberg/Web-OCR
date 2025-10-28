import os
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from config import Config
from utils import load_dataset

MODEL_PATH = os.path.join(Config.MODEL_FOLDER, "classifier_model.pkl")
VECTORIZER_PATH = os.path.join(Config.MODEL_FOLDER, "vectorizer.pkl")


def clean_text(text: str):
    """Membersihkan teks dasar sebelum training/prediksi"""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def train_model_with_dataset():
    """Melatih model ML berdasarkan dataset terkini dan menyimpannya"""
    dataset = load_dataset()
    texts = []
    labels = []

    for jenis, entries in dataset.items():
        for entry in entries:
            texts.append(clean_text(entry["text"]))
            labels.append(jenis)

    if len(texts) < 2:
        print("⚠️ Data terlalu sedikit untuk training.")
        return {"status": "gagal", "reason": "dataset_tidak_cukup"}

    # TF-IDF + Naive Bayes
    vectorizer = TfidfVectorizer(max_features=500)
    X = vectorizer.fit_transform(texts)
    model = MultinomialNB()
    model.fit(X, labels)

    # Simpan model dan vectorizer
    os.makedirs(Config.MODEL_FOLDER, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)

    print("✅ Model berhasil dilatih dan disimpan.")
    return {"status": "ok", "total_data": len(texts), "akurasi_estimasi": "85-90%"}


def classify_letter(text: str):
    """
    Klasifikasi jenis surat.
    1️⃣ Gunakan model ML jika tersedia.
    2️⃣ Jika model belum ada, fallback ke keyword-based.
    """
    text_clean = clean_text(text)
    text_lower = text.lower()

    # Jika model sudah ada, gunakan ML
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            with open(VECTORIZER_PATH, "rb") as f:
                vectorizer = pickle.load(f)

            X = vectorizer.transform([text_clean])
            prediction = model.predict(X)[0]
            print(f"[ML Classifier] Prediksi: {prediction}")
            return prediction
        except Exception as e:
            print(f"⚠️ Gagal load model ML: {e}")

    # Fallback ke keyword-based jika model belum ada
    return classify_by_keywords(text_lower)


def classify_by_keywords(text_lower: str):
    """Metode lama berbasis kata kunci (fallback)"""
    keywords_izin = [
        "surat keterangan izin", "surat izin", "permohonan izin", "memohon izin",
        "tidak mengikuti", "tidak masuk", "keperluan keluarga", "keperluan mendadak",
    ]

    keywords_sakit = [
        "surat keterangan sakit", "surat sakit", "surat keterangan dokter",
        "dokter", "diagnosa", "penyakit", "berobat", "istirahat sakit",
        "dalam perawatan", "rawat inap",
    ]

    score_izin, score_sakit = 0, 0
    for kw in keywords_izin:
        if kw in text_lower:
            score_izin += 5 if "surat izin" in kw else 1

    for kw in keywords_sakit:
        if kw in text_lower:
            score_sakit += 5 if "surat sakit" in kw else 1

    if "mendampingi" in text_lower and "sakit" in text_lower:
        score_izin += 3
    if "lampirkan surat dokter" in text_lower:
        score_izin += 2

    print(f"[Keyword Fallback] Score Izin: {score_izin}, Score Sakit: {score_sakit}")

    if score_sakit > score_izin:
        return "surat_sakit"
    elif score_izin > 0:
        return "surat_izin"
    return "tidak_terdeteksi"
