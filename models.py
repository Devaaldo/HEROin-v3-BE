from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    angkatan = db.Column(db.Integer, nullable=False)
    program_studi = db.Column(db.String(100), nullable=False)
    domisili = db.Column(db.String(100), nullable=False)
    jenis_kelamin = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    answers = db.relationship('Answer', backref='user', lazy=True)
    results = db.relationship('Result', backref='user', lazy=True)
    user_hypotheses = db.relationship('UserHypothesis', backref='user', lazy=True)

class ProgramStudi(db.Model):
    __tablename__ = 'program_studi'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

class Impact(db.Model):
    __tablename__ = 'impacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Relationships
    questions = db.relationship('Question', backref='impact', lazy=True)

class Hypothesis(db.Model):
    __tablename__ = 'hypotheses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Relationships
    user_hypotheses = db.relationship('UserHypothesis', backref='hypothesis', lazy=True)
    hypothesis_questions = db.relationship('HypothesisQuestion', backref='hypothesis', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    impact_id = db.Column(db.Integer, db.ForeignKey('impacts.id'), nullable=False)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True)
    hypothesis_questions = db.relationship('HypothesisQuestion', backref='question', lazy=True)

class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    certainty_value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Result(db.Model):
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    overall_certainty = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class UserHypothesis(db.Model):
    __tablename__ = 'user_hypotheses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey('hypotheses.id'), nullable=False)

class HypothesisQuestion(db.Model):
    __tablename__ = 'hypothesis_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey('hypotheses.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)