INSERT INTO citizens (run, full_name, email, phone) VALUES ('12.345.678-9', 'Benjamin Cruzado', 'benjamin@example.local', '+56 9 0000 0000');
INSERT INTO procedures (citizen_id, name, status, owner) SELECT id, 'Actualizar domicilio digital', 'en curso', 'MINSEGPRES' FROM citizens WHERE run='12.345.678-9';
INSERT INTO procedures (citizen_id, name, status, owner) SELECT id, 'Solicitar certificado ciudadano', 'pendiente', 'Registro Civil' FROM citizens WHERE run='12.345.678-9';
INSERT INTO notifications (citizen_id, procedure_id, subject, priority) SELECT c.id, p.id, 'Vencimiento de tramite', 'alta' FROM citizens c JOIN procedures p ON p.citizen_id=c.id LIMIT 1;
INSERT INTO sessions (citizen_id, device, location, active, trusted) SELECT id, 'Notebook', 'Santiago', true, true FROM citizens WHERE run='12.345.678-9';
INSERT INTO consents (citizen_id, institution, data_scope, status, expires_at) SELECT id, 'Registro Civil', 'Identidad', 'vigente', '2026-12-31' FROM citizens WHERE run='12.345.678-9';
INSERT INTO cases (citizen_id, procedure_id, status, responsible) SELECT c.id, p.id, 'en revision', 'Mesa ciudadana' FROM citizens c JOIN procedures p ON p.citizen_id=c.id LIMIT 1;
