"""
Unit tests for Foxglove Bridge integration.
"""

import pytest
from backend.foxglove.bridge import FoxgloveBridge, FoxgloveMessage


class TestFoxgloveMessage:
    """Tests for FoxgloveMessage formatting."""

    @pytest.fixture
    def sample_telemetry(self):
        """Sample telemetry data for testing."""
        return {
            'temperature': 42.5,
            'battery': 75,
            'motor_rpm': 1200,
            'status': 'working',
            'timestamp': '2026-01-30T12:00:00'
        }

    def test_create_telemetry_message(self, sample_telemetry):
        """Test creating Foxglove telemetry message."""
        message = FoxgloveMessage.create_telemetry_message(sample_telemetry)

        assert message['topic'] == '/robot/telemetry'
        assert 'timestamp' in message
        assert 'data' in message

        data = message['data']
        assert 'header' in data
        assert 'temperature' in data
        assert 'battery' in data
        assert 'motor' in data
        assert 'status' in data

        # Check temperature conversion
        assert data['temperature']['value'] == sample_telemetry['temperature']
        assert data['temperature']['unit'] == 'celsius'

        # Check battery conversion
        assert data['battery']['percentage'] == sample_telemetry['battery'] / 100.0

        # Check motor conversion
        assert data['motor']['rpm'] == sample_telemetry['motor_rpm']

    def test_create_diagnostic_message(self, sample_telemetry):
        """Test creating Foxglove diagnostic message."""
        message = FoxgloveMessage.create_diagnostic_message(sample_telemetry)

        assert message['topic'] == '/diagnostics'
        assert 'data' in message
        assert 'status' in message['data']

        status = message['data']['status'][0]
        assert status['name'] == 'Robot Status'
        assert status['hardware_id'] == 'robot_001'
        assert len(status['values']) == 4

    def test_create_pose_message(self, sample_telemetry):
        """Test creating Foxglove pose message."""
        message = FoxgloveMessage.create_pose_message(sample_telemetry)

        assert message['topic'] == '/robot/pose'
        assert 'data' in message
        assert 'pose' in message['data']

        pose = message['data']['pose']
        assert 'position' in pose
        assert 'orientation' in pose
        assert 'x' in pose['position']
        assert 'y' in pose['position']
        assert 'z' in pose['position']

    def test_diagnostic_level_by_status(self):
        """Test diagnostic level varies by robot status."""
        # Idle status
        idle_telemetry = {'temperature': 40, 'battery': 80, 'motor_rpm': 1000, 'status': 'idle'}
        idle_msg = FoxgloveMessage.create_diagnostic_message(idle_telemetry)
        assert idle_msg['data']['status'][0]['level'] == 0

        # Working status
        working_telemetry = {'temperature': 40, 'battery': 80, 'motor_rpm': 1000, 'status': 'working'}
        working_msg = FoxgloveMessage.create_diagnostic_message(working_telemetry)
        assert working_msg['data']['status'][0]['level'] == 0

        # Error status
        error_telemetry = {'temperature': 40, 'battery': 80, 'motor_rpm': 1000, 'status': 'error'}
        error_msg = FoxgloveMessage.create_diagnostic_message(error_telemetry)
        assert error_msg['data']['status'][0]['level'] == 2


class TestFoxgloveBridge:
    """Tests for FoxgloveBridge class."""

    @pytest.fixture
    def bridge(self):
        """Create a bridge instance for testing."""
        return FoxgloveBridge()

    @pytest.fixture
    def sample_telemetry(self):
        """Sample telemetry data for testing."""
        return {
            'temperature': 42.5,
            'battery': 75,
            'motor_rpm': 1200,
            'status': 'working',
            'timestamp': '2026-01-30T12:00:00'
        }

    def test_get_channels(self, bridge):
        """Test getting available channels."""
        channels = bridge.get_channels()

        assert len(channels) == 3
        topics = [ch['topic'] for ch in channels]
        assert '/robot/telemetry' in topics
        assert '/diagnostics' in topics
        assert '/robot/pose' in topics

    def test_get_server_info(self, bridge):
        """Test getting server info."""
        info = bridge.get_server_info()

        assert info['name'] == 'Robot Telemetry Bridge'
        assert 'capabilities' in info
        assert 'supportedEncodings' in info
        assert 'json' in info['supportedEncodings']

    def test_convert_telemetry(self, bridge, sample_telemetry):
        """Test converting telemetry to Foxglove format."""
        messages = bridge.convert_telemetry(sample_telemetry)

        assert len(messages) == 3
        topics = [msg['topic'] for msg in messages]
        assert '/robot/telemetry' in topics
        assert '/diagnostics' in topics
        assert '/robot/pose' in topics

    def test_format_for_export(self, bridge, sample_telemetry):
        """Test formatting data for export."""
        history = [sample_telemetry, sample_telemetry]
        export = bridge.format_for_export(history)

        assert export['format'] == 'foxglove_bridge_export'
        assert export['version'] == '1.0'
        assert 'channels' in export
        assert 'messages' in export
        assert 'metadata' in export
        assert export['metadata']['message_count'] == 6  # 3 messages per telemetry × 2
