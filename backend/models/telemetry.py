from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Robot(db.Model):
    """Model for robot registration and management."""
    __tablename__ = 'robots'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to telemetry data
    telemetry_data = db.relationship('Telemetry', backref='robot', lazy='dynamic')
    commands = db.relationship('Command', backref='robot', lazy='dynamic')

    def __repr__(self):
        return f'<Robot {self.id}: {self.name}>'

    def to_dict(self):
        """Convert robot record to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Telemetry(db.Model):
    """Model for robot telemetry data."""
    __tablename__ = 'telemetry'

    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.String(50), db.ForeignKey('robots.id'), default='robot_001')
    temperature = db.Column(db.Float, nullable=False)
    battery = db.Column(db.Integer, nullable=False)
    motor_rpm = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Telemetry {self.id} - {self.robot_id} - {self.status} at {self.timestamp}>'

    def to_dict(self):
        """Convert telemetry record to dictionary."""
        return {
            'id': self.id,
            'robot_id': self.robot_id,
            'temperature': round(self.temperature, 1),
            'battery': self.battery,
            'motor_rpm': self.motor_rpm,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Command(db.Model):
    """Model for robot command logs."""
    __tablename__ = 'commands'

    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.String(50), db.ForeignKey('robots.id'), default='robot_001')
    command = db.Column(db.String(50), nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Command {self.command} for {self.robot_id} at {self.executed_at}>'

    def to_dict(self):
        """Convert command record to dictionary."""
        return {
            'id': self.id,
            'robot_id': self.robot_id,
            'command': self.command,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }
