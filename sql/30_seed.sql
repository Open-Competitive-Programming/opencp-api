-- SEED DATA FOR open-cp DATABASE
-- Creates only the initial admin user.

INSERT INTO users (fname, lname, username, rating)
VALUES ('Admin', 'User', 'admin', 0)
ON CONFLICT (username) DO NOTHING;
