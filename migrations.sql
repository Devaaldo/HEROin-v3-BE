-- migrations.sql
-- Script untuk membuat database dan tabel untuk sistem pakar HEROin (Updated)

-- Buat database
CREATE DATABASE IF NOT EXISTS heroin_db;
USE heroin_db;

-- Buat tabel users
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    usia INT NOT NULL,
    angkatan VARCHAR(10) NOT NULL,
    program_studi VARCHAR(100) NOT NULL,
    domisili VARCHAR(100) NOT NULL,
    jenis_kelamin VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Buat tabel hypothesis (Updated)
CREATE TABLE IF NOT EXISTS hypothesis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    cf_threshold_min FLOAT NOT NULL,
    cf_threshold_max FLOAT NOT NULL
);

-- Buat tabel gejala/symptoms (New)
CREATE TABLE IF NOT EXISTS symptom (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    cf_expert FLOAT NOT NULL -- Bobot dari pakar
);

-- Buat tabel rules (New)
CREATE TABLE IF NOT EXISTS rule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hypothesis_id INT NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (hypothesis_id) REFERENCES hypothesis(id) ON DELETE CASCADE
);

-- Buat tabel rule_symptoms (New) - Many to many relationship
CREATE TABLE IF NOT EXISTS rule_symptom (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    symptom_id INT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES rule(id) ON DELETE CASCADE,
    FOREIGN KEY (symptom_id) REFERENCES symptom(id) ON DELETE CASCADE
);

-- Buat tabel question (Updated to link with symptoms)
CREATE TABLE IF NOT EXISTS question (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symptom_id INT NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (symptom_id) REFERENCES symptom(id) ON DELETE CASCADE
);

-- Buat tabel result (Updated)
CREATE TABLE IF NOT EXISTS result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    hypothesis_id INT NOT NULL,
    cf_value FLOAT NOT NULL,
    cf_percentage FLOAT NOT NULL,
    diagnosis TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (hypothesis_id) REFERENCES hypothesis(id) ON DELETE CASCADE
);

-- Buat tabel answer (Updated to link with symptoms)
CREATE TABLE IF NOT EXISTS answer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT NOT NULL,
    symptom_id INT NOT NULL,
    cf_user FLOAT NOT NULL, -- Nilai dari user (0.0 - 1.0)
    cf_combined FLOAT NOT NULL, -- CF_expert * CF_user
    FOREIGN KEY (result_id) REFERENCES result(id) ON DELETE CASCADE,
    FOREIGN KEY (symptom_id) REFERENCES symptom(id) ON DELETE CASCADE
);

-- Insert data hypothesis
INSERT INTO hypothesis (code, name, description, cf_threshold_min, cf_threshold_max) VALUES
('P1', 'Kecanduan Ringan', 'Kecanduan game online tingkat ringan dengan durasi bermain 2-4 jam/hari', 0.40, 0.60),
('P2', 'Kecanduan Sedang', 'Kecanduan game online tingkat sedang dengan durasi bermain 4-8 jam/hari', 0.61, 0.80),
('P3', 'Kecanduan Berat', 'Kecanduan game online tingkat berat dengan durasi bermain >8 jam/hari', 0.81, 1.00);

-- Insert data symptoms
INSERT INTO symptom (code, description, cf_expert) VALUES
('G1', 'Keasyikan berlebihan dengan game (selalu memikirkan game bahkan saat tidak bermain)', 0.9),
('G2', 'Tanda-tanda withdrawal (gelisah, marah, cemas saat tidak bermain)', 0.8),
('G3', 'Toleransi (perlu waktu bermain semakin lama untuk puas)', 0.7),
('G4', 'Gagal mengontrol durasi bermain meski sudah berusaha', 0.8),
('G5', 'Kehilangan minat pada hobi/aktivitas sebelumnya', 0.6),
('G6', 'Terus bermain meski tahu konsekuensi negatif (akademik, kesehatan, hubungan)', 0.9),
('G7', 'Berbohong tentang durasi bermain ke keluarga/teman', 0.7),
('G8', 'Menggunakan game untuk melarikan diri dari mood negatif (stres, depresi)', 0.8),
('G9', 'Mengorbankan hubungan/pekerjaan/studi demi game', 0.9),
('G10', 'Preferensi interaksi sosial di game daripada dunia nyata', 0.6),
('G11', 'Masalah fisik (kelelahan, sakit mata, kurang tidur, lupa makan)', 0.5),
('G12', 'Prestasi akademik/kinerja menurun', 0.7);

-- Insert rules untuk kecanduan ringan (P1)
INSERT INTO rule (hypothesis_id, rule_name, description) VALUES
(1, 'Rule P1-1', 'IF P1 THEN G1 AND G5'),
(1, 'Rule P1-2', 'IF P1 THEN G1 AND G5 AND G10'),
(1, 'Rule P1-3', 'IF P1 THEN G1 AND G5 AND G10 AND G3');

-- Insert rules untuk kecanduan sedang (P2)
INSERT INTO rule (hypothesis_id, rule_name, description) VALUES
(2, 'Rule P2-1', 'IF P2 THEN G2 AND G3 AND G4'),
(2, 'Rule P2-2', 'IF P2 THEN G2 AND G3 AND G4 AND G7'),
(2, 'Rule P2-3', 'IF P2 THEN G2 AND G3 AND G4 AND G7 AND G8');

-- Insert rules untuk kecanduan berat (P3)
INSERT INTO rule (hypothesis_id, rule_name, description) VALUES
(3, 'Rule P3-1', 'IF P3 THEN G6 AND G9'),
(3, 'Rule P3-2', 'IF P3 THEN G6 AND G9 AND G11'),
(3, 'Rule P3-3', 'IF P3 THEN G6 AND G9 AND G11 AND G12'),
(3, 'Rule P3-4', 'IF P3 THEN G6 AND G9 AND G11 AND G12 AND G2');

-- Insert rule_symptom relationships untuk kecanduan ringan
INSERT INTO rule_symptom (rule_id, symptom_id) VALUES
-- Rule P1-1: G1 AND G5
(1, 1), (1, 5),
-- Rule P1-2: G1 AND G5 AND G10
(2, 1), (2, 5), (2, 10),
-- Rule P1-3: G1 AND G5 AND G10 AND G3
(3, 1), (3, 5), (3, 10), (3, 3);

-- Insert rule_symptom relationships untuk kecanduan sedang
INSERT INTO rule_symptom (rule_id, symptom_id) VALUES
-- Rule P2-1: G2 AND G3 AND G4
(4, 2), (4, 3), (4, 4),
-- Rule P2-2: G2 AND G3 AND G4 AND G7
(5, 2), (5, 3), (5, 4), (5, 7),
-- Rule P2-3: G2 AND G3 AND G4 AND G7 AND G8
(6, 2), (6, 3), (6, 4), (6, 7), (6, 8);

-- Insert rule_symptom relationships untuk kecanduan berat
INSERT INTO rule_symptom (rule_id, symptom_id) VALUES
-- Rule P3-1: G6 AND G9
(7, 6), (7, 9),  
-- Rule P3-2: G6 AND G9 AND G11
(8, 6), (8, 9), (8, 11),
-- Rule P3-3: G6 AND G9 AND G11 AND G12
(9, 6), (9, 9), (9, 11), (9, 12),
-- Rule P3-4: G6 AND G9 AND G11 AND G12 AND G2
(10, 6), (10, 9), (10, 11), (10, 12), (10, 2);

-- Insert questions berdasarkan symptoms
INSERT INTO question (symptom_id, text) VALUES
(1, 'Apakah Anda selalu memikirkan game bahkan saat tidak sedang bermain?'),
(2, 'Apakah Anda merasa gelisah, marah, atau cemas ketika tidak bisa bermain game?'),
(3, 'Apakah Anda memerlukan waktu bermain yang semakin lama untuk merasa puas?'),
(4, 'Apakah Anda gagal mengontrol durasi bermain meskipun sudah berusaha?'),
(5, 'Apakah Anda kehilangan minat pada hobi atau aktivitas yang sebelumnya disukai?'),
(6, 'Apakah Anda terus bermain game meskipun tahu konsekuensi negatifnya terhadap akademik, kesehatan, atau hubungan?'),
(7, 'Apakah Anda berbohong tentang durasi bermain kepada keluarga atau teman?'),
(8, 'Apakah Anda menggunakan game untuk melarikan diri dari mood negatif seperti stres atau depresi?'),
(9, 'Apakah Anda mengorbankan hubungan, pekerjaan, atau studi demi bermain game?'),
(10, 'Apakah Anda lebih memilih berinteraksi sosial di dalam game daripada di dunia nyata?'),
(11, 'Apakah Anda mengalami masalah fisik seperti kelelahan, sakit mata, kurang tidur, atau lupa makan karena bermain game?'),
(12, 'Apakah prestasi akademik atau kinerja Anda menurun karena bermain game?');