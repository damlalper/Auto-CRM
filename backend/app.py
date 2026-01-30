import os
import sys
import threading
import time
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from backend.config import get_config
from backend.models.telemetry import db
from backend.routes.telemetry import telemetry_bp, telemetry_service
from backend.routes.foxglove import foxglove_bp
from backend.routes.robots import robots_bp
from backend.websocket.socket_handler import socketio, init_socketio, broadcast_telemetry, broadcast_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=None):
    """Application factory."""
    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    init_socketio(app)

    # Register blueprints
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(foxglove_bp)
    app.register_blueprint(robots_bp)

    # Create database tables and ensure default robot exists
    with app.app_context():
        db.create_all()
        telemetry_service.ensure_default_robot()
        logger.info('Database tables created')
        logger.info('Default robot initialized')

    # Main route - serve dashboard
    @app.route('/')
    def index():
        return render_template('index.html')

    # Health check endpoint
    @app.route('/health')
    def health():
        from backend.websocket.socket_handler import get_connected_clients_count
        return jsonify({
            'status': 'healthy',
            'websocket_clients': get_connected_clients_count()
        }), 200

    # Start background telemetry generator in production
    interval = app.config.get('TELEMETRY_INTERVAL', 2)
    generator_thread = threading.Thread(
        target=telemetry_generator,
        args=(app, interval),
        daemon=True
    )
    generator_thread.start()
    logger.info(f'Background telemetry generator started with {interval}s interval')

    return app


def check_alerts(telemetry_data):
    """Check telemetry data for alert conditions."""
    alerts = []

    # Temperature alert
    if telemetry_data.get('temperature', 0) > 50:
        alerts.append({
            'type': 'warning',
            'category': 'temperature',
            'message': f"High temperature: {telemetry_data['temperature']}°C",
            'threshold': 50,
            'value': telemetry_data['temperature']
        })

    if telemetry_data.get('temperature', 0) > 55:
        alerts.append({
            'type': 'critical',
            'category': 'temperature',
            'message': f"Critical temperature: {telemetry_data['temperature']}°C",
            'threshold': 55,
            'value': telemetry_data['temperature']
        })

    # Battery alert
    if telemetry_data.get('battery', 100) < 20:
        alerts.append({
            'type': 'warning',
            'category': 'battery',
            'message': f"Low battery: {telemetry_data['battery']}%",
            'threshold': 20,
            'value': telemetry_data['battery']
        })

    if telemetry_data.get('battery', 100) < 10:
        alerts.append({
            'type': 'critical',
            'category': 'battery',
            'message': f"Critical battery: {telemetry_data['battery']}%",
            'threshold': 10,
            'value': telemetry_data['battery']
        })

    # Error status alert
    if telemetry_data.get('status') == 'error':
        alerts.append({
            'type': 'critical',
            'category': 'status',
            'message': "Robot in ERROR state",
            'value': 'error'
        })

    return alerts


def telemetry_generator(app, interval=2):
    """Background thread to generate and save telemetry data."""
    with app.app_context():
        logger.info(f'Starting telemetry generator with {interval}s interval')
        while True:
            try:
                data = telemetry_service.generate_and_save_telemetry()
                logger.debug(f'Generated telemetry: {data}')

                # Broadcast via WebSocket
                broadcast_telemetry(data)

                # Check for alerts
                alerts = check_alerts(data)
                for alert in alerts:
                    broadcast_alert(alert)
                    logger.warning(f"Alert: {alert['message']}")

            except Exception as e:
                logger.error(f'Error generating telemetry: {e}')
            time.sleep(interval)


def run_app():
    """Run the application with telemetry generator."""
    app = create_app()

    # Get telemetry interval from config
    interval = app.config.get('TELEMETRY_INTERVAL', 2)

    # Start background telemetry generator
    generator_thread = threading.Thread(
        target=telemetry_generator,
        args=(app, interval),
        daemon=True
    )
    generator_thread.start()

    # Run Flask app with SocketIO
    port = int(os.getenv('PORT', 5000))
    debug = app.config.get('DEBUG', False)

    logger.info(f'Starting Robot Telemetry Dashboard on port {port}')
    logger.info(f'WebSocket enabled at ws://localhost:{port}')
    logger.info('Foxglove API available at /api/foxglove')

    socketio.run(app, host='0.0.0.0', port=port, debug=debug, use_reloader=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_app()
