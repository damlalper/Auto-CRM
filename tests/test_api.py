"""
Unit tests for Robot Telemetry API endpoints.
"""

import pytest
import json


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestTelemetryAPI:
    """Tests for telemetry API endpoints."""

    def test_get_latest_telemetry(self, client):
        """Test getting latest telemetry data."""
        response = client.get('/api/telemetry/latest')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Check required fields
        assert 'temperature' in data
        assert 'battery' in data
        assert 'motor_rpm' in data
        assert 'status' in data
        assert 'timestamp' in data

    def test_get_telemetry_history(self, client):
        """Test getting telemetry history."""
        response = client.get('/api/telemetry/history')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'count' in data
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_get_telemetry_history_with_limit(self, client):
        """Test getting telemetry history with limit parameter."""
        response = client.get('/api/telemetry/history?limit=5')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['count'] <= 5


class TestRobotCommandAPI:
    """Tests for robot command API endpoints."""

    def test_send_start_command(self, client):
        """Test sending start command."""
        response = client.post(
            '/api/robot/command',
            data=json.dumps({'command': 'start'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'started' in data['message'].lower()

    def test_send_stop_command(self, client):
        """Test sending stop command."""
        response = client.post(
            '/api/robot/command',
            data=json.dumps({'command': 'stop'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'stopped' in data['message'].lower()

    def test_send_reset_command(self, client):
        """Test sending reset command."""
        response = client.post(
            '/api/robot/command',
            data=json.dumps({'command': 'reset'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'reset' in data['message'].lower()

    def test_send_invalid_command(self, client):
        """Test sending invalid command returns error."""
        response = client.post(
            '/api/robot/command',
            data=json.dumps({'command': 'invalid'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_send_command_missing_field(self, client):
        """Test sending command without command field returns error."""
        response = client.post(
            '/api/robot/command',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_send_command_wrong_content_type(self, client):
        """Test sending command with wrong content type returns error."""
        response = client.post(
            '/api/robot/command',
            data='command=start',
            content_type='text/plain'
        )
        assert response.status_code == 400


class TestFoxgloveAPI:
    """Tests for Foxglove API endpoints."""

    def test_get_foxglove_info(self, client):
        """Test getting Foxglove server info."""
        response = client.get('/api/foxglove/info')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'name' in data
        assert 'capabilities' in data
        assert 'supportedEncodings' in data

    def test_get_foxglove_channels(self, client):
        """Test getting Foxglove channels."""
        response = client.get('/api/foxglove/channels')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'count' in data
        assert 'channels' in data
        assert len(data['channels']) > 0

    def test_get_foxglove_telemetry(self, client):
        """Test getting telemetry in Foxglove format."""
        response = client.get('/api/foxglove/telemetry')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'messages' in data
        assert isinstance(data['messages'], list)

    def test_get_foxglove_export(self, client):
        """Test Foxglove data export."""
        response = client.get('/api/foxglove/export?limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'format' in data
        assert 'channels' in data
        assert 'messages' in data
        assert 'metadata' in data
