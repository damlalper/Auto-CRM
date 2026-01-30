import random
from datetime import datetime


class RobotSimulator:
    """Simulator for generating robot telemetry data."""

    # Status weights: working is most common, error is rare
    STATUS_CHOICES = ['idle', 'working', 'working', 'working', 'error']

    # Telemetry ranges
    TEMP_MIN = 35.0
    TEMP_MAX = 55.0
    BATTERY_MIN = 20
    BATTERY_MAX = 100
    RPM_MIN = 800
    RPM_MAX = 1800

    def __init__(self):
        """Initialize simulator with default state."""
        self._running = True
        self._current_status = 'idle'
        self._battery_level = random.randint(70, 100)

    @property
    def is_running(self):
        """Check if simulator is running."""
        return self._running

    def start(self):
        """Start the robot simulation."""
        self._running = True
        self._current_status = 'working'
        return {'success': True, 'message': 'Robot started'}

    def stop(self):
        """Stop the robot simulation."""
        self._running = False
        self._current_status = 'idle'
        return {'success': True, 'message': 'Robot stopped'}

    def reset(self):
        """Reset the robot to initial state."""
        self._running = True
        self._current_status = 'idle'
        self._battery_level = random.randint(70, 100)
        return {'success': True, 'message': 'Robot reset'}

    def generate_telemetry(self):
        """Generate simulated telemetry data."""
        # Temperature varies based on status
        if self._current_status == 'working':
            temperature = random.uniform(40.0, self.TEMP_MAX)
        elif self._current_status == 'error':
            temperature = random.uniform(50.0, 60.0)
        else:
            temperature = random.uniform(self.TEMP_MIN, 42.0)

        # Battery decreases slowly when working
        if self._running and self._current_status == 'working':
            self._battery_level = max(
                self.BATTERY_MIN,
                self._battery_level - random.uniform(0, 0.5)
            )
        battery = int(self._battery_level)

        # Motor RPM based on status
        if self._current_status == 'working':
            motor_rpm = random.randint(1200, self.RPM_MAX)
        elif self._current_status == 'error':
            motor_rpm = random.randint(0, 500)
        else:
            motor_rpm = random.randint(self.RPM_MIN, 1000)

        # Randomly change status (with low probability)
        if self._running and random.random() < 0.1:
            self._current_status = random.choice(self.STATUS_CHOICES)

        # If battery is low, increase error probability
        if battery < 30 and random.random() < 0.3:
            self._current_status = 'error'

        return {
            'temperature': round(temperature, 1),
            'battery': battery,
            'motor_rpm': motor_rpm,
            'status': self._current_status,
            'timestamp': datetime.utcnow().isoformat()
        }

    def execute_command(self, command):
        """Execute a robot command."""
        commands = {
            'start': self.start,
            'stop': self.stop,
            'reset': self.reset
        }

        if command not in commands:
            return {
                'success': False,
                'message': f'Unknown command: {command}'
            }

        return commands[command]()
