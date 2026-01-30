"""
Foxglove Bridge Integration

Foxglove is a robotics visualization tool that supports various data formats.
This bridge converts our telemetry data to Foxglove-compatible format and
provides WebSocket streaming capability.

Foxglove WebSocket Protocol: https://docs.foxglove.dev/docs/connecting-to-data/frameworks/websocket
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
import threading
import logging

logger = logging.getLogger(__name__)


class FoxgloveMessage:
    """Foxglove-compatible message format."""

    @staticmethod
    def create_telemetry_message(telemetry_data: Dict) -> Dict:
        """
        Convert telemetry data to Foxglove-compatible format.

        Foxglove expects messages with specific schema for visualization.
        We use a custom schema that maps to Foxglove's supported types.
        """
        timestamp_ns = int(datetime.utcnow().timestamp() * 1e9)

        return {
            "topic": "/robot/telemetry",
            "timestamp": {
                "sec": int(timestamp_ns // 1e9),
                "nsec": int(timestamp_ns % 1e9)
            },
            "data": {
                "header": {
                    "stamp": {
                        "sec": int(timestamp_ns // 1e9),
                        "nsec": int(timestamp_ns % 1e9)
                    },
                    "frame_id": "robot_base"
                },
                "temperature": {
                    "value": telemetry_data.get("temperature", 0.0),
                    "unit": "celsius",
                    "variance": 0.1
                },
                "battery": {
                    "percentage": telemetry_data.get("battery", 0) / 100.0,
                    "voltage": 12.0 + (telemetry_data.get("battery", 0) / 100.0) * 2.0,
                    "current": 1.5,
                    "charge": telemetry_data.get("battery", 0) / 100.0 * 5.0,
                    "capacity": 5.0,
                    "power_supply_status": 2 if telemetry_data.get("battery", 0) > 20 else 1
                },
                "motor": {
                    "rpm": telemetry_data.get("motor_rpm", 0),
                    "velocity": telemetry_data.get("motor_rpm", 0) * 0.1047,  # rad/s
                    "effort": abs(telemetry_data.get("motor_rpm", 0)) / 1800.0 * 100.0
                },
                "status": {
                    "level": {
                        "idle": 0,
                        "working": 1,
                        "error": 2
                    }.get(telemetry_data.get("status", "idle"), 0),
                    "name": telemetry_data.get("status", "unknown"),
                    "message": f"Robot is {telemetry_data.get('status', 'unknown')}"
                }
            }
        }

    @staticmethod
    def create_diagnostic_message(telemetry_data: Dict) -> Dict:
        """Create Foxglove DiagnosticArray-compatible message."""
        timestamp_ns = int(datetime.utcnow().timestamp() * 1e9)

        status = telemetry_data.get("status", "idle")
        level = {"idle": 0, "working": 0, "error": 2}.get(status, 0)

        return {
            "topic": "/diagnostics",
            "timestamp": {
                "sec": int(timestamp_ns // 1e9),
                "nsec": int(timestamp_ns % 1e9)
            },
            "data": {
                "header": {
                    "stamp": {
                        "sec": int(timestamp_ns // 1e9),
                        "nsec": int(timestamp_ns % 1e9)
                    },
                    "frame_id": ""
                },
                "status": [
                    {
                        "level": level,
                        "name": "Robot Status",
                        "message": f"Robot is {status}",
                        "hardware_id": "robot_001",
                        "values": [
                            {"key": "temperature", "value": str(telemetry_data.get("temperature", 0))},
                            {"key": "battery", "value": str(telemetry_data.get("battery", 0))},
                            {"key": "motor_rpm", "value": str(telemetry_data.get("motor_rpm", 0))},
                            {"key": "status", "value": status}
                        ]
                    }
                ]
            }
        }

    @staticmethod
    def create_pose_message(telemetry_data: Dict) -> Dict:
        """Create simulated robot pose for Foxglove 3D visualization."""
        timestamp_ns = int(datetime.utcnow().timestamp() * 1e9)

        # Simulate robot movement based on status
        status = telemetry_data.get("status", "idle")
        rpm = telemetry_data.get("motor_rpm", 0)

        # Simple position simulation
        t = time.time()
        if status == "working":
            x = 2.0 * (rpm / 1800.0) * abs(((t % 10) - 5) / 5)
            y = 1.0 * (rpm / 1800.0) * abs(((t % 8) - 4) / 4)
        else:
            x = 0.0
            y = 0.0

        return {
            "topic": "/robot/pose",
            "timestamp": {
                "sec": int(timestamp_ns // 1e9),
                "nsec": int(timestamp_ns % 1e9)
            },
            "data": {
                "header": {
                    "stamp": {
                        "sec": int(timestamp_ns // 1e9),
                        "nsec": int(timestamp_ns % 1e9)
                    },
                    "frame_id": "world"
                },
                "pose": {
                    "position": {"x": x, "y": y, "z": 0.0},
                    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                }
            }
        }


class FoxgloveBridge:
    """
    Bridge for Foxglove Studio integration.

    Provides:
    - Telemetry data conversion to Foxglove format
    - Channel/topic management
    - Message schema definitions
    """

    # Foxglove channel definitions
    CHANNELS = [
        {
            "id": 1,
            "topic": "/robot/telemetry",
            "encoding": "json",
            "schemaName": "robot_telemetry/Telemetry",
            "schema": json.dumps({
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "temperature": {"type": "object"},
                    "battery": {"type": "object"},
                    "motor": {"type": "object"},
                    "status": {"type": "object"}
                }
            })
        },
        {
            "id": 2,
            "topic": "/diagnostics",
            "encoding": "json",
            "schemaName": "diagnostic_msgs/DiagnosticArray",
            "schema": json.dumps({
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "status": {"type": "array"}
                }
            })
        },
        {
            "id": 3,
            "topic": "/robot/pose",
            "encoding": "json",
            "schemaName": "geometry_msgs/PoseStamped",
            "schema": json.dumps({
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "pose": {"type": "object"}
                }
            })
        }
    ]

    def __init__(self):
        """Initialize Foxglove bridge."""
        self.subscribers: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        logger.info("Foxglove Bridge initialized")

    def get_channels(self) -> List[Dict]:
        """Get available Foxglove channels."""
        return self.CHANNELS

    def get_server_info(self) -> Dict:
        """Get Foxglove server information."""
        return {
            "name": "Robot Telemetry Bridge",
            "capabilities": ["clientPublish", "time", "parameters"],
            "supportedEncodings": ["json"],
            "metadata": {
                "version": "1.0.0",
                "robot_id": "robot_001"
            },
            "sessionId": f"session_{int(time.time())}"
        }

    def convert_telemetry(self, telemetry_data: Dict) -> List[Dict]:
        """
        Convert telemetry data to all Foxglove message formats.

        Returns a list of messages for different topics.
        """
        return [
            FoxgloveMessage.create_telemetry_message(telemetry_data),
            FoxgloveMessage.create_diagnostic_message(telemetry_data),
            FoxgloveMessage.create_pose_message(telemetry_data)
        ]

    def format_for_export(self, telemetry_history: List[Dict]) -> Dict:
        """
        Format telemetry history for Foxglove MCAP export.

        MCAP is Foxglove's preferred format for recorded data.
        """
        messages = []
        for telemetry in telemetry_history:
            messages.extend(self.convert_telemetry(telemetry))

        return {
            "format": "foxglove_bridge_export",
            "version": "1.0",
            "channels": self.CHANNELS,
            "messages": messages,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "message_count": len(messages),
                "duration_sec": len(telemetry_history) * 2  # Assuming 2s intervals
            }
        }
