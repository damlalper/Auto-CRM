-- Robot Telemetry Database Schema
-- Supports multi-robot telemetry monitoring

-- Robots table for robot registration
CREATE TABLE IF NOT EXISTS robots (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry table for storing robot sensor data
CREATE TABLE IF NOT EXISTS telemetry (
    id SERIAL PRIMARY KEY,
    robot_id VARCHAR(50) REFERENCES robots(id) DEFAULT 'robot_001',
    temperature FLOAT NOT NULL,
    battery INTEGER NOT NULL CHECK (battery >= 0 AND battery <= 100),
    motor_rpm INTEGER NOT NULL CHECK (motor_rpm >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('idle', 'working', 'error')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Commands table for logging robot commands
CREATE TABLE IF NOT EXISTS commands (
    id SERIAL PRIMARY KEY,
    robot_id VARCHAR(50) REFERENCES robots(id) DEFAULT 'robot_001',
    command VARCHAR(50) NOT NULL CHECK (command IN ('start', 'stop', 'reset')),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_telemetry_robot_id ON telemetry(robot_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_robot_timestamp ON telemetry(robot_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_commands_robot_id ON commands(robot_id);
CREATE INDEX IF NOT EXISTS idx_commands_executed_at ON commands(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_robots_is_active ON robots(is_active);

-- Insert default robot
INSERT INTO robots (id, name, description, location, is_active)
VALUES ('robot_001', 'Primary Robot', 'Default simulated robot', 'Main Floor', TRUE)
ON CONFLICT (id) DO NOTHING;
