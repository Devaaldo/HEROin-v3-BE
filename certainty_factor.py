from models import db, Answer, Question, Impact
from sqlalchemy import func

def calculate_certainty_factor(user_id):
    answers = Answer.query.filter_by(user_id=user_id).all()
    
    # Kelompokkan jawaban berdasarkan dampak
    impact_answers = {}
    
    for answer in answers:
        question = Question.query.get(answer.question_id)
        impact_id = question.impact_id
        
        if impact_id not in impact_answers:
            impact_answers[impact_id] = []
        
        impact_answers[impact_id].append(answer.certainty_value)
    
    # Hitung certainty factor untuk setiap dampak
    impact_certainties = {}
    
    for impact_id, certainty_values in impact_answers.items():
        combined_cf = combine_certainty_factors(certainty_values)
        impact_certainties[impact_id] = combined_cf
    
    return impact_certainties

def combine_certainty_factors(certainty_values):
    if not certainty_values:
        return 0.0
    
    # Jika hanya ada satu nilai CF, maka langsung kembalikan nilai tersebut
    if len(certainty_values) == 1:
        return certainty_values[0]
    
    # Mengurutkan nilai dari yang terbesar ke terkecil
    certainty_values.sort(reverse=True)
    
    # Inisialisasi dengan nilai pertama
    combined_cf = certainty_values[0]
    
    # Gabungkan dengan nilai-nilai selanjutnya
    for cf in certainty_values[1:]:
        # Formula kombinasi CF
        if combined_cf > 0 and cf > 0:
            # Jika keduanya positif
            combined_cf = combined_cf + cf * (1 - combined_cf)
        elif combined_cf < 0 and cf < 0:
            # Jika keduanya negatif
            combined_cf = combined_cf + cf * (1 + combined_cf)
        else:
            # Jika berbeda tanda
            denominator = 1 - min(abs(combined_cf), abs(cf))
            if denominator == 0:
                # Jika penyebut nol, cari alternatif untuk menghindari pembagian dengan nol
                combined_cf = (combined_cf + cf) / 2  # Gunakan rata-rata sebagai alternatif
            else:
                combined_cf = (combined_cf + cf) / denominator
    
    return combined_cf