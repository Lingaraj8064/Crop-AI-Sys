-- Core tables
CREATE TABLE plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    scientific_name TEXT,
    family TEXT
);

CREATE TABLE diseases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    symptoms TEXT,
    causes TEXT,
    treatments TEXT
);

CREATE TABLE plant_diseases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER,
    disease_id INTEGER,
    severity_level TEXT,
    FOREIGN KEY (plant_id) REFERENCES plants(id),
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT,
    plant_id INTEGER,
    disease_id INTEGER,
    confidence REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(id),
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    messages TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE soil_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER,
    ph_range TEXT,
    nutrients TEXT,
    drainage TEXT,
    FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE weather_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER,
    temperature_range TEXT,
    humidity TEXT,
    rainfall TEXT,
    FOREIGN KEY (plant_id) REFERENCES plants(id)
);
