"""
Foxglove API Routes

Provides REST endpoints for Foxglove Studio integration:
- Server info and channel listing
- Telemetry data in Foxglove format
- Data export for MCAP recording
"""

from flask import Blueprint, jsonify, request
from backend.foxglove.bridge import FoxgloveBridge
from backend.services.telemetry_service import TelemetryService

foxglove_bp = Blueprint('foxglove', __name__, url_prefix='/api/foxglove')

# Initialize services
foxglove_bridge = FoxgloveBridge()
telemetry_service = TelemetryService()


@foxglove_bp.route('/info', methods=['GET'])
def get_server_info():
    """Get Foxglove server information."""
    return jsonify(foxglove_bridge.get_server_info()), 200


@foxglove_bp.route('/channels', methods=['GET'])
def get_channels():
    """Get available Foxglove channels/topics."""
    channels = foxglove_bridge.get_channels()
    return jsonify({
        'count': len(channels),
        'channels': channels
    }), 200


@foxglove_bp.route('/telemetry', methods=['GET'])
def get_foxglove_telemetry():
    """Get latest telemetry in Foxglove format."""
    try:
        telemetry = telemetry_service.get_latest_telemetry()
        messages = foxglove_bridge.convert_telemetry(telemetry)

        return jsonify({
            'messages': messages
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@foxglove_bp.route('/stream', methods=['GET'])
def get_telemetry_stream():
    """
    Get telemetry history in Foxglove streaming format.

    Query params:
    - limit: Number of records (default: 50)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 500)

        history = telemetry_service.get_telemetry_history(limit=limit)

        all_messages = []
        for telemetry in history:
            all_messages.extend(foxglove_bridge.convert_telemetry(telemetry))

        return jsonify({
            'count': len(all_messages),
            'messages': all_messages
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@foxglove_bp.route('/export', methods=['GET'])
def export_for_foxglove():
    """
    Export telemetry data in Foxglove-compatible format.

    This format can be imported into Foxglove Studio for
    offline visualization and analysis.

    Query params:
    - limit: Number of records (default: 100)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 1000)

        history = telemetry_service.get_telemetry_history(limit=limit)
        export_data = foxglove_bridge.format_for_export(history)

        return jsonify(export_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@foxglove_bp.route('/schema/<topic_name>', methods=['GET'])
def get_topic_schema(topic_name):
    """Get schema for a specific topic."""
    channels = foxglove_bridge.get_channels()

    for channel in channels:
        if channel['topic'].replace('/', '_')[1:] == topic_name or \
           channel['topic'] == f'/{topic_name}':
            return jsonify({
                'topic': channel['topic'],
                'schemaName': channel['schemaName'],
                'schema': channel['schema']
            }), 200

    return jsonify({'error': f'Topic not found: {topic_name}'}), 404
