from models import db, Answer, Question, Symptom, Result
from sqlalchemy import func

def calculate_certainty_factor(user_id, result_id=None):
    """
    Menghitung Certainty Factor berdasarkan metodologi penelitian:
    1. CF_gejala = CF_pakar × CF_user
    2. CF_gabungan = CF1 + CF2 × (1 - CF1) untuk menggabungkan multiple CF
    3. CF_persentase = CF_gabungan × 100
    """
    if result_id:
        answers = Answer.query.filter_by(result_id=result_id).all()
    else:
        # Ambil hasil terbaru untuk user
        latest_result = Result.query.filter_by(user_id=user_id).order_by(Result.created_at.desc()).first()
        if not latest_result:
            return 0.0
        answers = Answer.query.filter_by(result_id=latest_result.id).all()
    
    if not answers:
        return 0.0
    
    # Kumpulkan semua CF kombinasi gejala
    cf_values = []
    
    for answer in answers:
        # CF_gejala = CF_pakar × CF_user (sesuai rumus [1] dalam penelitian)
        cf_gejala = answer.cf_combined  # Sudah dihitung saat menyimpan
        cf_values.append(cf_gejala)
    
    # Gabungkan semua CF menggunakan rumus penelitian
    cf_gabungan = combine_certainty_factors(cf_values)
    
    return cf_gabungan

def combine_certainty_factors(cf_values):
    """
    Menggabungkan multiple CF menggunakan rumus dari penelitian:
    CF_gabungan = CF1 + CF2 × (1 - CF1)
    
    Untuk lebih dari 2 CF, diterapkan secara berurutan:
    CF_temp = CF1 + CF2 × (1 - CF1)
    CF_gabungan = CF_temp + CF3 × (1 - CF_temp)
    dst...
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
        
        # Rumus: CF_gabungan = CF1 + CF2 × (1 - CF1)
        cf_gabungan = cf_gabungan + (cf_next * (1 - cf_gabungan))
    
    # Pastikan nilai antara 0 dan 1
    return max(0.0, min(1.0, cf_gabungan))

def get_cf_percentage(cf_value):
    """
    Mengkonversi CF value ke persentase sesuai penelitian:
    CF_persentase = CF_gabungan × 100
    """
    return cf_value * 100

def interpret_cf_result(cf_percentage):
    """
    Interpretasi hasil CF berdasarkan threshold penelitian:
    - Kecanduan Ringan (P1): 40-60%
    - Kecanduan Sedang (P2): 61-80% 
    - Kecanduan Berat (P3): 81-100%
    - Tidak Terdeteksi: <40%
    """
    if cf_percentage >= 81:
        return {
            'level': 'Kecanduan Berat',
            'code': 'P3',
            'description': 'Kecanduan game online tingkat berat dengan durasi bermain >8 jam/hari',
            'recommendation': 'Terapi perilaku (CBT), detoks digital, dukungan keluarga. Segera konsultasi dengan psikolog atau psikiater untuk penanganan intensif.'
        }
    elif cf_percentage >= 61:
        return {
            'level': 'Kecanduan Sedang',
            'code': 'P2', 
            'description': 'Kecanduan game online tingkat sedang dengan durasi bermain 4-8 jam/hari',
            'recommendation': 'Konsultasi psikolog, tetapkan jadwal bermain ketat. Mulai program detoks digital bertahap dan cari dukungan dari keluarga atau teman.'
        }
    elif cf_percentage >= 40:
        return {
            'level': 'Kecanduan Ringan',
            'code': 'P1',
            'description': 'Kecanduan game online tingkat ringan dengan durasi bermain 2-4 jam/hari', 
            'recommendation': 'Batasi waktu bermain (<2 jam/hari), alihkan ke hobi fisik. Buat jadwal harian yang seimbang antara gaming dan aktivitas lain.'
        }
    else:
        return {
            'level': 'Tidak Terdeteksi Kecanduan',
            'code': 'P0',
            'description': 'Tidak terdeteksi kecanduan game online',
            'recommendation': 'Pertahankan pola bermain yang sehat. Tetap waspadai tanda-tanda kecanduan dan jaga keseimbangan antara gaming dan aktivitas lain.'
        }

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
    return cf_expert * cf_user

# Skala nilai user sesuai Tabel 3 dalam penelitian
USER_SCALE_MAP = {
    'Sangat yakin': 1.0,
    'Yakin': 0.8,
    'Cukup Yakin': 0.6,
    'Kadang-kadang': 0.4,
    'Jarang': 0.2,
    'Tidak Pernah': 0.0
}

def get_user_cf_from_scale(scale_text):
    """
    Konversi skala teks ke nilai CF user sesuai Tabel 3
    """
    return USER_SCALE_MAP.get(scale_text, 0.0)