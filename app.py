from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import json
import pandas as pd
from datetime import datetime
import numpy as np
from io import BytesIO
import xlsxwriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
CORS(app)  # Mengaktifkan CORS untuk seluruh domain

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:sql123@localhost/heroin_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    angkatan = db.Column(db.String(10), nullable=False)
    program_studi = db.Column(db.String(100), nullable=False)
    domisili = db.Column(db.String(100), nullable=False)
    jenis_kelamin = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nama': self.nama,
            'usia': self.usia,
            'angkatan': self.angkatan,
            'programStudi': self.program_studi,
            'domisili': self.domisili,
            'jenisKelamin': self.jenis_kelamin,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Hypothesis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description
        }

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey('hypothesis.id'), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=False)
    
    hypothesis = db.relationship('Hypothesis', backref=db.backref('questions', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'hypothesisId': self.hypothesis_id,
            'code': self.code,
            'text': self.text
        }

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey('hypothesis.id'), nullable=False)
    cf_value = db.Column(db.Float, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('results', lazy=True))
    hypothesis = db.relationship('Hypothesis', backref=db.backref('results', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'hypothesisId': self.hypothesis_id,
            'cfValue': self.cf_value,
            'diagnosis': self.diagnosis,
            'recommendation': self.recommendation,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    cf_value = db.Column(db.Float, nullable=False)
    
    result = db.relationship('Result', backref=db.backref('answers', lazy=True))
    question = db.relationship('Question', backref=db.backref('answers', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'resultId': self.result_id,
            'questionId': self.question_id,
            'cfValue': self.cf_value
        }

# Utility functions untuk Backward Chaining dan Certainty Factor
class BackwardChaining:
    def __init__(self, hypothesis_id):
        self.hypothesis_id = hypothesis_id
        self.questions = Question.query.filter_by(hypothesis_id=hypothesis_id).all()
    
    # Method ini yang digunakan dalam submit_questionnaire
    def process_answers(self, answers):
        # Implementasi backward chaining sederhana
        # Dalam kasus ini, kita akan menghitung certainty factor berdasarkan jawaban
        if not answers:
            return 0
            
        # Validasi nilai input
        try:
            cf_values = [float(ans['value']) for ans in answers]
            # Tambahkan validasi untuk memastikan nilai valid
            cf_values = [cf for cf in cf_values if -1.0 <= cf <= 1.0]  # Filter nilai yang valid
            
            if not cf_values:  # Jika tidak ada nilai yang valid
                return 0
                
            # Kombinasikan semua CF jawaban
            cf_combined = self.combine_cf_values(cf_values)
            
            return cf_combined
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error saat memproses jawaban: {e}")
            return 0  # Nilai default jika terjadi error
    
    def combine_cf_values(self, cf_values):
        if not cf_values:
            return 0
            
        # Implementasi metode kombinasi CF yang diperbaiki
        cf_result = cf_values[0]
        
        for cf in cf_values[1:]:
            # Jika keduanya positif
            if cf_result > 0 and cf > 0:
                cf_result = cf_result + cf * (1 - cf_result)
            # Jika keduanya negatif
            elif cf_result < 0 and cf < 0:
                cf_result = cf_result + cf * (1 + cf_result)
            # Jika berbeda tanda atau salah satu atau keduanya adalah 0
            else:
                # Tambahkan pengecekan untuk menghindari pembagian dengan nol
                denominator = 1 - min(abs(cf_result), abs(cf))
                if denominator == 0:  # Jika denominator 0, gunakan nilai alternatif
                    cf_result = (cf_result + cf) / 2  # Ambil rata-rata sebagai alternatif
                else:
                    cf_result = (cf_result + cf) / denominator
                    
        return cf_result
        
    def get_diagnosis(self, cf_value):
    # Berikan diagnosis berdasarkan nilai CF
        if cf_value >= 0.8:
            return "Kecanduan game online tingkat sangat tinggi", "Segera kurangi waktu bermain game dan cari bantuan profesional. Pertimbangkan untuk berkonsultasi dengan psikolog atau konselor kampus untuk strategi penanganan kecanduan."
        elif cf_value >= 0.6:
            return "Kecanduan game online tingkat tinggi", "Anda menunjukkan tanda-tanda kecanduan yang signifikan. Tetapkan batasan waktu bermain game, aktifkan timer, dan cari aktivitas alternatif."
        elif cf_value >= 0.4:
            return "Kecanduan game online tingkat sedang", "Anda menunjukkan beberapa tanda kecanduan. Cobalah membatasi waktu bermain game dan tetapkan prioritas utama pada kegiatan akademik."
        elif cf_value >= 0.2:
            return "Kecanduan game online tingkat rendah", "Anda menunjukkan sedikit tanda kecanduan. Pertahankan keseimbangan antara bermain game dan aktivitas lainnya."
        else:
            return "Tidak terdeteksi kecanduan game online", "Anda tidak menunjukkan tanda-tanda kecanduan game online. Tetap pertahankan keseimbangan aktivitas Anda."

# Fungsi untuk menghasilkan laporan
def generate_excel_report(result_id):
    # Ambil data hasil
    result = Result.query.get(result_id)
    
    if not result:
        return None
    
    user = User.query.get(result.user_id)
    hypothesis = Hypothesis.query.get(result.hypothesis_id)
    answers = Answer.query.filter_by(result_id=result_id).all()
    
    # Buat workbook Excel
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Hasil Analisis')
    
    # Format
    title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#9630FB', 'color': 'white', 'border': 1})
    cell_format = workbook.add_format({'border': 1})
    
    # Judul
    worksheet.merge_range('A1:H1', 'LAPORAN HASIL ANALISIS KECANDUAN GAME ONLINE', title_format)
    worksheet.merge_range('A2:H2', 'Sistem Pakar HEROin', title_format)
    
    # Informasi Pengguna
    worksheet.merge_range('A4:B4', 'Informasi Pengguna:', workbook.add_format({'bold': True}))
    
    worksheet.write('A5', 'Nama:', workbook.add_format({'bold': True}))
    worksheet.write('B5', user.nama)
    
    worksheet.write('A6', 'Usia:', workbook.add_format({'bold': True}))
    worksheet.write('B6', user.usia)
    
    worksheet.write('A7', 'Program Studi:', workbook.add_format({'bold': True}))
    worksheet.write('B7', user.program_studi)
    
    worksheet.write('A8', 'Angkatan:', workbook.add_format({'bold': True}))
    worksheet.write('B8', user.angkatan)
    
    worksheet.write('A9', 'Jenis Kelamin:', workbook.add_format({'bold': True}))
    worksheet.write('B9', user.jenis_kelamin)
    
    worksheet.write('A10', 'Domisili:', workbook.add_format({'bold': True}))
    worksheet.write('B10', user.domisili)
    
    # Hasil Analisis
    worksheet.merge_range('A12:H12', 'Hasil Analisis:', workbook.add_format({'bold': True}))
    
    worksheet.write('A13', 'Hipotesis:', workbook.add_format({'bold': True}))
    worksheet.merge_range('B13:H13', hypothesis.description)
    
    worksheet.write('A14', 'Nilai CF:', workbook.add_format({'bold': True}))
    worksheet.write('B14', f'{result.cf_value * 100:.2f}%')
    
    worksheet.write('A15', 'Diagnosis:', workbook.add_format({'bold': True}))
    worksheet.merge_range('B15:H15', result.diagnosis)
    
    worksheet.write('A16', 'Rekomendasi:', workbook.add_format({'bold': True}))
    worksheet.merge_range('B16:H16', result.recommendation)
    
    # Detail Jawaban
    worksheet.merge_range('A18:H18', 'Detail Jawaban:', workbook.add_format({'bold': True}))
    
    # Header tabel
    worksheet.write('A19', 'No', header_format)
    worksheet.write('B19', 'Kode', header_format)
    worksheet.merge_range('C19:F19', 'Pertanyaan', header_format)
    worksheet.write('G19', 'Nilai CF', header_format)
    worksheet.write('H19', 'Persentase', header_format)
    
    # Isi tabel
    row = 19
    for i, answer in enumerate(answers):
        question = Question.query.get(answer.question_id)
        
        row += 1
        worksheet.write(row, 0, i+1, cell_format)
        worksheet.write(row, 1, question.code, cell_format)
        worksheet.merge_range(row, 2, row, 5, question.text, cell_format)
        worksheet.write(row, 6, answer.cf_value, cell_format)
        worksheet.write(row, 7, f'{answer.cf_value * 100:.2f}%', cell_format)
    
    # Pengaturan lebar kolom
    worksheet.set_column('A:A', 5)
    worksheet.set_column('B:B', 10)
    worksheet.set_column('C:F', 15)
    worksheet.set_column('G:H', 10)
    
    workbook.close()
    
    output.seek(0)
    return output

def generate_pdf_report(result_id):
    # Ambil data hasil
    result = Result.query.get(result_id)
    
    if not result:
        return None
    
    user = User.query.get(result.user_id)
    hypothesis = Hypothesis.query.get(result.hypothesis_id)
    answers = Answer.query.filter_by(result_id=result_id).all()
    
    # Buat file PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Judul
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center
    elements.append(Paragraph("LAPORAN HASIL ANALISIS KECANDUAN GAME ONLINE", title_style))
    elements.append(Paragraph("Sistem Pakar HEROin", styles['Heading2']))
    elements.append(Paragraph(" ", styles['Normal']))  # Spasi
    
    # Informasi Pengguna
    elements.append(Paragraph("Informasi Pengguna:", styles['Heading3']))
    
    user_data = [
        ["Nama", ": " + user.nama],
        ["Usia", ": " + str(user.usia)],
        ["Program Studi", ": " + user.program_studi],
        ["Angkatan", ": " + user.angkatan],
        ["Jenis Kelamin", ": " + user.jenis_kelamin],
        ["Domisili", ": " + user.domisili]
    ]
    
    user_table = Table(user_data, colWidths=[100, 400])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(user_table)
    elements.append(Paragraph(" ", styles['Normal']))  # Spasi
    
    # Hasil Analisis
    elements.append(Paragraph("Hasil Analisis:", styles['Heading3']))
    
    result_data = [
        ["Hipotesis", ": " + hypothesis.description],
        ["Nilai CF", ": " + f'{result.cf_value * 100:.2f}%'],
        ["Diagnosis", ": " + result.diagnosis],
        ["Rekomendasi", ": " + result.recommendation]
    ]
    
    result_table = Table(result_data, colWidths=[100, 400])
    result_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(result_table)
    elements.append(Paragraph(" ", styles['Normal']))  # Spasi
    
    # Detail Jawaban
    elements.append(Paragraph("Detail Jawaban:", styles['Heading3']))
    
    # Header tabel
    answer_data = [["No", "Kode", "Pertanyaan", "Nilai CF", "Persentase"]]
    
    # Isi tabel
    for i, answer in enumerate(answers):
        question = Question.query.get(answer.question_id)
        answer_data.append([
            str(i+1),
            question.code,
            question.text,
            str(answer.cf_value),
            f'{answer.cf_value * 100:.2f}%'
        ])
    
    answer_table = Table(answer_data, colWidths=[30, 50, 320, 50, 80])
    answer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(answer_table)
    
    # Tanggal dan waktu cetak
    elements.append(Paragraph(" ", styles['Normal']))  # Spasi
    elements.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# API Endpoints
@app.route('/api/user-info', methods=['POST'])
def save_user_info():
    data = request.json
    
    # Cek apakah user sudah ada (berdasarkan nama)
    existing_user = User.query.filter_by(nama=data['nama']).first()
    
    if existing_user:
        # Update data user yang sudah ada
        existing_user.usia = data['usia']
        existing_user.angkatan = data['angkatan']
        existing_user.program_studi = data['programStudi']
        existing_user.domisili = data['domisili']
        existing_user.jenis_kelamin = data['jenisKelamin']
        db.session.commit()
        
        return jsonify({'id': existing_user.id, 'message': 'Data user berhasil diperbarui'})
    else:
        # Buat user baru
        new_user = User(
            nama=data['nama'],
            usia=data['usia'],
            angkatan=data['angkatan'],
            program_studi=data['programStudi'],
            domisili=data['domisili'],
            jenis_kelamin=data['jenisKelamin']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'id': new_user.id, 'message': 'Data user berhasil disimpan'})

@app.route('/api/hypotheses', methods=['GET'])
def get_hypotheses():
    hypotheses = Hypothesis.query.all()
    return jsonify([h.to_dict() for h in hypotheses])

@app.route('/api/selected-hypothesis', methods=['POST'])
def save_selected_hypothesis():
    data = request.json
    
    # Ambil user berdasarkan nama
    user = User.query.filter_by(nama=data['userId']).first()
    
    if not user:
        return jsonify({'error': 'User tidak ditemukan'}), 404
    
    # Simpan hipotesis yang dipilih (akan digunakan saat membuat hasil)
    # Dalam kasus ini, kita hanya menyimpan ke session
    
    return jsonify({'message': 'Hipotesis berhasil disimpan'})

@app.route('/api/questions/<hypothesis_id>', methods=['GET'])
def get_questions(hypothesis_id):
    questions = Question.query.filter_by(hypothesis_id=hypothesis_id).all()
    return jsonify([q.to_dict() for q in questions])

@app.route('/api/submit-questionnaire', methods=['POST'])
def submit_questionnaire():
    data = request.json
    
    # Ambil user berdasarkan nama
    user = User.query.filter_by(nama=data['userId']).first()
    
    if not user:
        return jsonify({'error': 'User tidak ditemukan'}), 404
    
    # Proses jawaban dengan backward chaining dan certainty factor
    bc = BackwardChaining(data['hypothesisId'])
    cf_value = bc.process_answers(data['answers'])
    
    diagnosis, recommendation = bc.get_diagnosis(cf_value)
    
    # Simpan hasil
    result = Result(
        user_id=user.id,
        hypothesis_id=data['hypothesisId'],
        cf_value=cf_value,
        diagnosis=diagnosis,
        recommendation=recommendation
    )
    
    db.session.add(result)
    db.session.commit()
    
    # Simpan jawaban
    for answer_data in data['answers']:
        answer = Answer(
            result_id=result.id,
            question_id=answer_data['questionId'],
            cf_value=float(answer_data['value'])
        )
        db.session.add(answer)
    
    db.session.commit()
    
    return jsonify({'resultId': result.id, 'message': 'Kuesioner berhasil disimpan'})

@app.route('/api/result/<result_id>', methods=['GET'])
def get_result(result_id):
    result = Result.query.get(result_id)
    
    if not result:
        return jsonify({'error': 'Hasil tidak ditemukan'}), 404
    
    user = User.query.get(result.user_id)
    hypothesis = Hypothesis.query.get(result.hypothesis_id)
    answers = Answer.query.filter_by(result_id=result.id).all()
    
    # Ambil pertanyaan untuk setiap jawaban
    identified_symptoms = []
    for answer in answers:
        question = Question.query.get(answer.question_id)
        identified_symptoms.append({
            'symptomCode': question.code,
            'symptomText': question.text,
            'cfValue': answer.cf_value
        })
    
    result_data = {
        'id': result.id,
        'userInfo': user.to_dict(),
        'hypothesis': hypothesis.to_dict(),
        'cfValue': result.cf_value,
        'diagnosis': result.diagnosis,
        'recommendation': result.recommendation,
        'identifiedSymptoms': identified_symptoms,
        'createdAt': result.created_at.isoformat() if result.created_at else None
    }
    
    return jsonify(result_data)

@app.route('/api/download-report/<result_id>', methods=['GET'])
def download_report(result_id):
    format_type = request.args.get('format', 'excel')
    
    if format_type == 'excel':
        # Generate Excel report
        output = generate_excel_report(result_id)
        
        if not output:
            return jsonify({'error': 'Hasil tidak ditemukan'}), 404
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'hasil-analisis-{result_id}.xlsx'
        )
    else:
        # Generate PDF report
        output = generate_pdf_report(result_id)
        
        if not output:
            return jsonify({'error': 'Hasil tidak ditemukan'}), 404
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'hasil-analisis-{result_id}.pdf'
        )

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    # Total responden
    total_respondents = User.query.count()
    
    # Rata-rata tingkat kecanduan
    results = Result.query.all()
    avg_addiction_level = 0
    if results:
        avg_addiction_level = sum(r.cf_value for r in results) / len(results) * 100
    
    # Jumlah kasus kecanduan tinggi
    high_addiction_cases = Result.query.filter(Result.cf_value >= 0.6).count()
    
    # Distribusi tingkat kecanduan
    addiction_levels = {
        'veryLow': Result.query.filter(Result.cf_value < 0.2).count(),
        'low': Result.query.filter(Result.cf_value >= 0.2, Result.cf_value < 0.4).count(),
        'medium': Result.query.filter(Result.cf_value >= 0.4, Result.cf_value < 0.6).count(),
        'high': Result.query.filter(Result.cf_value >= 0.6, Result.cf_value < 0.8).count(),
        'veryHigh': Result.query.filter(Result.cf_value >= 0.8).count()
    }
    
    # Responden berdasarkan program studi
    program_studies = db.session.query(
        User.program_studi, 
        db.func.count(User.id).label('count')
    ).group_by(User.program_studi).all()
    
    by_program_studi = [
        {'programStudi': ps[0], 'count': ps[1]} 
        for ps in program_studies
    ]
    
    # Responden berdasarkan jenis kelamin
    by_gender = {
        'male': User.query.filter_by(jenis_kelamin='Laki-laki').count(),
        'female': User.query.filter_by(jenis_kelamin='Perempuan').count()
    }
    
    # Data responden (untuk tabel)
    respondents_data = []
    users = User.query.order_by(User.id.desc()).limit(10).all()
    
    for user in users:
        # Ambil hasil terbaru untuk user ini
        latest_result = Result.query.filter_by(user_id=user.id).order_by(Result.created_at.desc()).first()
        
        if latest_result:
            respondents_data.append({
                'id': user.id,
                'nama': user.nama,
                'programStudi': user.program_studi,
                'angkatan': user.angkatan,
                'jenisKelamin': user.jenis_kelamin,
                'cfValue': latest_result.cf_value,
                'resultId': latest_result.id
            })
    
    return jsonify({
        'totalRespondents': total_respondents,
        'averageAddictionLevel': avg_addiction_level,
        'highAddictionCases': high_addiction_cases,
        'addictionLevels': addiction_levels,
        'byProgramStudi': by_program_studi,
        'byGender': by_gender,
        'respondents': respondents_data
    })

@app.route('/api/download-all-reports', methods=['GET'])
def download_all_reports():
    format_type = request.args.get('format', 'excel')
    
    # Ambil semua hasil
    results = Result.query.all()
    
    if format_type == 'excel':
        # Buat workbook Excel untuk semua hasil
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Format
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#9630FB', 'color': 'white', 'border': 1})
        cell_format = workbook.add_format({'border': 1})
        
        # Worksheet ringkasan
        summary_ws = workbook.add_worksheet('Ringkasan')
        
        # Judul
        summary_ws.merge_range('A1:H1', 'RINGKASAN HASIL ANALISIS KECANDUAN GAME ONLINE', title_format)
        summary_ws.merge_range('A2:H2', 'Sistem Pakar HEROin', title_format)
        
        # Header tabel
        row = 3
        summary_ws.write(row, 0, 'No', header_format)
        summary_ws.write(row, 1, 'Nama', header_format)
        summary_ws.write(row, 2, 'Program Studi', header_format)
        summary_ws.write(row, 3, 'Angkatan', header_format)
        summary_ws.write(row, 4, 'Jenis Kelamin', header_format)
        summary_ws.write(row, 5, 'Diagnosis', header_format)
        summary_ws.write(row, 6, 'Nilai CF', header_format)
        summary_ws.write(row, 7, 'Tanggal', header_format)
        
        # Isi tabel
        for i, result in enumerate(results):
            user = User.query.get(result.user_id)
            
            row += 1
            summary_ws.write(row, 0, i+1, cell_format)
            summary_ws.write(row, 1, user.nama, cell_format)
            summary_ws.write(row, 2, user.program_studi, cell_format)
            summary_ws.write(row, 3, user.angkatan, cell_format)
            summary_ws.write(row, 4, user.jenis_kelamin, cell_format)
            summary_ws.write(row, 5, result.diagnosis, cell_format)
            summary_ws.write(row, 6, f'{result.cf_value * 100:.2f}%', cell_format)
            summary_ws.write(row, 7, result.created_at.strftime('%d-%m-%Y') if result.created_at else '', cell_format)
        
        # Pengaturan lebar kolom
        summary_ws.set_column('A:A', 5)
        summary_ws.set_column('B:B', 25)
        summary_ws.set_column('C:C', 30)
        summary_ws.set_column('D:D', 10)
        summary_ws.set_column('E:E', 15)
        summary_ws.set_column('F:F', 40)
        summary_ws.set_column('G:G', 10)
        summary_ws.set_column('H:H', 15)
        
        # Buat worksheet untuk setiap hasil
        for result in results:
            user = User.query.get(result.user_id)
            hypothesis = Hypothesis.query.get(result.hypothesis_id)
            answers = Answer.query.filter_by(result_id=result.id).all()
            
            # Buat worksheet
            ws_name = f'User_{user.id}'
            worksheet = workbook.add_worksheet(ws_name)
            
            # Judul
            worksheet.merge_range('A1:G1', 'HASIL ANALISIS KECANDUAN GAME ONLINE', title_format)
            worksheet.merge_range('A2:G2', 'Sistem Pakar HEROin', title_format)
            
            # Informasi Pengguna
            worksheet.merge_range('A4:B4', 'Informasi Pengguna:', workbook.add_format({'bold': True}))
            
            worksheet.write('A5', 'Nama:', workbook.add_format({'bold': True}))
            worksheet.write('B5', user.nama)
            
            worksheet.write('A6', 'Usia:', workbook.add_format({'bold': True}))
            worksheet.write('B6', user.usia)
            
            worksheet.write('A7', 'Program Studi:', workbook.add_format({'bold': True}))
            worksheet.write('B7', user.program_studi)
            
            worksheet.write('A8', 'Angkatan:', workbook.add_format({'bold': True}))
            worksheet.write('B8', user.angkatan)
            
            worksheet.write('A9', 'Jenis Kelamin:', workbook.add_format({'bold': True}))
            worksheet.write('B9', user.jenis_kelamin)
            
            worksheet.write('A10', 'Domisili:', workbook.add_format({'bold': True}))
            worksheet.write('B10', user.domisili)
            
            # Hasil Analisis
            worksheet.merge_range('A12:G12', 'Hasil Analisis:', workbook.add_format({'bold': True}))
            
            worksheet.write('A13', 'Hipotesis:', workbook.add_format({'bold': True}))
            worksheet.merge_range('B13:G13', hypothesis.description)
            
            worksheet.write('A14', 'Nilai CF:', workbook.add_format({'bold': True}))
            worksheet.write('B14', f'{result.cf_value * 100:.2f}%')
            
            worksheet.write('A15', 'Diagnosis:', workbook.add_format({'bold': True}))
            worksheet.merge_range('B15:G15', result.diagnosis)
            
            worksheet.write('A16', 'Rekomendasi:', workbook.add_format({'bold': True}))
            worksheet.merge_range('B16:G16', result.recommendation)
            
            # Detail Jawaban
            worksheet.merge_range('A18:G18', 'Detail Jawaban:', workbook.add_format({'bold': True}))
            
            # Header tabel
            worksheet.write('A19', 'No', header_format)
            worksheet.write('B19', 'Kode', header_format)
            worksheet.merge_range('C19:E19', 'Pertanyaan', header_format)
            worksheet.write('F19', 'Nilai CF', header_format)
            worksheet.write('G19', 'Persentase', header_format)
            
            # Isi tabel
            row = 19
            for i, answer in enumerate(answers):
                question = Question.query.get(answer.question_id)
                
                row += 1
                worksheet.write(row, 0, i+1, cell_format)
                worksheet.write(row, 1, question.code, cell_format)
                worksheet.merge_range(row, 2, row, 4, question.text, cell_format)
                worksheet.write(row, 5, answer.cf_value, cell_format)
                worksheet.write(row, 6, f'{answer.cf_value * 100:.2f}%', cell_format)
        
        workbook.close()
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='semua-hasil-analisis.xlsx'
        )
    else:
        # Membuat PDF untuk semua hasil mungkin terlalu besar,
        # Jadi kita akan membuat PDF yang berisi ringkasan saja
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Judul
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center
        elements.append(Paragraph("RINGKASAN HASIL ANALISIS KECANDUAN GAME ONLINE", title_style))
        elements.append(Paragraph("Sistem Pakar HEROin", styles['Heading2']))
        elements.append(Paragraph(" ", styles['Normal']))  # Spasi
        
        # Tabel ringkasan
        summary_data = [['No', 'Nama', 'Program Studi', 'Angkatan', 'Nilai CF', 'Diagnosis']]
        
        for i, result in enumerate(results):
            user = User.query.get(result.user_id)
            
            summary_data.append([
                str(i+1),
                user.nama,
                user.program_studi,
                user.angkatan,
                f'{result.cf_value * 100:.2f}%',
                result.diagnosis
            ])
        
        summary_table = Table(summary_data, colWidths=[30, 80, 100, 60, 60, 190])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(summary_table)
        
        # Statistik sederhana
        elements.append(Paragraph(" ", styles['Normal']))  # Spasi
        elements.append(Paragraph("Statistik:", styles['Heading3']))
        
        # Hitung statistik
        total_respondents = len(results)
        avg_addiction = sum(r.cf_value for r in results) / total_respondents * 100 if total_respondents > 0 else 0
        high_addiction = sum(1 for r in results if r.cf_value >= 0.6)
        
        stats_data = [
            ["Total Responden", ": " + str(total_respondents)],
            ["Rata-rata Tingkat Kecanduan", ": " + f'{avg_addiction:.2f}%'],
            ["Kasus Kecanduan Tinggi", ": " + str(high_addiction)]
        ]
        
        stats_table = Table(stats_data, colWidths=[200, 300])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ]))
        elements.append(stats_table)
        
        # Tanggal dan waktu cetak
        elements.append(Paragraph(" ", styles['Normal']))  # Spasi
        elements.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='semua-hasil-analisis.pdf'
        )

@app.route('/api/result/<result_id>', methods=['DELETE'])
def delete_result(result_id):
    try:
        # Cari result berdasarkan ID
        result = Result.query.get(result_id)
        
        if not result:
            return jsonify({'error': 'Hasil tidak ditemukan'}), 404
        
        # Hapus semua jawaban terkait
        Answer.query.filter_by(result_id=result.id).delete()
        
        # Simpan user_id sebelum menghapus result
        user_id = result.user_id
        
        # Hapus result
        db.session.delete(result)
        db.session.commit()
        
        # Periksa apakah user masih memiliki result lain
        remaining_results = Result.query.filter_by(user_id=user_id).count()
        
        # Jika tidak ada result lain, hapus juga user
        if remaining_results == 0:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
        
        return jsonify({'message': 'Data berhasil dihapus'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

# Inisialisasi database dan data awal (untuk development)
def initialize_database():
    # Buat tabel
    db.create_all()
    
    # Cek apakah data awal sudah ada
    if Hypothesis.query.count() == 0:
        # Tambahkan data hipotesis
        hypotheses = [
            Hypothesis(code='H1', description='Dampak negatif terhadap kesehatan fisik (gangguan tidur, sakit kepala, mata lelah)'),
            Hypothesis(code='H2', description='Dampak negatif terhadap kesehatan mental (kecemasan, depresi, mood swing)'),
            Hypothesis(code='H3', description='Dampak negatif terhadap performa akademik (penurunan nilai, absensi)'),
            Hypothesis(code='H4', description='Dampak negatif terhadap hubungan sosial (isolasi, konflik dengan teman/keluarga)'),
            Hypothesis(code='H5', description='Dampak negatif terhadap manajemen waktu (prokrastinasi, kehilangan waktu produktif)')
        ]
        
        db.session.add_all(hypotheses)
        db.session.commit()
        
        # Tambahkan data pertanyaan untuk hipotesis 1
        h1_questions = [
            Question(hypothesis_id=1, code='Q1-1', text='Saya sering merasa sakit kepala setelah bermain game online dalam waktu lama'),
            Question(hypothesis_id=1, code='Q1-2', text='Jam tidur saya terganggu karena bermain game online hingga larut malam'),
            Question(hypothesis_id=1, code='Q1-3', text='Mata saya sering terasa lelah dan kering setelah bermain game online'),
            Question(hypothesis_id=1, code='Q1-4', text='Saya merasakan nyeri pada pergelangan tangan atau jari setelah bermain game dalam waktu lama'),
            Question(hypothesis_id=1, code='Q1-5', text='Saya sering melewatkan waktu makan karena terlalu fokus bermain game online')
        ]
        
        # Tambahkan data pertanyaan untuk hipotesis 2
        h2_questions = [
            Question(hypothesis_id=2, code='Q2-1', text='Saya merasa cemas ketika tidak bisa bermain game online'),
            Question(hypothesis_id=2, code='Q2-2', text='Mood saya berubah-ubah (mudah marah/sedih) ketika kalah dalam game'),
            Question(hypothesis_id=2, code='Q2-3', text='Saya kesulitan berkonsentrasi pada kegiatan lain karena terus memikirkan game'),
            Question(hypothesis_id=2, code='Q2-4', text='Saya merasa tertekan ketika tidak mencapai target dalam game'),
            Question(hypothesis_id=2, code='Q2-5', text='Saya sering merasa tidak berharga di dunia nyata dibandingkan dengan pencapaian di game')
        ]
        
        # Tambahkan data pertanyaan untuk hipotesis 3
        h3_questions = [
            Question(hypothesis_id=3, code='Q3-1', text='Nilai akademik saya menurun sejak saya bermain game online secara intensif'),
            Question(hypothesis_id=3, code='Q3-2', text='Saya sering tidak mengerjakan tugas kuliah karena bermain game online'),
            Question(hypothesis_id=3, code='Q3-3', text='Saya pernah tidak masuk kuliah karena bermain game online semalaman'),
            Question(hypothesis_id=3, code='Q3-4', text='Saya sulit fokus saat kuliah karena memikirkan strategi atau level dalam game'),
            Question(hypothesis_id=3, code='Q3-5', text='Saya lebih memilih bermain game daripada belajar untuk ujian')
        ]
        
        # Tambahkan data pertanyaan untuk hipotesis 4
        h4_questions = [
            Question(hypothesis_id=4, code='Q4-1', text='Saya lebih memilih bermain game online daripada berkumpul dengan teman-teman'),
            Question(hypothesis_id=4, code='Q4-2', text='Keluarga saya sering mengeluhkan waktu yang saya habiskan untuk bermain game'),
            Question(hypothesis_id=4, code='Q4-3', text='Saya pernah berkonflik dengan teman/keluarga karena masalah game online'),
            Question(hypothesis_id=4, code='Q4-4', text='Saya merasa lebih nyaman berinteraksi dengan teman online daripada teman di dunia nyata'),
            Question(hypothesis_id=4, code='Q4-5', text='Saya menolak ajakan kegiatan sosial karena ingin bermain game online')
        ]
        
        # Tambahkan data pertanyaan untuk hipotesis 5
        h5_questions = [
            Question(hypothesis_id=5, code='Q5-1', text='Saya sering menunda-nunda pekerjaan penting karena bermain game online'),
            Question(hypothesis_id=5, code='Q5-2', text='Waktu bermain game online saya semakin bertambah dari waktu ke waktu'),
            Question(hypothesis_id=5, code='Q5-3', text='Saya sering bermain game online lebih lama dari yang saya rencanakan'),
            Question(hypothesis_id=5, code='Q5-4', text='Saya merasa waktu produktif saya banyak terbuang karena bermain game online'),
            Question(hypothesis_id=5, code='Q5-5', text='Saya kesulitan mengatur jadwal kegiatan sehari-hari karena terlalu banyak bermain game')
        ]
        
        db.session.add_all(h1_questions + h2_questions + h3_questions + h4_questions + h5_questions)
        db.session.commit()
        
        print("Data awal berhasil ditambahkan")

if __name__ == '__main__':
    # Panggil fungsi inisialisasi database dalam konteks aplikasi
    with app.app_context():
        initialize_database()
    
    app.run(debug=True)