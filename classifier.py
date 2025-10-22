def classify_letter(text):
    """Klasifikasi jenis surat berdasarkan kata kunci"""
    text_lower = text.lower()
    
    # Kata kunci untuk surat izin
    keywords_izin = [
        "surat keterangan izin",
        "surat izin",
        "permohonan izin",
        "memohon izin",
        "tidak mengikuti",
        "tidak masuk",
        "keperluan keluarga",
        "keperluan mendadak",
    ]
    
    # Kata kunci untuk surat sakit
    keywords_sakit = [
        "surat keterangan sakit",
        "surat sakit",
        "surat keterangan dokter",
        "dokter",
        "diagnosa",
        "penyakit",
        "berobat",
        "istirahat sakit",
        "dalam perawatan",
        "rawat inap",
    ]
    
    # Hitung score
    score_izin = 0
    score_sakit = 0
    
    for kw in keywords_izin:
        if kw in text_lower:
            # Kata kunci spesifik diberi bobot lebih tinggi
            if "surat keterangan izin" in kw or "surat izin" in kw:
                score_izin += 5
            else:
                score_izin += 1
    
    for kw in keywords_sakit:
        if kw in text_lower:
            # Kata kunci spesifik diberi bobot lebih tinggi
            if "surat keterangan sakit" in kw or "surat sakit" in kw:
                score_sakit += 5
            else:
                score_sakit += 1
    
    # Cek konteks tambahan
    if "mendampingi" in text_lower and "sakit" in text_lower:
        score_izin += 3  # Izin karena anggota keluarga sakit
    
    if "lampirkan surat dokter" in text_lower:
        score_izin += 2  # Biasanya ada di surat izin
    
    print(f"[DEBUG] Score Izin: {score_izin}, Score Sakit: {score_sakit}")
    
    # Membandingkan score
    if score_sakit > score_izin:
        return "surat_sakit"
    elif score_izin > 0:
        return "surat_izin"
    return "tidak_terdeteksi"