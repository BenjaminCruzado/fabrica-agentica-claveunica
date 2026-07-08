CREATE TABLE citizens (id TEXT PRIMARY KEY, name TEXT, run TEXT, email TEXT, phone TEXT, digital_address TEXT, mfa TEXT);
CREATE TABLE procedures (id TEXT PRIMARY KEY, name TEXT, status TEXT, owner TEXT, updated_at TEXT);
CREATE TABLE notifications (id TEXT PRIMARY KEY, subject TEXT, priority TEXT, read INTEGER, procedure_id TEXT);
CREATE TABLE sessions (id TEXT PRIMARY KEY, device TEXT, location TEXT, active INTEGER, trusted INTEGER);
CREATE TABLE consents (id TEXT PRIMARY KEY, institution TEXT, data TEXT, status TEXT, expires_at TEXT);
CREATE TABLE cases (id TEXT PRIMARY KEY, status TEXT, responsible TEXT, procedure_id TEXT);
CREATE TABLE tickets (id TEXT PRIMARY KEY, topic TEXT, status TEXT, updated_at TEXT);
CREATE TABLE screen_records (route TEXT, field_a TEXT, field_b TEXT, field_c TEXT, source TEXT);
CREATE TABLE events (id TEXT PRIMARY KEY, type TEXT, screen TEXT, message TEXT, created_at TEXT);
