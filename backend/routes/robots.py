"""
Robot Management API Routes

Provides REST endpoints for multi-robot management:
- Robot registration and listing
- Robot-specific telemetry and commands
"""

from flask import Blueprint, jsonify, request
from backend.models.telemetry import db, Robot, Telemetry, Command
from backend.services.telemetry_service import TelemetryService
from datetime import datetime

robots_bp = Blueprint('robots', __name__, url_prefix='/api/robots')


@robots_bp.route('', methods=['GET'])
def get_all_robots():
    """Get list of all registered robots."""
    try:
        robots = Robot.query.all()
        return jsonify({
            'count': len(robots),
            'robots': [robot.to_dict() for robot in robots]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@robots_bp.route('', methods=['POST'])
def register_robot():
    """Register a new robot."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()

        # Validate required fields
        if 'id' not in data or 'name' not in data:
            return jsonify({'error': 'Missing required fields: id, name'}), 400

        # Check if robot already exists
        existing = Robot.query.get(data['id'])
        if existing:
            return jsonify({'error': f"Robot with id '{data['id']}' already exists"}), 409

        robot = Robot(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            location=data.get('location'),
            is_active=data.get('is_active', True)
        )

        db.session.add(robot)
        db.session.commit()

        return jsonify({
            'message': 'Robot registered successfully',
            'robot': robot.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/<robot_id>', methods=['GET'])
def get_robot(robot_id):
    """Get details of a specific robot."""
    try:
        robot = Robot.query.get(robot_id)
        if not robot:
            return jsonify({'error': f"Robot '{robot_id}' not found"}), 404

        # Get latest telemetry for this robot
        latest_telemetry = Telemetry.query.filter_by(robot_id=robot_id)\
            .order_by(Telemetry.timestamp.desc()).first()

        response = robot.to_dict()
        if latest_telemetry:
            response['latest_telemetry'] = latest_telemetry.to_dict()

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/<robot_id>', methods=['PUT'])
def update_robot(robot_id):
    """Update robot information."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        robot = Robot.query.get(robot_id)
        if not robot:
            return jsonify({'error': f"Robot '{robot_id}' not found"}), 404

        data = request.get_json()

        if 'name' in data:
            robot.name = data['name']
        if 'description' in data:
            robot.description = data['description']
        if 'location' in data:
            robot.location = data['location']
        if 'is_active' in data:
            robot.is_active = data['is_active']

        db.session.commit()

        return jsonify({
            'message': 'Robot updated successfully',
            'robot': robot.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/<robot_id>', methods=['DELETE'])
def delete_robot(robot_id):
    """Delete a robot (soft delete by setting inactive)."""
    try:
        robot = Robot.query.get(robot_id)
        if not robot:
            return jsonify({'error': f"Robot '{robot_id}' not found"}), 404

        robot.is_active = False
        db.session.commit()

        return jsonify({
            'message': f"Robot '{robot_id}' deactivated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/<robot_id>/telemetry/latest', methods=['GET'])
def get_robot_latest_telemetry(robot_id):
    """Get latest telemetry for a specific robot."""
    try:
        telemetry = Telemetry.query.filter_by(robot_id=robot_id)\
            .order_by(Telemetry.timestamp.desc()).first()

        if not telemetry:
            return jsonify({'error': f"No telemetry data for robot '{robot_id}'"}), 404

        return jsonify(telemetry.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/<robot_id>/telemetry/history', methods=['GET'])
def get_robot_telemetry_history(robot_id):
    """Get telemetry history for a specific robot."""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 500)

        telemetry_records = Telemetry.query.filter_by(robot_id=robot_id)\
            .order_by(Telemetry.timestamp.desc())\
            .limit(limit).all()

        return jsonify({
            'robot_id': robot_id,
            'count': len(telemetry_records),
            'data': [record.to_dict() for record in telemetry_records]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/<robot_id>/command', methods=['POST'])
def send_robot_command(robot_id):
    """Send command to a specific robot."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        # Verify robot exists
        robot = Robot.query.get(robot_id)
        if not robot:
            return jsonify({'error': f"Robot '{robot_id}' not found"}), 404

        if not robot.is_active:
            return jsonify({'error': f"Robot '{robot_id}' is not active"}), 400

        data = request.get_json()

        if 'command' not in data:
            return jsonify({'error': 'Missing required field: command'}), 400

        command = data['command'].lower().strip()
        valid_commands = ['start', 'stop', 'reset']

        if command not in valid_commands:
            return jsonify({
                'error': f'Invalid command. Valid commands: {", ".join(valid_commands)}'
            }), 400

        # Log command
        cmd_log = Command(robot_id=robot_id, command=command)
        db.session.add(cmd_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Command '{command}' sent to robot '{robot_id}'",
            'robot_id': robot_id,
            'command': command
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@robots_bp.route('/summary', methods=['GET'])
def get_robots_summary():
    """Get summary of all robots with their latest status."""
    try:
        robots = Robot.query.filter_by(is_active=True).all()
        summary = []

        for robot in robots:
            latest = Telemetry.query.filter_by(robot_id=robot.id)\
                .order_by(Telemetry.timestamp.desc()).first()

            robot_summary = {
                'id': robot.id,
                'name': robot.name,
                'location': robot.location,
                'status': latest.status if latest else 'unknown',
                'battery': latest.battery if latest else None,
                'temperature': latest.temperature if latest else None,
                'last_update': latest.timestamp.isoformat() if latest else None
            }
            summary.append(robot_summary)

        return jsonify({
            'count': len(summary),
            'robots': summary
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
