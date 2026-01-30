from flask import Blueprint, jsonify, request
from backend.services.telemetry_service import TelemetryService
from datetime import datetime

telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api')

# Initialize service
telemetry_service = TelemetryService()


@telemetry_bp.route('/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    """Get the latest telemetry data."""
    try:
        data = telemetry_service.get_latest_telemetry()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/telemetry/history', methods=['GET'])
def get_telemetry_history():
    """Get historical telemetry data with optional filters."""
    try:
        # Parse query parameters
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 500)  # Cap at 500 records

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Parse dates if provided
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        data = telemetry_service.get_telemetry_history(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            'count': len(data),
            'data': data
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/robot/command', methods=['POST'])
def execute_command():
    """Execute a robot command."""
    try:
        # Validate request body
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()

        if 'command' not in data:
            return jsonify({'error': 'Missing required field: command'}), 400

        command = data['command'].lower().strip()

        # Validate command
        valid_commands = ['start', 'stop', 'reset']
        if command not in valid_commands:
            return jsonify({
                'error': f'Invalid command. Valid commands: {", ".join(valid_commands)}'
            }), 400

        result = telemetry_service.execute_command(command)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/robot/status', methods=['GET'])
def get_robot_status():
    """Get current robot status."""
    try:
        telemetry = telemetry_service.get_latest_telemetry()
        return jsonify({
            'status': telemetry.get('status', 'unknown'),
            'is_running': telemetry_service.simulator.is_running
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/commands/history', methods=['GET'])
def get_command_history():
    """Get recent command history."""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)

        data = telemetry_service.get_command_history(limit=limit)
        return jsonify({
            'count': len(data),
            'data': data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
