import re
from datetime import datetime

def extract_info(text, jenis_surat):
    """Ekstrak informasi penting dari teks OCR"""
    info = {
        "jenis": jenis_surat,
        "nama": None,
        "nim": None,
        "tanggal": None,
        "tanggal_mulai": None,
        "tanggal_selesai": None,
        "alasan": None,
        "durasi": None,
        "dokter": None,
        "klinik": None
    }
    
    # Ekstrak satu per satu
    info["nama"] = extract_nama(text)           # Nama
    info["nim"] = extract_nim(text)             # NIM
    info["tanggal"] = extract_tanggal(text)     # Tanggal
    
    # Ekstrak range tanggal (khusus surat sakit)
    tanggal_mulai, tanggal_selesai, durasi = extract_tanggal_range(text)
    if tanggal_mulai:
        info["tanggal_mulai"] = tanggal_mulai
        info["tanggal_selesai"] = tanggal_selesai
        info["durasi"] = durasi
        if not info["tanggal"]:
            info["tanggal"] = tanggal_mulai
    
    # Ekstrak alasan
    info["alasan"] = extract_alasan(text, jenis_surat)
    
    # Ekstrak durasi (jika belum ada)
    if not info["durasi"]:
        info["durasi"] = extract_durasi(text)
    
    # Ekstrak dokter (surat sakit)
    info["dokter"] = extract_dokter(text)
    
    # Ekstrak klinik/rumah sakit
    info["klinik"] = extract_klinik(text)
    
    return info

def extract_nama(text):
    """Ekstrak nama dari teks"""
    nama_patterns = [
        r"Nama\s*[:=]\s*([A-Z][a-zA-Z\s]+?)(?:\n|Umur|NIM|Prodi)",
        r"(?:yang bertanda tangan|pembuat surat)\s+(?:di\s*)?(?:bawah|atas)\s+ini\s*[:=]?\s*\n+Nama\s*[:=]\s*([A-Z][a-zA-Z\s]+?)(?:\n|Umur|NIM)",
        r"Nama\s+mahasiswa\s*[:=]\s*([A-Z][a-zA-Z\s]+)",
        r"yang tersebut namanya\s+(?:di\s*)?(?:atas|bawah)\s+(?:.*?)\s+([A-Z][a-zA-Z\s]{3,})",
    ]
    
    for pattern in nama_patterns:
        nama_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if nama_match:
            nama = nama_match.group(1).strip()
            nama = re.sub(r'\s+', ' ', nama)
            if len(nama) > 3 and not any(x in nama.lower() for x in ['benar', 'dalam', 'keadaan']):
                return nama
    return None

def extract_nim(text):
    """Ekstrak NIM dari teks"""
    nim_pattern = r"NIM\s*[:=]?\s*(\d+)"
    nim_match = re.search(nim_pattern, text, re.IGNORECASE)
    if nim_match:
        return nim_match.group(1).strip()
    return None

def extract_tanggal(text):
    """Ekstrak tanggal tunggal dari teks"""
    tanggal_patterns = [
        r"tanggal\s+(\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4})",
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"(\d{1,2}\s+\w+\s+\d{4})",
    ]
    
    for pattern in tanggal_patterns:
        tanggal_match = re.search(pattern, text, re.IGNORECASE)
        if tanggal_match:
            return tanggal_match.group(1).strip()
    return None

def extract_tanggal_range(text):
    """Ekstrak range tanggal dan hitung durasi"""
    tanggal_range_pattern = r"(?:mulai dari )?[Tt]anggal\s+(\d{1,2}\s+\w+\s+\d{4})\s*[–\-—]\s*(\d{1,2}\s+\w+\s+\d{4})"
    range_match = re.search(tanggal_range_pattern, text)
    
    if range_match:
        tanggal_mulai = range_match.group(1).strip()
        tanggal_selesai = range_match.group(2).strip()
        
        # Hitung durasi
        durasi = calculate_durasi(tanggal_mulai, tanggal_selesai)
        return tanggal_mulai, tanggal_selesai, durasi
    
    return None, None, None

def calculate_durasi(tanggal_mulai, tanggal_selesai):
    """Menghitung durasi antara dua tanggal"""
    try:
        bulan_map = {
            'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
        }
        
        def parse_indo_date(date_str):
            parts = date_str.lower().split()
            if len(parts) == 3:
                day = int(parts[0])
                month = bulan_map.get(parts[1], 1)
                year = int(parts[2])
                return datetime(year, month, day)
            return None
        
        d1 = parse_indo_date(tanggal_mulai)
        d2 = parse_indo_date(tanggal_selesai)
        
        if d1 and d2:
            durasi_hari = (d2 - d1).days + 1
            return f"{durasi_hari} hari"
    except:
        pass
    return None

def extract_alasan(text, jenis_surat):
    """Ekstrak alasan/diagnosa dari teks"""
    if jenis_surat == "surat_sakit":
        alasan_patterns = [
            r"(?:dalam keadaan|menderita|didiagnosa|diagnosa|penyakit)\s+([A-Z][^\n\.]+?)(?:\s+maka|\s+sehingga|\.|Demikian)",
            r"keadaan\s+([A-Z][A-Z\s]+?)(?:\s+maka)",
        ]
        
        for pattern in alasan_patterns:
            alasan_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if alasan_match:
                alasan = alasan_match.group(1).strip()
                if len(alasan) > 3 and alasan.upper() == alasan:
                    return alasan
    
    if jenis_surat == "surat_izin":
        alasan_patterns = [
            r"karena\s*[:=]?\s*([^\n\.]+?)(?:\.|Demikian|\n\n)",
            r"alasan\s*[:=]?\s*([^\n\.]+)",
        ]
        
        for pattern in alasan_patterns:
            alasan_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if alasan_match:
                return alasan_match.group(1).strip()
    
    return None

def extract_durasi(text):
    """Ekstrak durasi dari teks"""
    durasi_patterns = [
        r"(?:berlaku|selama|istirahat)\s+(\d+)\s*(?:hari|day)",
        r"(\d+)\s*(?:hari|day)",
    ]
    
    for pattern in durasi_patterns:
        durasi_match = re.search(pattern, text, re.IGNORECASE)
        if durasi_match:
            return durasi_match.group(1) + " hari"
    return None

def extract_dokter(text):
    """Ekstrak nama dokter dari teks"""
    dokter_pattern = r"(?:Dokter|dr\.|Dr\.)\s+([A-Z][a-zA-Z\s\.]+?)(?:\n|NIP)"
    dokter_match = re.search(dokter_pattern, text, re.MULTILINE)
    if dokter_match:
        return dokter_match.group(1).strip()
    return None

def extract_klinik(text):
    """Ekstrak nama klinik/rumah sakit dari teks"""
    klinik_patterns = [
        r"(KLINIK [A-Z\s]+?)(?:\n|Jl\.)",
        r"(RUMAH SAKIT [A-Z\s]+?)(?:\n|Jl\.)",
        r"(PUSKESMAS [A-Z\s]+?)(?:\n|Jl\.)",
    ]
    
    for pattern in klinik_patterns:
        klinik_match = re.search(pattern, text, re.IGNORECASE)
        if klinik_match:
            return klinik_match.group(1).strip()
    return None


"""Cara kerja Regex:**
```
Teks: "Nama: BUDI SANTOSO\nNIM: 2021001"
       ↓
Pattern: r"Nama\s*[:=]\s*([A-Z][a-zA-Z\s]+)"
         Nama  (spasi)  :   (spasi)  [tangkap huruf kapital & spasi]
       ↓
Match: "BUDI SANTOSO"
       ↓
Hasil: info["nama"] = "BUDI SANTOSO"
"""