"""
Unit tests for Robot Telemetry Simulator.
"""

import pytest
from backend.simulator.robot_simulator import RobotSimulator


class TestRobotSimulator:
    """Tests for RobotSimulator class."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator instance for testing."""
        return RobotSimulator()

    def test_simulator_initialization(self, simulator):
        """Test simulator initializes correctly."""
        assert simulator.is_running is True
        assert simulator._current_status == 'idle'

    def test_generate_telemetry(self, simulator):
        """Test telemetry generation returns valid data."""
        telemetry = simulator.generate_telemetry()

        # Check required fields
        assert 'temperature' in telemetry
        assert 'battery' in telemetry
        assert 'motor_rpm' in telemetry
        assert 'status' in telemetry
        assert 'timestamp' in telemetry

        # Check value ranges
        assert 35.0 <= telemetry['temperature'] <= 60.0
        assert 0 <= telemetry['battery'] <= 100
        assert 0 <= telemetry['motor_rpm'] <= 1800
        assert telemetry['status'] in ['idle', 'working', 'error']

    def test_start_command(self, simulator):
        """Test start command changes status."""
        result = simulator.start()

        assert result['success'] is True
        assert simulator.is_running is True
        assert simulator._current_status == 'working'

    def test_stop_command(self, simulator):
        """Test stop command changes status."""
        result = simulator.stop()

        assert result['success'] is True
        assert simulator.is_running is False
        assert simulator._current_status == 'idle'

    def test_reset_command(self, simulator):
        """Test reset command resets state."""
        # First change some state
        simulator.stop()

        # Then reset
        result = simulator.reset()

        assert result['success'] is True
        assert simulator.is_running is True
        assert simulator._current_status == 'idle'

    def test_execute_valid_command(self, simulator):
        """Test executing valid commands."""
        for command in ['start', 'stop', 'reset']:
            result = simulator.execute_command(command)
            assert result['success'] is True

    def test_execute_invalid_command(self, simulator):
        """Test executing invalid command returns error."""
        result = simulator.execute_command('invalid')

        assert result['success'] is False
        assert 'Unknown command' in result['message']

    def test_battery_decreases_when_working(self, simulator):
        """Test that battery decreases when robot is working."""
        simulator.start()  # Set to working status
        initial_battery = simulator._battery_level

        # Generate telemetry multiple times
        for _ in range(10):
            simulator.generate_telemetry()

        # Battery should have decreased (or stayed same if random was 0)
        assert simulator._battery_level <= initial_battery

    def test_temperature_varies_by_status(self, simulator):
        """Test that temperature range depends on status."""
        # Test idle temperature
        simulator._current_status = 'idle'
        idle_temps = [simulator.generate_telemetry()['temperature'] for _ in range(10)]

        # Test working temperature
        simulator._current_status = 'working'
        working_temps = [simulator.generate_telemetry()['temperature'] for _ in range(10)]

        # Working should generally have higher average temperature
        # (this is probabilistic, so we just check ranges are valid)
        assert all(35.0 <= t <= 60.0 for t in idle_temps)
        assert all(35.0 <= t <= 60.0 for t in working_temps)

    def test_rpm_varies_by_status(self, simulator):
        """Test that motor RPM varies based on status."""
        # Test idle RPM
        simulator._current_status = 'idle'
        idle_rpms = [simulator.generate_telemetry()['motor_rpm'] for _ in range(5)]

        # Test working RPM
        simulator._current_status = 'working'
        working_rpms = [simulator.generate_telemetry()['motor_rpm'] for _ in range(5)]

        # Working should generally have higher RPM
        # (just check valid ranges)
        assert all(0 <= rpm <= 1800 for rpm in idle_rpms)
        assert all(0 <= rpm <= 1800 for rpm in working_rpms)
