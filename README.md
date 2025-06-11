# HEROin Backend - Flask API Server

![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-red?style=for-the-badge&logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?style=for-the-badge&logo=mysql)

Backend API untuk sistem pakar **HEROin** yang mengimplementasikan algoritma **Backward Chaining** dan **Certainty Factor** untuk diagnosa kecanduan game online.

## 🧠 Core Algorithm

### 1. Backward Chaining Engine

```python
class BackwardChaining:
    """
    Implementasi Backward Chaining sesuai metodologi penelitian.
    Penalaran dimulai dari hipotesis tingkat tertinggi,
    turun ke fakta level bawah untuk mendukung hipotesis.
    """
```

### 2. Certainty Factor Calculator

```python
def calculate_certainty_factor(cf_values):
    """
    Formula: CF_gabungan = CF1 + CF2 × (1 - CF1)
    Untuk multiple CF: diterapkan secara berurutan
    """
    combined_cf = cf_values[0]
    for cf in cf_values[1:]:
        combined_cf = combined_cf + (cf * (1 - combined_cf))
    return max(0.0, min(1.0, combined_cf))
```

## 🏗️ Architecture

### Tech Stack

- **Flask 2.x** - Lightweight web framework
- **SQLAlchemy** - ORM untuk database operations
- **MySQL 8.0+** - Relational database management
- **Flask-CORS** - Cross-origin resource sharing
- **XlsxWriter** - Excel report generation
- **ReportLab** - PDF report generation

### Database Schema

```sql
-- 8 tabel utama dengan relasi yang optimal
user            # Data identitas pengguna
hypothesis      # Hipotesis kecanduan (P1, P2, P3)
symptom         # 12 gejala kecanduan (G1-G12)
rule            # Aturan knowledge base
rule_symptom    # Relasi many-to-many rules & symptoms
question        # Pertanyaan diagnostik
result          # Hasil analisis CF
answer          # Jawaban detail per gejala
```

## 🚀 Installation & Setup

### Prerequisites

```bash
Python 3.8+
MySQL 8.0+
pip (Python package manager)
```

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd heroin-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

```bash
# Login ke MySQL
mysql -u root -p

# Create database
CREATE DATABASE heroin_db;
USE heroin_db;

# Run migrations
source migrations.sql
```

### 3. Application Configuration

```python
# app.py - Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/heroin_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

### 4. Start Development Server

```bash
python app.py
# Server running on http://localhost:5000
```

## 📂 Project Structure

```
backend/
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy database models
├── backward_chaining.py      # Backward chaining algorithm
├── certainty_factor.py       # CF calculation utilities
├── migrations.sql            # Database schema & seed data
├── check_database.py         # Database validation script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🗃️ Database Models

### Core Models

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    program_studi = db.Column(db.String(100), nullable=False)
    # ... other fields

class Hypothesis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)  # P1, P2, P3
    name = db.Column(db.String(100), nullable=False)
    cf_threshold_min = db.Column(db.Float, nullable=False)
    cf_threshold_max = db.Column(db.Float, nullable=False)

class Symptom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)  # G1-G12
    description = db.Column(db.Text, nullable=False)
    cf_expert = db.Column(db.Float, nullable=False)  # Bobot pakar
```

### Knowledge Base

```python
# Rules mapping sesuai penelitian
rules_mapping = {
    1: {  # P1 - Kecanduan Ringan
        'rules': [
            ['G1', 'G5'],                    # Rule 1
            ['G1', 'G5', 'G10'],           # Rule 2
            ['G1', 'G5', 'G10', 'G3']      # Rule 3
        ]
    },
    2: {  # P2 - Kecanduan Sedang
        'rules': [
            ['G2', 'G3', 'G4'],            # Rule 1
            ['G2', 'G3', 'G4', 'G7'],      # Rule 2
            ['G2', 'G3', 'G4', 'G7', 'G8'] # Rule 3
        ]
    },
    3: {  # P3 - Kecanduan Berat
        'rules': [
            ['G6', 'G9'],                           # Rule 1
            ['G6', 'G9', 'G11'],                   # Rule 2
            ['G6', 'G9', 'G11', 'G12'],           # Rule 3
            ['G6', 'G9', 'G11', 'G12', 'G2']      # Rule 4
        ]
    }
}
```

## 🔌 API Endpoints

### User Management

```python
POST   /api/user-info              # Save user information
GET    /api/hypotheses             # Get available hypotheses
POST   /api/selected-hypothesis    # Save selected hypothesis
```

### Questionnaire System

```python
GET    /api/questions/<hypothesis_id>  # Get adaptive questions (Backward Chaining)
POST   /api/submit-questionnaire       # Submit answers & calculate CF
```

### Results & Analytics

```python
GET    /api/result/<result_id>         # Get detailed analysis result
GET    /api/statistics                 # Dashboard statistics
DELETE /api/result/<result_id>         # Delete result & related data
```

### Report Generation

```python
GET    /api/download-report/<result_id>?format=excel  # Individual Excel report
GET    /api/download-report/<result_id>?format=pdf    # Individual PDF report
GET    /api/download-all-reports?format=excel         # Bulk Excel export
```

## 🧮 Algorithm Implementation

### 1. Backward Chaining Process

```python
def get_questions_for_hypothesis(self):
    """
    Mendapatkan pertanyaan berdasarkan gejala yang diperlukan
    untuk memvalidasi hipotesis (backward chaining).
    """
    required_symptom_codes = self.get_required_symptoms()
    questions = []

    for symptom_code in required_symptom_codes:
        symptom = Symptom.query.filter_by(code=symptom_code).first()
        if symptom:
            question = Question.query.filter_by(symptom_id=symptom.id).first()
            if question:
                questions.append({
                    'id': question.id,
                    'text': question.text,
                    'symptom_code': symptom.code,
                    'cf_expert': symptom.cf_expert
                })

    return questions
```

### 2. Certainty Factor Calculation

```python
def process_answers(self, symptom_answers):
    """
    Memproses jawaban berdasarkan backward chaining dan certainty factor
    """
    cf_values = []

    for answer in symptom_answers:
        symptom = Symptom.query.get(answer['symptomId'])
        if symptom:
            # CF_kombinasi = CF_expert × CF_user
            cf_combined = symptom.cf_expert * answer['cfUser']
            cf_values.append(cf_combined)

    # Gabungkan semua CF menggunakan formula
    final_cf = self.combine_certainty_factors(cf_values)

    return {
        'cfValue': final_cf,
        'cfPercentage': final_cf * 100,
        'diagnosis': self.get_diagnosis(final_cf)
    }
```

### 3. CF Combination Formula

```python
def combine_certainty_factors(self, cf_values):
    """
    Menggabungkan nilai CF menggunakan formula kombinasi:
    CF_gabungan = CF1 + CF2 × (1 - CF1)
    """
    if not cf_values:
        return 0.0

    combined_cf = cf_values[0]

    for cf in cf_values[1:]:
        if combined_cf >= 0 and cf >= 0:
            # Kedua positif: CF1 + CF2 * (1 - CF1)
            combined_cf = combined_cf + cf * (1 - combined_cf)
        elif combined_cf < 0 and cf < 0:
            # Kedua negatif: CF1 + CF2 * (1 + CF1)
            combined_cf = combined_cf + cf * (1 + combined_cf)
        else:
            # Berbeda tanda: (CF1 + CF2) / (1 - min(|CF1|, |CF2|))
            denominator = 1 - min(abs(combined_cf), abs(cf))
            combined_cf = (combined_cf + cf) / denominator

    return max(0, min(1, combined_cf))
```

## 📊 Report Generation

### Excel Reports

```python
def generate_excel_report(result_id):
    """Generate comprehensive Excel report with formatting"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # Format styles
    title_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'align': 'center'
    })
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#9630FB', 'color': 'white'
    })

    # Create worksheets with user info, analysis results, and symptom details
    # ... implementation details
```

### PDF Reports

```python
def generate_pdf_report(result_id):
    """Generate professional PDF report using ReportLab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Create styled elements
    elements = []
    elements.append(Paragraph("LAPORAN HASIL ANALISIS", title_style))

    # Add user information table
    # Add analysis results with CF visualization
    # Add symptom details table
    # ... implementation details
```

## 📈 Statistics & Analytics

### Dashboard Statistics

```python
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    # Total responden
    total_respondents = User.query.count()

    # Rata-rata tingkat kecanduan
    results = Result.query.all()
    avg_addiction_level = sum(r.cf_percentage for r in results) / len(results)

    # Distribusi tingkat kecanduan berdasarkan CF
    addiction_levels = {
        'veryLow': Result.query.filter(Result.cf_percentage < 20).count(),
        'low': Result.query.filter(Result.cf_percentage >= 20, Result.cf_percentage < 40).count(),
        'medium': Result.query.filter(Result.cf_percentage >= 40, Result.cf_percentage < 61).count(),
        'high': Result.query.filter(Result.cf_percentage >= 61, Result.cf_percentage < 81).count(),
        'veryHigh': Result.query.filter(Result.cf_percentage >= 81).count()
    }

    # Data berdasarkan program studi dan gender
    # ... implementation details
```

## 🔧 Database Utilities

### Database Validation

```python
# check_database.py
def check_database():
    """Validate database connection and data integrity"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='heroin_db',
            user='root',
            password='sql123'
        )

        # Check hypothesis data
        cursor.execute("SELECT COUNT(*) FROM hypothesis")
        hypothesis_count = cursor.fetchone()[0]

        if hypothesis_count > 0:
            print("✅ Database setup is OK!")
        else:
            print("⚠️ Run migrations.sql first")

    except Error as e:
        print(f"❌ Database error: {e}")
```

### Migration Script

```sql
-- migrations.sql contains:
-- 1. Database and table creation
-- 2. Seed data for hypotheses (P1, P2, P3)
-- 3. 12 symptoms (G1-G12) with CF expert values
-- 4. Knowledge base rules implementation
-- 5. Questions mapped to symptoms
```

## 🛡️ Error Handling

### API Error Responses

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
```

### Data Validation

```python
def validate_cf_input(cf_value):
    """Validate certainty factor input range"""
    try:
        cf = float(cf_value)
        if 0.0 <= cf <= 1.0:
            return cf
        else:
            raise ValueError("CF must be between 0.0 and 1.0")
    except (ValueError, TypeError):
        raise ValueError("Invalid CF value format")
```

## 🚀 Deployment

### Production Configuration

```python
# config.py
class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    TESTING = False
```

### Environment Variables

```bash
# .env
DATABASE_URL=mysql://user:password@host:port/heroin_db
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🧪 Testing

### Database Testing

```bash
# Validate database setup
python check_database.py

# Expected output:
✅ Koneksi database berhasil!
📊 Jumlah data hypothesis: 3
📊 Jumlah data symptom: 12
📊 Jumlah data question: 12
✅ Database setup is OK!
```

### API Testing

```bash
# Test endpoints with curl
curl -X GET http://localhost:5000/api/hypotheses
curl -X POST http://localhost:5000/api/user-info -H "Content-Type: application/json" -d '{"nama":"Test User",...}'
```

## 📋 Development Guidelines

### Code Style

- **PEP 8** compliance untuk Python code
- **Docstrings** untuk semua functions dan classes
- **Type hints** untuk better code documentation
- **Error handling** yang comprehensive

### Database Best Practices

- **Foreign key constraints** untuk data integrity
- **Indexes** pada kolom yang sering di-query
- **Transaction management** untuk operasi complex
- **Connection pooling** untuk performance

## 🐛 Troubleshooting

### Common Issues

```bash
# Database connection error
Error: Access denied for user 'root'@'localhost'
Solution: Check MySQL credentials and user permissions

# Missing modules
ModuleNotFoundError: No module named 'flask'
Solution: pip install -r requirements.txt

# Port already in use
OSError: [Errno 48] Address already in use
Solution: Change port in app.py or kill existing process
```

### Performance Optimization

- **Query optimization** dengan SQLAlchemy
- **Caching** untuk data yang jarang berubah
- **Pagination** untuk large datasets
- **Connection pooling** untuk database

## 📝 Future Enhancements

- [ ] **JWT Authentication** - Secure API access
- [ ] **Rate Limiting** - API abuse prevention
- [ ] **Caching Layer** - Redis integration
- [ ] **API Documentation** - Swagger/OpenAPI
- [ ] **Unit Testing** - Comprehensive test suite
- [ ] **Logging** - Structured logging dengan ELK stack

---

**Backend developed with 🐍 Python Flask for robust expert system implementation**# HEROin Backend - Flask API Server

![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-red?style=for-the-badge&logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?style=for-the-badge&logo=mysql)

Backend API untuk sistem pakar **HEROin** yang mengimplementasikan algoritma **Backward Chaining** dan **Certainty Factor** untuk diagnosa kecanduan game online.

## 🧠 Core Algorithm

### 1. Backward Chaining Engine

```python
class BackwardChaining:
    """
    Implementasi Backward Chaining sesuai metodologi penelitian.
    Penalaran dimulai dari hipotesis tingkat tertinggi,
    turun ke fakta level bawah untuk mendukung hipotesis.
    """
```

### 2. Certainty Factor Calculator

```python
def calculate_certainty_factor(cf_values):
    """
    Formula: CF_gabungan = CF1 + CF2 × (1 - CF1)
    Untuk multiple CF: diterapkan secara berurutan
    """
    combined_cf = cf_values[0]
    for cf in cf_values[1:]:
        combined_cf = combined_cf + (cf * (1 - combined_cf))
    return max(0.0, min(1.0, combined_cf))
```

## 🏗️ Architecture

### Tech Stack

- **Flask 2.x** - Lightweight web framework
- **SQLAlchemy** - ORM untuk database operations
- **MySQL 8.0+** - Relational database management
- **Flask-CORS** - Cross-origin resource sharing
- **XlsxWriter** - Excel report generation
- **ReportLab** - PDF report generation

### Database Schema

```sql
-- 8 tabel utama dengan relasi yang optimal
user            # Data identitas pengguna
hypothesis      # Hipotesis kecanduan (P1, P2, P3)
symptom         # 12 gejala kecanduan (G1-G12)
rule            # Aturan knowledge base
rule_symptom    # Relasi many-to-many rules & symptoms
question        # Pertanyaan diagnostik
result          # Hasil analisis CF
answer          # Jawaban detail per gejala
```

## 🚀 Installation & Setup

### Prerequisites

```bash
Python 3.8+
MySQL 8.0+
pip (Python package manager)
```

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd heroin-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

```bash
# Login ke MySQL
mysql -u root -p

# Create database
CREATE DATABASE heroin_db;
USE heroin_db;

# Run migrations
source migrations.sql
```

### 3. Application Configuration

```python
# app.py - Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/heroin_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

### 4. Start Development Server

```bash
python app.py
# Server running on http://localhost:5000
```

## 📂 Project Structure

```
backend/
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy database models
├── backward_chaining.py      # Backward chaining algorithm
├── certainty_factor.py       # CF calculation utilities
├── migrations.sql            # Database schema & seed data
├── check_database.py         # Database validation script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🗃️ Database Models

### Core Models

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    program_studi = db.Column(db.String(100), nullable=False)
    # ... other fields

class Hypothesis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)  # P1, P2, P3
    name = db.Column(db.String(100), nullable=False)
    cf_threshold_min = db.Column(db.Float, nullable=False)
    cf_threshold_max = db.Column(db.Float, nullable=False)

class Symptom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)  # G1-G12
    description = db.Column(db.Text, nullable=False)
    cf_expert = db.Column(db.Float, nullable=False)  # Bobot pakar
```

### Knowledge Base

```python
# Rules mapping sesuai penelitian
rules_mapping = {
    1: {  # P1 - Kecanduan Ringan
        'rules': [
            ['G1', 'G5'],                    # Rule 1
            ['G1', 'G5', 'G10'],           # Rule 2
            ['G1', 'G5', 'G10', 'G3']      # Rule 3
        ]
    },
    2: {  # P2 - Kecanduan Sedang
        'rules': [
            ['G2', 'G3', 'G4'],            # Rule 1
            ['G2', 'G3', 'G4', 'G7'],      # Rule 2
            ['G2', 'G3', 'G4', 'G7', 'G8'] # Rule 3
        ]
    },
    3: {  # P3 - Kecanduan Berat
        'rules': [
            ['G6', 'G9'],                           # Rule 1
            ['G6', 'G9', 'G11'],                   # Rule 2
            ['G6', 'G9', 'G11', 'G12'],           # Rule 3
            ['G6', 'G9', 'G11', 'G12', 'G2']      # Rule 4
        ]
    }
}
```

## 🔌 API Endpoints

### User Management

```python
POST   /api/user-info              # Save user information
GET    /api/hypotheses             # Get available hypotheses
POST   /api/selected-hypothesis    # Save selected hypothesis
```

### Questionnaire System

```python
GET    /api/questions/<hypothesis_id>  # Get adaptive questions (Backward Chaining)
POST   /api/submit-questionnaire       # Submit answers & calculate CF
```

### Results & Analytics

```python
GET    /api/result/<result_id>         # Get detailed analysis result
GET    /api/statistics                 # Dashboard statistics
DELETE /api/result/<result_id>         # Delete result & related data
```

### Report Generation

```python
GET    /api/download-report/<result_id>?format=excel  # Individual Excel report
GET    /api/download-report/<result_id>?format=pdf    # Individual PDF report
GET    /api/download-all-reports?format=excel         # Bulk Excel export
```

## 🧮 Algorithm Implementation

### 1. Backward Chaining Process

```python
def get_questions_for_hypothesis(self):
    """
    Mendapatkan pertanyaan berdasarkan gejala yang diperlukan
    untuk memvalidasi hipotesis (backward chaining).
    """
    required_symptom_codes = self.get_required_symptoms()
    questions = []

    for symptom_code in required_symptom_codes:
        symptom = Symptom.query.filter_by(code=symptom_code).first()
        if symptom:
            question = Question.query.filter_by(symptom_id=symptom.id).first()
            if question:
                questions.append({
                    'id': question.id,
                    'text': question.text,
                    'symptom_code': symptom.code,
                    'cf_expert': symptom.cf_expert
                })

    return questions
```

### 2. Certainty Factor Calculation

```python
def process_answers(self, symptom_answers):
    """
    Memproses jawaban berdasarkan backward chaining dan certainty factor
    """
    cf_values = []

    for answer in symptom_answers:
        symptom = Symptom.query.get(answer['symptomId'])
        if symptom:
            # CF_kombinasi = CF_expert × CF_user
            cf_combined = symptom.cf_expert * answer['cfUser']
            cf_values.append(cf_combined)

    # Gabungkan semua CF menggunakan formula
    final_cf = self.combine_certainty_factors(cf_values)

    return {
        'cfValue': final_cf,
        'cfPercentage': final_cf * 100,
        'diagnosis': self.get_diagnosis(final_cf)
    }
```

### 3. CF Combination Formula

```python
def combine_certainty_factors(self, cf_values):
    """
    Menggabungkan nilai CF menggunakan formula kombinasi:
    CF_gabungan = CF1 + CF2 × (1 - CF1)
    """
    if not cf_values:
        return 0.0

    combined_cf = cf_values[0]

    for cf in cf_values[1:]:
        if combined_cf >= 0 and cf >= 0:
            # Kedua positif: CF1 + CF2 * (1 - CF1)
            combined_cf = combined_cf + cf * (1 - combined_cf)
        elif combined_cf < 0 and cf < 0:
            # Kedua negatif: CF1 + CF2 * (1 + CF1)
            combined_cf = combined_cf + cf * (1 + combined_cf)
        else:
            # Berbeda tanda: (CF1 + CF2) / (1 - min(|CF1|, |CF2|))
            denominator = 1 - min(abs(combined_cf), abs(cf))
            combined_cf = (combined_cf + cf) / denominator

    return max(0, min(1, combined_cf))
```

## 📊 Report Generation

### Excel Reports

```python
def generate_excel_report(result_id):
    """Generate comprehensive Excel report with formatting"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # Format styles
    title_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'align': 'center'
    })
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#9630FB', 'color': 'white'
    })

    # Create worksheets with user info, analysis results, and symptom details
    # ... implementation details
```

### PDF Reports

```python
def generate_pdf_report(result_id):
    """Generate professional PDF report using ReportLab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Create styled elements
    elements = []
    elements.append(Paragraph("LAPORAN HASIL ANALISIS", title_style))

    # Add user information table
    # Add analysis results with CF visualization
    # Add symptom details table
    # ... implementation details
```

## 📈 Statistics & Analytics

### Dashboard Statistics

```python
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    # Total responden
    total_respondents = User.query.count()

    # Rata-rata tingkat kecanduan
    results = Result.query.all()
    avg_addiction_level = sum(r.cf_percentage for r in results) / len(results)

    # Distribusi tingkat kecanduan berdasarkan CF
    addiction_levels = {
        'veryLow': Result.query.filter(Result.cf_percentage < 20).count(),
        'low': Result.query.filter(Result.cf_percentage >= 20, Result.cf_percentage < 40).count(),
        'medium': Result.query.filter(Result.cf_percentage >= 40, Result.cf_percentage < 61).count(),
        'high': Result.query.filter(Result.cf_percentage >= 61, Result.cf_percentage < 81).count(),
        'veryHigh': Result.query.filter(Result.cf_percentage >= 81).count()
    }

    # Data berdasarkan program studi dan gender
    # ... implementation details
```

## 🔧 Database Utilities

### Database Validation

```python
# check_database.py
def check_database():
    """Validate database connection and data integrity"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='heroin_db',
            user='root',
            password='sql123'
        )

        # Check hypothesis data
        cursor.execute("SELECT COUNT(*) FROM hypothesis")
        hypothesis_count = cursor.fetchone()[0]

        if hypothesis_count > 0:
            print("✅ Database setup is OK!")
        else:
            print("⚠️ Run migrations.sql first")

    except Error as e:
        print(f"❌ Database error: {e}")
```

### Migration Script

```sql
-- migrations.sql contains:
-- 1. Database and table creation
-- 2. Seed data for hypotheses (P1, P2, P3)
-- 3. 12 symptoms (G1-G12) with CF expert values
-- 4. Knowledge base rules implementation
-- 5. Questions mapped to symptoms
```

## 🛡️ Error Handling

### API Error Responses

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
```

### Data Validation

```python
def validate_cf_input(cf_value):
    """Validate certainty factor input range"""
    try:
        cf = float(cf_value)
        if 0.0 <= cf <= 1.0:
            return cf
        else:
            raise ValueError("CF must be between 0.0 and 1.0")
    except (ValueError, TypeError):
        raise ValueError("Invalid CF value format")
```

## 🚀 Deployment

### Production Configuration

```python
# config.py
class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    TESTING = False
```

### Environment Variables

```bash
# .env
DATABASE_URL=mysql://user:password@host:port/heroin_db
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🧪 Testing

### Database Testing

```bash
# Validate database setup
python check_database.py

# Expected output:
✅ Koneksi database berhasil!
📊 Jumlah data hypothesis: 3
📊 Jumlah data symptom: 12
📊 Jumlah data question: 12
✅ Database setup is OK!
```

### API Testing

```bash
# Test endpoints with curl
curl -X GET http://localhost:5000/api/hypotheses
curl -X POST http://localhost:5000/api/user-info -H "Content-Type: application/json" -d '{"nama":"Test User",...}'
```

## 📋 Development Guidelines

### Code Style

- **PEP 8** compliance untuk Python code
- **Docstrings** untuk semua functions dan classes
- **Type hints** untuk better code documentation
- **Error handling** yang comprehensive

### Database Best Practices

- **Foreign key constraints** untuk data integrity
- **Indexes** pada kolom yang sering di-query
- **Transaction management** untuk operasi complex
- **Connection pooling** untuk performance

## 🐛 Troubleshooting

### Common Issues

```bash
# Database connection error
Error: Access denied for user 'root'@'localhost'
Solution: Check MySQL credentials and user permissions

# Missing modules
ModuleNotFoundError: No module named 'flask'
Solution: pip install -r requirements.txt

# Port already in use
OSError: [Errno 48] Address already in use
Solution: Change port in app.py or kill existing process
```

### Performance Optimization

- **Query optimization** dengan SQLAlchemy
- **Caching** untuk data yang jarang berubah
- **Pagination** untuk large datasets
- **Connection pooling** untuk database

## 📝 Future Enhancements

- [ ] **JWT Authentication** - Secure API access
- [ ] **Rate Limiting** - API abuse prevention
- [ ] **Caching Layer** - Redis integration
- [ ] **API Documentation** - Swagger/OpenAPI
- [ ] **Unit Testing** - Comprehensive test suite
- [ ] **Logging** - Structured logging dengan ELK stack

---

**Backend developed with 🐍 Python Flask for robust expert system implementation**
