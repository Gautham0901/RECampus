-- Insert different types of users first
INSERT INTO user (email, password, role) VALUES 
('admin@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'admin'),
('printer@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'printer'),
('warden@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'warden'),
('hod_cse@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'hod'),
('studentcare@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'student_care'),
('doctor@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'doctor'),
('student1@campus.com', 'pbkdf2:sha256:600000$YOUR_HASHED_PASSWORD', 'student');

-- Insert a student
INSERT INTO student (user_id, name, roll_number, department) VALUES 
(7, 'John Doe', '2023CSE001', 'Computer Science');

-- Insert an HOD
INSERT INTO hod (user_id, name, department) VALUES 
(4, 'Dr. Smith', 'Computer Science');

-- Insert printer shop admin
INSERT INTO printer_shop (user_id) VALUES 
(2);

-- Insert hostel warden
INSERT INTO hostel_warden (user_id, hostel_name) VALUES 
(3, 'Block A');

-- Insert student care staff
INSERT INTO student_care (user_id) VALUES 
(5);

-- Insert health centre doctor
INSERT INTO health_centre (user_id, doctor_name) VALUES 
(6, 'Dr. Johnson');

-- Add this to your init_db() function
CREATE TRIGGER IF NOT EXISTS update_event_status
AFTER UPDATE ON event
BEGIN
    -- Update status to approved when all required approvals are received
    UPDATE event 
    SET status = CASE
        -- If needs both transport and food
        WHEN needs_transport AND needs_food THEN
            CASE WHEN coordinator_approval = 'approved' 
                 AND principal_approval = 'approved'
                 AND transport_approval = 'approved'
                 AND food_approval = 'approved'
            THEN 'approved' ELSE status END
        -- If needs only transport
        WHEN needs_transport AND NOT needs_food THEN
            CASE WHEN coordinator_approval = 'approved'
                 AND principal_approval = 'approved'
                 AND transport_approval = 'approved'
            THEN 'approved' ELSE status END
        -- If needs only food
        WHEN NOT needs_transport AND needs_food THEN
            CASE WHEN coordinator_approval = 'approved'
                 AND principal_approval = 'approved'
                 AND food_approval = 'approved'
            THEN 'approved' ELSE status END
        -- If needs no special approvals
        ELSE 
            CASE WHEN coordinator_approval = 'approved'
                 AND principal_approval = 'approved'
            THEN 'approved' ELSE status END
    END
    WHERE id = NEW.id;
END; 