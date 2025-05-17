-- migrations.sql
-- Script untuk membuat database dan tabel untuk sistem pakar HEROin

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

-- Buat tabel hypothesis
CREATE TABLE IF NOT EXISTS hypothesis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL
);

-- Buat tabel question
CREATE TABLE IF NOT EXISTS question (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hypothesis_id INT NOT NULL,
    code VARCHAR(10) NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (hypothesis_id) REFERENCES hypothesis(id) ON DELETE CASCADE
);

-- Buat tabel result
CREATE TABLE IF NOT EXISTS result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    hypothesis_id INT NOT NULL,
    cf_value FLOAT NOT NULL,
    diagnosis TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (hypothesis_id) REFERENCES hypothesis(id) ON DELETE CASCADE
);

-- Buat tabel answer
CREATE TABLE IF NOT EXISTS answer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT NOT NULL,
    question_id INT NOT NULL,
    cf_value FLOAT NOT NULL,
    FOREIGN KEY (result_id) REFERENCES result(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES question(id) ON DELETE CASCADE
);

-- Insert data awal untuk hipotesis
INSERT INTO hypothesis (code, description) VALUES
('H1', 'Dampak negatif terhadap kesehatan fisik (gangguan tidur, sakit kepala, mata lelah)'),
('H2', 'Dampak negatif terhadap kesehatan mental (kecemasan, depresi, mood swing)'),
('H3', 'Dampak negatif terhadap performa akademik (penurunan nilai, absensi)'),
('H4', 'Dampak negatif terhadap hubungan sosial (isolasi, konflik dengan teman/keluarga)'),
('H5', 'Dampak negatif terhadap manajemen waktu (prokrastinasi, kehilangan waktu produktif)');

-- Insert data awal untuk pertanyaan hipotesis 1
INSERT INTO question (hypothesis_id, code, text) VALUES
(1, 'Q1-1', 'Saya sering merasa sakit kepala setelah bermain game online dalam waktu lama'),
(1, 'Q1-2', 'Jam tidur saya terganggu karena bermain game online hingga larut malam'),
(1, 'Q1-3', 'Mata saya sering terasa lelah dan kering setelah bermain game online'),
(1, 'Q1-4', 'Saya merasakan nyeri pada pergelangan tangan atau jari setelah bermain game dalam waktu lama'),
(1, 'Q1-5', 'Saya sering melewatkan waktu makan karena terlalu fokus bermain game online');

-- Insert data awal untuk pertanyaan hipotesis 2
INSERT INTO question (hypothesis_id, code, text) VALUES
(2, 'Q2-1', 'Saya merasa cemas ketika tidak bisa bermain game online'),
(2, 'Q2-2', 'Mood saya berubah-ubah (mudah marah/sedih) ketika kalah dalam game'),
(2, 'Q2-3', 'Saya kesulitan berkonsentrasi pada kegiatan lain karena terus memikirkan game'),
(2, 'Q2-4', 'Saya merasa tertekan ketika tidak mencapai target dalam game'),
(2, 'Q2-5', 'Saya sering merasa tidak berharga di dunia nyata dibandingkan dengan pencapaian di game');

-- Insert data awal untuk pertanyaan hipotesis 3
INSERT INTO question (hypothesis_id, code, text) VALUES
(3, 'Q3-1', 'Nilai akademik saya menurun sejak saya bermain game online secara intensif'),
(3, 'Q3-2', 'Saya sering tidak mengerjakan tugas kuliah karena bermain game online'),
(3, 'Q3-3', 'Saya pernah tidak masuk kuliah karena bermain game online semalaman'),
(3, 'Q3-4', 'Saya sulit fokus saat kuliah karena memikirkan strategi atau level dalam game'),
(3, 'Q3-5', 'Saya lebih memilih bermain game daripada belajar untuk ujian');

-- Insert data awal untuk pertanyaan hipotesis 4
INSERT INTO question (hypothesis_id, code, text) VALUES
(4, 'Q4-1', 'Saya lebih memilih bermain game online daripada berkumpul dengan teman-teman'),
(4, 'Q4-2', 'Keluarga saya sering mengeluhkan waktu yang saya habiskan untuk bermain game'),
(4, 'Q4-3', 'Saya pernah berkonflik dengan teman/keluarga karena masalah game online'),
(4, 'Q4-4', 'Saya merasa lebih nyaman berinteraksi dengan teman online daripada teman di dunia nyata'),
(4, 'Q4-5', 'Saya menolak ajakan kegiatan sosial karena ingin bermain game online');

-- Insert data awal untuk pertanyaan hipotesis 5
INSERT INTO question (hypothesis_id, code, text) VALUES
(5, 'Q5-1', 'Saya sering menunda-nunda pekerjaan penting karena bermain game online'),
(5, 'Q5-2', 'Waktu bermain game online saya semakin bertambah dari waktu ke waktu'),
(5, 'Q5-3', 'Saya sering bermain game online lebih lama dari yang saya rencanakan'),
(5, 'Q5-4', 'Saya merasa waktu produktif saya banyak terbuang karena bermain game online'),
(5, 'Q5-5', 'Saya kesulitan mengatur jadwal kegiatan sehari-hari karena terlalu banyak bermain game');