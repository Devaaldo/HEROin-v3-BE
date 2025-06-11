from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================================================
# MODELS YANG SESUAI DENGAN MIGRATION SQL
# ============================================================================

class User(db.Model):
    """Model User sesuai dengan tabel 'user' di migrations.sql"""
    __tablename__ = 'user'  # Sesuai dengan migrations.sql
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    angkatan = db.Column(db.String(10), nullable=False)  # String sesuai SQL
    program_studi = db.Column(db.String(100), nullable=False)
    domisili = db.Column(db.String(100), nullable=False)
    jenis_kelamin = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    results = db.relationship('Result', backref='user', lazy=True, cascade='all, delete-orphan')
    
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
    """Model Hypothesis sesuai dengan tabel 'hypothesis' di migrations.sql"""
    __tablename__ = 'hypothesis'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)  # P1, P2, P3
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cf_threshold_min = db.Column(db.Float, nullable=False)
    cf_threshold_max = db.Column(db.Float, nullable=False)
    
    # Relationships
    rules = db.relationship('Rule', backref='hypothesis', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='hypothesis', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'cfThresholdMin': self.cf_threshold_min,
            'cfThresholdMax': self.cf_threshold_max
        }

class Symptom(db.Model):
    """Model Symptom sesuai dengan tabel 'symptom' di migrations.sql"""
    __tablename__ = 'symptom'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)  # G1-G12
    description = db.Column(db.Text, nullable=False)
    cf_expert = db.Column(db.Float, nullable=False)  # Bobot dari pakar (0.0-1.0)
    
    # Relationships
    questions = db.relationship('Question', backref='symptom', lazy=True, cascade='all, delete-orphan')
    rule_symptoms = db.relationship('RuleSymptom', backref='symptom', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='symptom', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'cfExpert': self.cf_expert
        }

class Rule(db.Model):
    """Model Rule sesuai dengan tabel 'rule' di migrations.sql"""
    __tablename__ = 'rule'
    
    id = db.Column(db.Integer, primary_key=True)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey('hypothesis.id'), nullable=False)
    rule_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    rule_symptoms = db.relationship('RuleSymptom', backref='rule', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'hypothesisId': self.hypothesis_id,
            'ruleName': self.rule_name,
            'description': self.description
        }

class RuleSymptom(db.Model):
    """Model RuleSymptom sesuai dengan tabel 'rule_symptom' di migrations.sql"""
    __tablename__ = 'rule_symptom'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('rule.id'), nullable=False)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptom.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ruleId': self.rule_id,
            'symptomId': self.symptom_id
        }

class Question(db.Model):
    """Model Question sesuai dengan tabel 'question' di migrations.sql"""
    __tablename__ = 'question'
    
    id = db.Column(db.Integer, primary_key=True)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptom.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symptomId': self.symptom_id,
            'text': self.text,
            'symptomCode': self.symptom.code if self.symptom else None
        }

class Result(db.Model):
    """Model Result sesuai dengan tabel 'result' di migrations.sql"""
    __tablename__ = 'result'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey('hypothesis.id'), nullable=False)
    cf_value = db.Column(db.Float, nullable=False)  # CF value (0.0-1.0)
    cf_percentage = db.Column(db.Float, nullable=False)  # CF percentage (0-100)
    diagnosis = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='result', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'hypothesisId': self.hypothesis_id,
            'cfValue': self.cf_value,
            'cfPercentage': self.cf_percentage,
            'diagnosis': self.diagnosis,
            'recommendation': self.recommendation,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Answer(db.Model):
    """Model Answer sesuai dengan tabel 'answer' di migrations.sql"""
    __tablename__ = 'answer'
    
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptom.id'), nullable=False)
    cf_user = db.Column(db.Float, nullable=False)  # Nilai dari user (0.0-1.0)
    cf_combined = db.Column(db.Float, nullable=False)  # CF_expert * CF_user
    
    def to_dict(self):
        return {
            'id': self.id,
            'resultId': self.result_id,
            'symptomId': self.symptom_id,
            'cfUser': self.cf_user,
            'cfCombined': self.cf_combined
        }