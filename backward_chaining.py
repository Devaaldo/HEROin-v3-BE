from models import db, Question, HypothesisQuestion, Hypothesis, UserHypothesis

def get_questions_for_hypothesis(hypothesis_ids):
    """
    Implementasi Backward Chaining untuk mendapatkan pertanyaan-pertanyaan
    yang terkait dengan hipotesis yang dipilih pengguna.
    
    Args:
        hypothesis_ids (list): Daftar ID hipotesis yang dipilih oleh pengguna
        
    Returns:
        list: Daftar ID pertanyaan yang perlu dijawab
    """
    # Inisialisasi backend knowledge base
    # Tentukan hubungan antara hipotesis dan pertanyaan jika belum ada
    initialize_knowledge_base()
    
    # Dapatkan pertanyaan-pertanyaan untuk hipotesis yang dipilih
    questions = set()
    
    for hypothesis_id in hypothesis_ids:
        hypothesis_questions = HypothesisQuestion.query.filter_by(hypothesis_id=hypothesis_id).all()
        for hq in hypothesis_questions:
            questions.add(hq.question_id)
    
    return list(questions)

def initialize_knowledge_base():
    """
    Inisialisasi knowledge base yang menghubungkan hipotesis dengan pertanyaan
    yang relevan jika hubungan tersebut belum ada di database.
    """
    # Periksa apakah knowledge base sudah diinisialisasi
    if HypothesisQuestion.query.count() > 0:
        return
    
    # Dapatkan semua hipotesis dan pertanyaan
    hypotheses = Hypothesis.query.all()
    questions = Question.query.all()
    
    # Mapping nama hipotesis ke ID
    hypothesis_map = {h.name: h.id for h in hypotheses}
    
    # Aturan untuk menentukan pertanyaan mana yang terkait dengan hipotesis mana
    rules = {
        'Penurunan Prestasi Akademik': [
            'Apakah Anda sering menunda atau tidak mengerjakan tugas kuliah karena bermain game online?',
            'Apakah nilai atau IPK Anda menurun sejak mulai bermain game online secara intensif?',
            'Apakah Anda sering tidak fokus saat kuliah karena memikirkan game online?',
            'Apakah Anda sering bolos kuliah untuk bermain game online?'
        ],
        'Gangguan Pola Tidur': [
            'Apakah Anda sering bermain game online hingga larut malam (di atas jam 12 malam)?',
            'Apakah Anda sering merasa kantuk di siang hari karena kurang tidur akibat bermain game online?',
            'Apakah jadwal tidur Anda menjadi tidak teratur karena bermain game online?'
        ],
        'Masalah Kesehatan Fisik': [
            'Apakah Anda sering mengalami sakit kepala setelah bermain game online dalam waktu lama?',
            'Apakah Anda mengalami mata kering atau penglihatan kabur setelah bermain game online?',
            'Apakah Anda sering mengalami nyeri pada punggung, leher, atau tangan setelah bermain game online?'
        ],
        'Isolasi Sosial': [
            'Apakah Anda lebih memilih bermain game online daripada bertemu dengan teman-teman di dunia nyata?',
            'Apakah hubungan Anda dengan teman atau keluarga menjadi renggang karena terlalu fokus pada game online?',
            'Apakah Anda merasa lebih nyaman berinteraksi dengan orang lain secara online daripada secara langsung?'
        ],
        'Masalah Keuangan': [
            'Apakah Anda sering menghabiskan uang untuk pembelian dalam game (skins, item, battle pass, dll)?',
            'Apakah pengeluaran untuk game online menyebabkan Anda mengalami kesulitan keuangan?'
        ],
        'Kecemasan dan Depresi': [
            'Apakah Anda merasa cemas atau gelisah ketika tidak bisa bermain game online?',
            'Apakah Anda merasa mood Anda terganggu ketika tidak bisa bermain game online?',
            'Apakah Anda merasa cemas jika melewatkan event atau update terbaru dalam game online?'
        ]
    }
    
    # Buat mapping pertanyaan teks ke ID
    question_map = {}
    for q in questions:
        question_map[q.text] = q.id
    
    # Buat hubungan antara hipotesis dan pertanyaan
    for hypothesis_name, question_texts in rules.items():
        hypothesis_id = hypothesis_map.get(hypothesis_name)
        if not hypothesis_id:
            continue
        
        for question_text in question_texts:
            question_id = question_map.get(question_text)
            if not question_id:
                continue
            
            # Periksa apakah hubungan sudah ada
            existing = HypothesisQuestion.query.filter_by(
                hypothesis_id=hypothesis_id,
                question_id=question_id
            ).first()
            
            if not existing:
                hq = HypothesisQuestion(hypothesis_id=hypothesis_id, question_id=question_id)
                db.session.add(hq)
    
    db.session.commit()