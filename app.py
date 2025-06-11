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
from models import db, User, Hypothesis, Symptom, Rule, RuleSymptom, Question, Result, Answer
from backward_chaining import BackwardChaining
from certainty_factor import calculate_certainty_factor, combine_certainty_factors

app = Flask(__name__)
CORS(app)

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:sql123@localhost/heroin_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database dengan models yang sudah diimport
db.init_app(app)

@app.route('/api/user-info', methods=['POST'])
def save_user_info():
    data = request.json
    
    existing_user = User.query.filter_by(nama=data['nama']).first()
    
    if existing_user:
        existing_user.usia = data['usia']
        existing_user.angkatan = data['angkatan']
        existing_user.program_studi = data['programStudi']
        existing_user.domisili = data['domisili']
        existing_user.jenis_kelamin = data['jenisKelamin']
        db.session.commit()
        
        return jsonify({'id': existing_user.id, 'message': 'Data user berhasil diperbarui'})
    else:
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
    """Endpoint untuk menyimpan hipotesis yang dipilih user"""
    try:
        data = request.json
        print(f"Received hypothesis data: {data}")
        
        if not data.get('userId') or not data.get('hypothesisId'):
            return jsonify({'error': 'UserId dan HypothesisId harus diisi'}), 400
        
        hypothesis = Hypothesis.query.get(data['hypothesisId'])
        if not hypothesis:
            return jsonify({'error': 'Hipotesis tidak ditemukan'}), 404
        
        return jsonify({
            'message': 'Hipotesis berhasil dipilih',
            'hypothesisId': data['hypothesisId'],
            'hypothesisName': hypothesis.name
        }), 200
        
    except Exception as e:
        print(f"Error in save_selected_hypothesis: {str(e)}")
        return jsonify({'error': f'Terjadi kesalahan server: {str(e)}'}), 500

@app.route('/api/questions/<hypothesis_id>', methods=['GET'])
def get_questions(hypothesis_id):
    bc = BackwardChaining(int(hypothesis_id))
    questions = bc.get_questions_for_hypothesis()
    return jsonify(questions)

@app.route('/api/submit-questionnaire', methods=['POST'])
def submit_questionnaire():
    """Memproses kuesioner dengan BackwardChaining dan CertaintyFactor"""
    try:
        data = request.json
        
        # Ambil user
        user = User.query.filter_by(nama=data['userId']).first()
        if not user:
            return jsonify({'error': 'User tidak ditemukan'}), 404
        
        # Gunakan BackwardChaining dari file terpisah
        bc = BackwardChaining(data['hypothesisId'])
        
        # Format jawaban untuk processing
        responses = []
        for answer in data['answers']:
            responses.append({
                'symptom_id': answer['questionId'],  # Sesuaikan mapping
                'cf_user': float(answer['value'])
            })
        
        # Proses dengan BackwardChaining
        result_data = bc.process_user_responses(responses)
        
        # Simpan hasil
        result = Result(
            user_id=user.id,
            hypothesis_id=data['hypothesisId'],
            cf_value=result_data['cf_value'],
            cf_percentage=result_data['cf_percentage'],
            diagnosis=result_data['diagnosis'],
            recommendation=result_data['recommendation']
        )
        
        db.session.add(result)
        db.session.commit()
        
        # Simpan jawaban detail
        for symptom_detail in result_data['symptom_details']:
            answer = Answer(
                result_id=result.id,
                symptom_id=symptom_detail['symptom_id'],
                cf_user=symptom_detail['cf_user'],
                cf_combined=symptom_detail['cf_combined']
            )
            db.session.add(answer)
        
        db.session.commit()
        
        return jsonify({'resultId': result.id, 'message': 'Kuesioner berhasil disimpan'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in submit_questionnaire: {str(e)}")
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/result/<result_id>', methods=['GET'])
def get_result(result_id):
    result = Result.query.get(result_id)
    
    if not result:
        return jsonify({'error': 'Hasil tidak ditemukan'}), 404
    
    user = User.query.get(result.user_id)
    hypothesis = Hypothesis.query.get(result.hypothesis_id)
    answers = Answer.query.filter_by(result_id=result.id).all()
    
    # Format gejala yang teridentifikasi
    identified_symptoms = []
    for answer in answers:
        symptom = Symptom.query.get(answer.symptom_id)
        identified_symptoms.append({
            'symptomCode': symptom.code,
            'symptomText': symptom.description,
            'cfExpert': symptom.cf_expert,
            'cfUser': answer.cf_user,
            'cfCombined': answer.cf_combined
        })
    
    result_data = {
        'id': result.id,
        'userInfo': user.to_dict(),
        'hypothesis': hypothesis.to_dict(),
        'cfValue': result.cf_value,
        'cfPercentage': result.cf_percentage,
        'diagnosis': result.diagnosis,
        'recommendation': result.recommendation,
        'identifiedSymptoms': identified_symptoms,
        'createdAt': result.created_at.isoformat() if result.created_at else None
    }
    
    return jsonify(result_data)

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Dashboard statistics menggunakan query yang optimized"""
    try:
        # Total responden
        total_respondents = User.query.count()
        
        # Rata-rata tingkat kecanduan
        results = Result.query.all()
        avg_addiction_level = 0
        if results:
            avg_addiction_level = sum(r.cf_percentage for r in results) / len(results)
        
        # Kasus kecanduan tinggi
        high_addiction_cases = Result.query.filter(Result.cf_percentage >= 61).count()
        
        # Distribusi tingkat kecanduan
        addiction_levels = {
            'veryLow': Result.query.filter(Result.cf_percentage < 20).count(),
            'low': Result.query.filter(Result.cf_percentage >= 20, Result.cf_percentage < 40).count(),
            'medium': Result.query.filter(Result.cf_percentage >= 40, Result.cf_percentage < 61).count(),
            'high': Result.query.filter(Result.cf_percentage >= 61, Result.cf_percentage < 81).count(),
            'veryHigh': Result.query.filter(Result.cf_percentage >= 81).count()
        }
        
        # Data berdasarkan program studi
        program_studies = db.session.query(
            User.program_studi, 
            db.func.count(User.id).label('count')
        ).group_by(User.program_studi).all()
        
        by_program_studi = [
            {'programStudi': ps[0], 'count': ps[1]} 
            for ps in program_studies
        ]
        
        # Data berdasarkan gender
        by_gender = {
            'male': User.query.filter_by(jenis_kelamin='Laki-laki').count(),
            'female': User.query.filter_by(jenis_kelamin='Perempuan').count()
        }
        
        # Data responden untuk tabel
        respondents_data = []
        users = User.query.order_by(User.id.desc()).limit(10).all()
        
        for user in users:
            latest_result = Result.query.filter_by(user_id=user.id).order_by(Result.created_at.desc()).first()
            
            if latest_result:
                respondents_data.append({
                    'id': user.id,
                    'nama': user.nama,
                    'programStudi': user.program_studi,
                    'angkatan': user.angkatan,
                    'jenisKelamin': user.jenis_kelamin,
                    'cfValue': latest_result.cf_value,
                    'cfPercentage': latest_result.cf_percentage,
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
        
    except Exception as e:
        print(f"Error in get_statistics: {str(e)}")
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/result/<result_id>', methods=['DELETE'])
def delete_result(result_id):
    try:
        result = Result.query.get(result_id)
        
        if not result:
            return jsonify({'error': 'Hasil tidak ditemukan'}), 404
        
        # Hapus answers terkait
        Answer.query.filter_by(result_id=result.id).delete()
        
        user_id = result.user_id
        
        # Hapus result
        db.session.delete(result)
        db.session.commit()
        
        # Cek apakah user masih punya result lain
        remaining_results = Result.query.filter_by(user_id=user_id).count()
        
        if remaining_results == 0:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
        
        return jsonify({'message': 'Data berhasil dihapus'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/download-report/<result_id>', methods=['GET'])
def download_report(result_id):
    format_type = request.args.get('format', 'excel')
    
    if format_type == 'excel':
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
        output = generate_pdf_report(result_id)
        if not output:
            return jsonify({'error': 'Hasil tidak ditemukan'}), 404
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'hasil-analisis-{result_id}.pdf'
        )

@app.route('/api/download-all-reports', methods=['GET'])
def download_all_reports():
    format_type = request.args.get('format', 'excel')
    
    results = Result.query.all()
    
    if format_type == 'excel':
        output = generate_all_excel_reports(results)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='semua-hasil-analisis.xlsx'
        )
    
    return jsonify({'error': 'Format tidak didukung'}), 400

# Fungsi untuk menggenerate laporan Excel
def generate_excel_report(result_id):
    result = Result.query.get(result_id)
    if not result:
        return None
    
    user = User.query.get(result.user_id)
    hypothesis = Hypothesis.query.get(result.hypothesis_id)
    answers = Answer.query.filter_by(result_id=result_id).all()
    
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
    
    user_info = [
        ('Nama:', user.nama),
        ('Usia:', user.usia),
        ('Program Studi:', user.program_studi),
        ('Angkatan:', user.angkatan),
        ('Jenis Kelamin:', user.jenis_kelamin),
        ('Domisili:', user.domisili)
    ]
    
    for i, (label, value) in enumerate(user_info, 5):
        worksheet.write(f'A{i}', label, workbook.add_format({'bold': True}))
        worksheet.write(f'B{i}', value)
    
    # Hasil Analisis
    worksheet.merge_range('A12:H12', 'Hasil Analisis:', workbook.add_format({'bold': True}))
    
    analysis_info = [
        ('Hipotesis:', hypothesis.description),
        ('Nilai CF:', result.cf_value),
        ('Persentase CF:', f'{result.cf_percentage:.2f}%'),
        ('Diagnosis:', result.diagnosis),
        ('Rekomendasi:', result.recommendation)
    ]
    
    for i, (label, value) in enumerate(analysis_info, 13):
        worksheet.write(f'A{i}', label, workbook.add_format({'bold': True}))
        if i == 13:  # Hipotesis
            worksheet.merge_range(f'B{i}:H{i}', value)
        elif i in [16, 17]:  # Diagnosis dan Rekomendasi
            worksheet.merge_range(f'B{i}:H{i}', value)
        else:
            worksheet.write(f'B{i}', value)
    
    # Detail Gejala
    worksheet.merge_range('A19:H19', 'Detail Gejala yang Teridentifikasi:', workbook.add_format({'bold': True}))
    
    # Header tabel
    headers = ['No', 'Kode', 'Gejala', 'CF Expert', 'CF User', 'CF Kombinasi', 'Persentase']
    for col, header in enumerate(headers):
        worksheet.write(20, col, header, header_format)
    
    # Isi tabel gejala
    for i, answer in enumerate(answers):
        symptom = Symptom.query.get(answer.symptom_id)
        row = 21 + i
        
        worksheet.write(row, 0, i+1, cell_format)
        worksheet.write(row, 1, symptom.code, cell_format)
        worksheet.write(row, 2, symptom.description, cell_format)
        worksheet.write(row, 3, symptom.cf_expert, cell_format)
        worksheet.write(row, 4, answer.cf_user, cell_format)
        worksheet.write(row, 5, answer.cf_combined, cell_format)
        worksheet.write(row, 6, f'{answer.cf_combined * 100:.2f}%', cell_format)
    
    # Pengaturan lebar kolom
    column_widths = [5, 10, 50, 12, 12, 15, 12]
    for i, width in enumerate(column_widths):
        worksheet.set_column(i, i, width)
    
    workbook.close()
    output.seek(0)
    return output

# Fungsi untuk menggenerate laporan PDF
def generate_pdf_report(result_id):
    result = Result.query.get(result_id)
    if not result:
        return None
    
    user = User.query.get(result.user_id)
    hypothesis = Hypothesis.query.get(result.hypothesis_id)
    answers = Answer.query.filter_by(result_id=result_id).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Judul
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center
    elements.append(Paragraph("LAPORAN HASIL ANALISIS KECANDUAN GAME ONLINE", title_style))
    elements.append(Paragraph("Sistem Pakar HEROin", styles['Heading2']))
    elements.append(Paragraph(" ", styles['Normal']))
    
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
    elements.append(Paragraph(" ", styles['Normal']))
    
    # Hasil Analisis
    elements.append(Paragraph("Hasil Analisis:", styles['Heading3']))
    
    result_data = [
        ["Hipotesis", ": " + hypothesis.description],
        ["Nilai CF", ": " + str(result.cf_value)],
        ["Persentase CF", ": " + f'{result.cf_percentage:.2f}%'],
        ["Diagnosis", ": " + result.diagnosis],
        ["Rekomendasi", ": " + result.recommendation]
    ]
    
    result_table = Table(result_data, colWidths=[100, 400])
    result_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(result_table)
    elements.append(Paragraph(" ", styles['Normal']))
    
    # Detail Gejala
    elements.append(Paragraph("Detail Gejala yang Teridentifikasi:", styles['Heading3']))
    
    # Header tabel
    gejala_data = [["No", "Kode", "Gejala", "CF Expert", "CF User", "CF Kombinasi"]]
    
    # Isi tabel
    for i, answer in enumerate(answers):
        symptom = Symptom.query.get(answer.symptom_id)
        gejala_data.append([
            str(i+1),
            symptom.code,
            symptom.description,
            str(symptom.cf_expert),
            str(answer.cf_user),
            f'{answer.cf_combined:.3f}'
        ])
    
    gejala_table = Table(gejala_data, colWidths=[30, 40, 280, 60, 60, 80])
    gejala_table.setStyle(TableStyle([
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
    elements.append(gejala_table)
    
    # Tanggal dan waktu cetak
    elements.append(Paragraph(" ", styles['Normal']))
    elements.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Cek inisialisasi database
def initialize_database():
    """Initialize database dengan checking yang proper"""
    db.create_all()
    
    if Hypothesis.query.count() == 0:
        print("⚠️  Database kosong. Silakan jalankan migrations.sql")
    else:
        print("✅ Database sudah terinisialisasi")

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    
    app.run(debug=True)