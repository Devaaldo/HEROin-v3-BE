from models import db, Question, Rule, RuleSymptom, Hypothesis, Symptom

class BackwardChaining:
    """
    Implementasi Backward Chaining sesuai metodologi penelitian.
    
    Backward Chaining adalah penalaran yang dimulai dari level tertinggi 
    membangun suatu hipotesis, turun ke fakta level paling bawah yang dapat 
    mendukung hipotesis (penalaran dari atas kebawah).
    """
    
    def __init__(self, hypothesis_id):
        self.hypothesis_id = hypothesis_id
        self.hypothesis = Hypothesis.query.get(hypothesis_id)
        
        # Mapping rules berdasarkan penelitian
        self.rules_mapping = {
            1: {  # P1 - Kecanduan Ringan
                'rules': [
                    ['G1', 'G5'],                    # Rule 1: IF P1 THEN G1 AND G5
                    ['G1', 'G5', 'G10'],            # Rule 2: IF P1 THEN G1 AND G5 AND G10
                    ['G1', 'G5', 'G10', 'G3']       # Rule 3: IF P1 THEN G1 AND G5 AND G10 AND G3
                ],
                'dominant_symptoms': ['G1', 'G5', 'G10']
            },
            2: {  # P2 - Kecanduan Sedang
                'rules': [
                    ['G2', 'G3', 'G4'],             # Rule 1: IF P2 THEN G2 AND G3 AND G4
                    ['G2', 'G3', 'G4', 'G7'],       # Rule 2: IF P2 THEN G2 AND G3 AND G4 AND G7
                    ['G2', 'G3', 'G4', 'G7', 'G8'] # Rule 3: IF P2 THEN G2 AND G3 AND G4 AND G7 AND G8
                ],
                'dominant_symptoms': ['G2', 'G3', 'G4', 'G7', 'G8']
            },
            3: {  # P3 - Kecanduan Berat
                'rules': [
                    ['G6', 'G9'],                           # Rule 1: IF P3 THEN G6 AND G9
                    ['G6', 'G9', 'G11'],                    # Rule 2: IF P3 THEN G6 AND G9 AND G11
                    ['G6', 'G9', 'G11', 'G12'],            # Rule 3: IF P3 THEN G6 AND G9 AND G11 AND G12
                    ['G6', 'G9', 'G11', 'G12', 'G2']       # Rule 4: IF P3 THEN G6 AND G9 AND G11 AND G12 AND G2
                ],
                'dominant_symptoms': ['G6', 'G9', 'G11', 'G12']
            }
        }
        
    def get_required_symptoms(self):
        """
        Mendapatkan gejala-gejala yang diperlukan untuk hipotesis yang dipilih
        berdasarkan aturan backward chaining.
        
        Returns:
            list: Daftar kode gejala yang relevan untuk hipotesis
        """
        if self.hypothesis_id not in self.rules_mapping:
            return []
        
        # Ambil semua gejala yang terlibat dalam rules untuk hipotesis ini
        all_symptoms = set()
        rules = self.rules_mapping[self.hypothesis_id]['rules']
        
        for rule in rules:
            for symptom_code in rule:
                all_symptoms.add(symptom_code)
        
        return list(all_symptoms)
    
    def get_questions_for_hypothesis(self):
        """
        Mendapatkan pertanyaan-pertanyaan berdasarkan gejala yang diperlukan
        untuk memvalidasi hipotesis (backward chaining).
        
        Returns:
            list: Daftar pertanyaan dengan detail gejala
        """
        required_symptom_codes = self.get_required_symptoms()
        questions = []
        
        for symptom_code in required_symptom_codes:
            # Cari symptom berdasarkan kode
            symptom = Symptom.query.filter_by(code=symptom_code).first()
            if symptom:
                # Cari pertanyaan untuk symptom ini
                question = Question.query.filter_by(symptom_id=symptom.id).first()
                if question:
                    questions.append({
                        'id': question.id,
                        'text': question.text,
                        'symptom_id': symptom.id,
                        'symptom_code': symptom.code,
                        'symptom_description': symptom.description,
                        'cf_expert': symptom.cf_expert
                    })
        
        return questions
    
    def validate_hypothesis(self, user_answers):
        """
        Memvalidasi hipotesis berdasarkan jawaban user menggunakan rules.
        
        Args:
            user_answers (dict): Dictionary dengan symptom_code sebagai key 
                               dan cf_user sebagai value
                               
        Returns:
            dict: Hasil validasi dengan tingkat keyakinan
        """
        if self.hypothesis_id not in self.rules_mapping:
            return {'valid': False, 'confidence': 0.0, 'matched_rules': []}
        
        rules = self.rules_mapping[self.hypothesis_id]['rules']
        matched_rules = []
        rule_confidences = []
        
        # Evaluasi setiap rule
        for i, rule in enumerate(rules):
            rule_cf_values = []
            all_symptoms_present = True
            
            # Periksa setiap gejala dalam rule
            for symptom_code in rule:
                if symptom_code in user_answers and user_answers[symptom_code] > 0:
                    # Ambil CF expert untuk symptom ini
                    symptom = Symptom.query.filter_by(code=symptom_code).first()
                    if symptom:
                        # Hitung CF kombinasi: CF_pakar × CF_user
                        cf_combined = symptom.cf_expert * user_answers[symptom_code]
                        rule_cf_values.append(cf_combined)
                else:
                    all_symptoms_present = False
                    break
            
            # Jika semua gejala dalam rule terpenuhi
            if all_symptoms_present and rule_cf_values:
                # Gabungkan CF untuk rule ini
                rule_confidence = self._combine_rule_cf(rule_cf_values)
                rule_confidences.append(rule_confidence)
                matched_rules.append({
                    'rule_number': i + 1,
                    'symptoms': rule,
                    'confidence': rule_confidence
                })
        
        # Hitung confidence keseluruhan dari rules yang cocok
        if rule_confidences:
            # Gunakan CF maksimal dari rules yang cocok
            overall_confidence = max(rule_confidences)
        else:
            overall_confidence = 0.0
        
        return {
            'valid': overall_confidence > 0,
            'confidence': overall_confidence,
            'confidence_percentage': overall_confidence * 100,
            'matched_rules': matched_rules,
            'total_rules_matched': len(matched_rules)
        }
    
    def _combine_rule_cf(self, cf_values):
        """
        Menggabungkan CF values dalam satu rule menggunakan rumus penelitian:
        CF_gabungan = CF1 + CF2 × (1 - CF1)
        """
        if not cf_values:
            return 0.0
        
        if len(cf_values) == 1:
            return cf_values[0]
        
        combined_cf = cf_values[0]
        
        for i in range(1, len(cf_values)):
            cf_next = cf_values[i]
            combined_cf = combined_cf + (cf_next * (1 - combined_cf))
        
        return max(0.0, min(1.0, combined_cf))
    
    def get_diagnosis_recommendation(self, cf_percentage):
        """
        Mendapatkan diagnosis dan rekomendasi berdasarkan tingkat CF
        sesuai dengan threshold penelitian.
        """
        if cf_percentage >= 81:
            return (
                "Kecanduan Game Online Tingkat Berat",
                "Terapi perilaku (CBT), detoks digital, dukungan keluarga. Segera konsultasi dengan psikolog atau psikiater untuk penanganan intensif."
            )
        elif cf_percentage >= 61:
            return (
                "Kecanduan Game Online Tingkat Sedang", 
                "Konsultasi psikolog, tetapkan jadwal bermain ketat. Mulai program detoks digital bertahap dan cari dukungan dari keluarga atau teman."
            )
        elif cf_percentage >= 40:
            return (
                "Kecanduan Game Online Tingkat Ringan",
                "Batasi waktu bermain (<2 jam/hari), alihkan ke hobi fisik. Buat jadwal harian yang seimbang antara gaming dan aktivitas lain."
            )
        else:
            return (
                "Tidak Terdeteksi Kecanduan Game Online",
                "Pertahankan pola bermain yang sehat. Tetap waspadai tanda-tanda kecanduan dan jaga keseimbangan antara gaming dan aktivitas lain."
            )
    
    def process_user_responses(self, responses):
        """
        Memproses respons user dan mengembalikan hasil analisis lengkap.
        
        Args:
            responses (list): List dictionary dengan format:
                [{'symptom_id': int, 'cf_user': float}, ...]
                
        Returns:
            dict: Hasil analisis lengkap
        """
        # Konversi responses ke format yang sesuai untuk validasi
        user_answers = {}
        symptom_details = []
        
        for response in responses:
            symptom = Symptom.query.get(response['symptom_id'])
            if symptom:
                user_answers[symptom.code] = response['cf_user']
                
                # Hitung CF kombinasi
                cf_combined = symptom.cf_expert * response['cf_user']
                
                symptom_details.append({
                    'symptom_id': symptom.id,
                    'symptom_code': symptom.code,
                    'symptom_text': symptom.description,
                    'cf_expert': symptom.cf_expert,
                    'cf_user': response['cf_user'],
                    'cf_combined': cf_combined
                })
        
        # Validasi hipotesis
        validation_result = self.validate_hypothesis(user_answers)
        
        # Dapatkan diagnosis dan rekomendasi
        diagnosis, recommendation = self.get_diagnosis_recommendation(
            validation_result['confidence_percentage']
        )
        
        return {
            'hypothesis_id': self.hypothesis_id,
            'hypothesis_name': self.hypothesis.name if self.hypothesis else '',
            'cf_value': validation_result['confidence'],
            'cf_percentage': validation_result['confidence_percentage'],
            'diagnosis': diagnosis,
            'recommendation': recommendation,
            'symptom_details': symptom_details,
            'matched_rules': validation_result['matched_rules'],
            'validation_successful': validation_result['valid']
        }