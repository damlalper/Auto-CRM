from datetime import datetime, timedelta
from backend.models.telemetry import db, Telemetry, Command, Robot
from backend.simulator.robot_simulator import RobotSimulator


class TelemetryService:
    """Service layer for telemetry operations."""

    DEFAULT_ROBOT_ID = 'robot_001'

    def __init__(self, robot_id=None):
        """Initialize telemetry service with robot simulator."""
        self.robot_id = robot_id or self.DEFAULT_ROBOT_ID
        self.simulator = RobotSimulator()

    def ensure_default_robot(self):
        """Ensure default robot exists in database."""
        robot = Robot.query.get(self.DEFAULT_ROBOT_ID)
        if not robot:
            robot = Robot(
                id=self.DEFAULT_ROBOT_ID,
                name='Primary Robot',
                description='Default simulated robot',
                location='Main Floor',
                is_active=True
            )
            db.session.add(robot)
            db.session.commit()
        return robot

    def get_latest_telemetry(self, robot_id=None):
        """Get the most recent telemetry record."""
        rid = robot_id or self.robot_id

        telemetry = Telemetry.query.filter_by(robot_id=rid).order_by(
            Telemetry.timestamp.desc()
        ).first()

        if telemetry:
            return telemetry.to_dict()

        # If no data exists, generate new telemetry
        data = self.simulator.generate_telemetry()
        data['robot_id'] = rid
        return data

    def get_telemetry_history(self, limit=50, start_date=None, end_date=None, robot_id=None):
        """Get historical telemetry data with optional filters."""
        query = Telemetry.query

        # Filter by robot if specified
        if robot_id:
            query = query.filter_by(robot_id=robot_id)

        # Apply date filters
        if start_date:
            query = query.filter(Telemetry.timestamp >= start_date)
        if end_date:
            query = query.filter(Telemetry.timestamp <= end_date)

        # Order by timestamp descending and limit results
        telemetry_records = query.order_by(
            Telemetry.timestamp.desc()
        ).limit(limit).all()

        return [record.to_dict() for record in telemetry_records]

    def save_telemetry(self, data=None, robot_id=None):
        """Save telemetry data to database."""
        if data is None:
            data = self.simulator.generate_telemetry()

        rid = robot_id or data.get('robot_id') or self.robot_id

        telemetry = Telemetry(
            robot_id=rid,
            temperature=data['temperature'],
            battery=data['battery'],
            motor_rpm=data['motor_rpm'],
            status=data['status'],
            timestamp=datetime.fromisoformat(data['timestamp'])
                if isinstance(data['timestamp'], str)
                else data['timestamp']
        )

        db.session.add(telemetry)
        db.session.commit()

        return telemetry.to_dict()

    def generate_and_save_telemetry(self, robot_id=None):
        """Generate new telemetry and save to database."""
        data = self.simulator.generate_telemetry()
        return self.save_telemetry(data, robot_id or self.robot_id)

    def execute_command(self, command, robot_id=None):
        """Execute a robot command and log it."""
        rid = robot_id or self.robot_id

        # Validate command
        valid_commands = ['start', 'stop', 'reset']
        if command not in valid_commands:
            return {
                'success': False,
                'message': f'Invalid command. Valid commands: {", ".join(valid_commands)}'
            }

        # Execute command on simulator
        result = self.simulator.execute_command(command)

        # Log command to database
        cmd_log = Command(robot_id=rid, command=command)
        db.session.add(cmd_log)
        db.session.commit()

        result['robot_id'] = rid
        return result

    def get_command_history(self, limit=20, robot_id=None):
        """Get recent command history."""
        query = Command.query

        if robot_id:
            query = query.filter_by(robot_id=robot_id)

        commands = query.order_by(
            Command.executed_at.desc()
        ).limit(limit).all()

        return [cmd.to_dict() for cmd in commands]

    def cleanup_old_data(self, days=7):
        """Remove telemetry data older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = Telemetry.query.filter(
            Telemetry.timestamp < cutoff_date
        ).delete()

        db.session.commit()
        return {'deleted_records': deleted}

    def get_all_robots_status(self):
        """Get status summary for all active robots."""
        robots = Robot.query.filter_by(is_active=True).all()
        status_list = []

        for robot in robots:
            latest = Telemetry.query.filter_by(robot_id=robot.id)\
                .order_by(Telemetry.timestamp.desc()).first()

            status_list.append({
                'robot_id': robot.id,
                'name': robot.name,
                'status': latest.status if latest else 'unknown',
                'battery': latest.battery if latest else None,
                'temperature': latest.temperature if latest else None,
                'last_update': latest.timestamp.isoformat() if latest else None
            })

        return status_list
