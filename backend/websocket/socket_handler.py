"""
WebSocket Handler for Real-time Telemetry Streaming

Provides real-time telemetry updates via Socket.IO WebSocket connection.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import logging

logger = logging.getLogger(__name__)

# Initialize SocketIO with CORS support
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

# Track connected clients
connected_clients = set()


def init_socketio(app):
    """Initialize SocketIO with Flask app."""
    socketio.init_app(app)
    logger.info("WebSocket initialized")
    return socketio


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection."""
    client_id = request.sid
    connected_clients.add(client_id)
    logger.info(f"Client connected: {client_id}. Total clients: {len(connected_clients)}")

    emit('connection_status', {
        'status': 'connected',
        'client_id': client_id,
        'message': 'Connected to Robot Telemetry WebSocket'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    client_id = request.sid
    connected_clients.discard(client_id)
    logger.info(f"Client disconnected: {client_id}. Total clients: {len(connected_clients)}")


@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to a specific telemetry channel."""
    channel = data.get('channel', 'telemetry')
    client_id = request.sid

    join_room(channel)
    logger.info(f"Client {client_id} subscribed to channel: {channel}")

    emit('subscribed', {
        'channel': channel,
        'message': f'Subscribed to {channel} updates'
    })


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Unsubscribe from a telemetry channel."""
    channel = data.get('channel', 'telemetry')
    client_id = request.sid

    leave_room(channel)
    logger.info(f"Client {client_id} unsubscribed from channel: {channel}")

    emit('unsubscribed', {
        'channel': channel,
        'message': f'Unsubscribed from {channel}'
    })


@socketio.on('ping')
def handle_ping():
    """Handle ping for connection keep-alive."""
    emit('pong', {'message': 'pong'})


def broadcast_telemetry(telemetry_data):
    """
    Broadcast telemetry data to all connected clients.

    This function is called by the telemetry generator to push
    real-time updates to all WebSocket clients.
    """
    if connected_clients:
        socketio.emit('telemetry_update', telemetry_data, room='telemetry')
        socketio.emit('telemetry_update', telemetry_data)  # Also emit to all
        logger.debug(f"Broadcasted telemetry to {len(connected_clients)} clients")


def broadcast_alert(alert_data):
    """Broadcast alert to all connected clients."""
    socketio.emit('alert', alert_data)
    logger.info(f"Broadcasted alert: {alert_data.get('message', 'Unknown alert')}")


def broadcast_command_result(result):
    """Broadcast command execution result."""
    socketio.emit('command_result', result)


def get_connected_clients_count():
    """Get number of connected WebSocket clients."""
    return len(connected_clients)
