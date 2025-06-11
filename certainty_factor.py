"""
Certainty Factor Calculator untuk Sistem Pakar HEROin
Implementasi sesuai dengan metodologi penelitian yang telah dipublikasi
"""

def calculate_symptom_cf(cf_expert, cf_user):
    """
    Menghitung CF gejala berdasarkan rumus penelitian:
    CF_gejala = CF_pakar × CF_user
    
    Args:
        cf_expert (float): Bobot keyakinan pakar (0.0 - 1.0)
        cf_user (float): Tingkat keyakinan user (0.0 - 1.0)
        
    Returns:
        float: CF kombinasi gejala
    """
    if not (0.0 <= cf_expert <= 1.0) or not (0.0 <= cf_user <= 1.0):
        raise ValueError("CF values must be between 0.0 and 1.0")
    
    return cf_expert * cf_user

def combine_certainty_factors(cf_values):
    """
    Menggabungkan multiple CF menggunakan rumus dari penelitian:
    CF_gabungan = CF1 + CF2 × (1 - CF1)
    
    Untuk lebih dari 2 CF, diterapkan secara berurutan:
    CF_temp = CF1 + CF2 × (1 - CF1)
    CF_gabungan = CF_temp + CF3 × (1 - CF_temp)
    dst...
    
    Args:
        cf_values (list): List nilai CF yang akan digabungkan
        
    Returns:
        float: CF gabungan (0.0 - 1.0)
    """
    if not cf_values:
        return 0.0
    
    if len(cf_values) == 1:
        return cf_values[0]
    
    # Mulai dengan CF pertama
    cf_gabungan = cf_values[0]
    
    # Gabungkan dengan CF berikutnya menggunakan rumus penelitian
    for i in range(1, len(cf_values)):
        cf_next = cf_values[i]
        
        if cf_gabungan >= 0 and cf_next >= 0:
            # Kedua nilai positif: CF1 + CF2 × (1 - CF1)
            cf_gabungan = cf_gabungan + (cf_next * (1 - cf_gabungan))
        elif cf_gabungan < 0 and cf_next < 0:
            # Kedua nilai negatif: CF1 + CF2 × (1 + CF1)
            cf_gabungan = cf_gabungan + (cf_next * (1 + cf_gabungan))
        else:
            # Nilai berbeda tanda: (CF1 + CF2) / (1 - min(|CF1|, |CF2|))
            denominator = 1 - min(abs(cf_gabungan), abs(cf_next))
            if denominator == 0:
                # Avoid division by zero
                cf_gabungan = (cf_gabungan + cf_next) / 2
            else:
                cf_gabungan = (cf_gabungan + cf_next) / denominator
    
    # Pastikan nilai tetap dalam rentang 0-1
    return max(0.0, min(1.0, cf_gabungan))

def get_cf_percentage(cf_value):
    """
    Mengkonversi CF value ke persentase sesuai penelitian:
    CF_persentase = CF_gabungan × 100
    
    Args:
        cf_value (float): Nilai CF (0.0 - 1.0)
        
    Returns:
        float: CF dalam persentase (0.0 - 100.0)
    """
    if not (0.0 <= cf_value <= 1.0):
        raise ValueError("CF value must be between 0.0 and 1.0")
    
    return cf_value * 100

def interpret_cf_result(cf_percentage):
    """
    Interpretasi hasil CF berdasarkan threshold penelitian:
    - Kecanduan Ringan (P1): 40-60%
    - Kecanduan Sedang (P2): 61-80% 
    - Kecanduan Berat (P3): 81-100%
    - Tidak Terdeteksi: <40%
    
    Args:
        cf_percentage (float): CF dalam persentase
        
    Returns:
        dict: Interpretasi hasil dengan level, kode, deskripsi, dan rekomendasi
    """
    if cf_percentage >= 81:
        return {
            'level': 'Kecanduan Berat',
            'code': 'P3',
            'description': 'Kecanduan game online tingkat berat dengan durasi bermain >8 jam/hari',
            'recommendation': 'Terapi perilaku (CBT), detoks digital, dukungan keluarga. Segera konsultasi dengan psikolog atau psikiater untuk penanganan intensif.',
            'color': 'danger',
            'icon': 'exclamation-triangle-fill'
        }
    elif cf_percentage >= 61:
        return {
            'level': 'Kecanduan Sedang',
            'code': 'P2', 
            'description': 'Kecanduan game online tingkat sedang dengan durasi bermain 4-8 jam/hari',
            'recommendation': 'Konsultasi psikolog, tetapkan jadwal bermain ketat. Mulai program detoks digital bertahap dan cari dukungan dari keluarga atau teman.',
            'color': 'warning',
            'icon': 'exclamation-triangle'
        }
    elif cf_percentage >= 40:
        return {
            'level': 'Kecanduan Ringan',
            'code': 'P1',
            'description': 'Kecanduan game online tingkat ringan dengan durasi bermain 2-4 jam/hari', 
            'recommendation': 'Batasi waktu bermain (<2 jam/hari), alihkan ke hobi fisik. Buat jadwal harian yang seimbang antara gaming dan aktivitas lain.',
            'color': 'info',
            'icon': 'info-circle'
        }
    else:
        return {
            'level': 'Tidak Terdeteksi Kecanduan',
            'code': 'P0',
            'description': 'Tidak terdeteksi kecanduan game online',
            'recommendation': 'Pertahankan pola bermain yang sehat. Tetap waspadai tanda-tanda kecanduan dan jaga keseimbangan antara gaming dan aktivitas lain.',
            'color': 'success',
            'icon': 'check-circle-fill'
        }

def calculate_certainty_factor(answers_data):
    """
    Menghitung Certainty Factor berdasarkan data jawaban lengkap
    
    Args:
        answers_data (list): List jawaban dengan format:
            [{'symptom_id': int, 'cf_expert': float, 'cf_user': float}, ...]
            
    Returns:
        dict: Hasil perhitungan CF lengkap
    """
    if not answers_data:
        return {
            'cf_value': 0.0,
            'cf_percentage': 0.0,
            'interpretation': interpret_cf_result(0.0),
            'symptom_cfs': []
        }
    
    # Hitung CF untuk setiap gejala
    symptom_cfs = []
    cf_values = []
    
    for answer in answers_data:
        cf_symptom = calculate_symptom_cf(answer['cf_expert'], answer['cf_user'])
        cf_values.append(cf_symptom)
        
        symptom_cfs.append({
            'symptom_id': answer['symptom_id'],
            'cf_expert': answer['cf_expert'],
            'cf_user': answer['cf_user'],
            'cf_combined': cf_symptom
        })
    
    # Gabungkan semua CF
    final_cf = combine_certainty_factors(cf_values)
    cf_percentage = get_cf_percentage(final_cf)
    
    return {
        'cf_value': final_cf,
        'cf_percentage': cf_percentage,
        'interpretation': interpret_cf_result(cf_percentage),
        'symptom_cfs': symptom_cfs
    }

# Skala nilai user sesuai Tabel 3 dalam penelitian
USER_SCALE_MAP = {
    'Sangat yakin': 1.0,
    'Yakin': 0.8,
    'Cukup yakin': 0.6,
    'Kadang-kadang': 0.4,
    'Jarang': 0.2,
    'Tidak pernah': 0.0
}

def get_user_cf_from_scale(scale_text):
    """
    Konversi skala teks ke nilai CF user sesuai Tabel 3
    
    Args:
        scale_text (str): Teks skala dari user
        
    Returns:
        float: Nilai CF yang sesuai (0.0 - 1.0)
    """
    return USER_SCALE_MAP.get(scale_text, 0.0)

def validate_cf_input(cf_value):
    """
    Validasi input CF untuk memastikan dalam rentang yang benar
    
    Args:
        cf_value: Input yang akan divalidasi
        
    Returns:
        float: CF value yang sudah divalidasi
        
    Raises:
        ValueError: Jika input tidak valid
    """
    try:
        cf = float(cf_value)
        if 0.0 <= cf <= 1.0:
            return cf
        else:
            raise ValueError(f"CF value {cf} must be between 0.0 and 1.0")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid CF value format: {cf_value}") from e