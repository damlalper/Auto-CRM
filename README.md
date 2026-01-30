# 🤖 Robot Telemetry & Web-Based Monitoring Dashboard

## Overview

This project is a **fullstack web application** designed to simulate, collect, process, and visualize telemetry data coming from robotic systems. The system follows **industrial software practices** and demonstrates end-to-end development using Python-based backend services and a web-based user interface.

The application focuses on:

* Real-time telemetry visualization
* Backend service development
* REST API design
* Database persistence
* Cloud deployment

This repository is intentionally structured to be **clear and machine-readable**, enabling both humans and LLM-based systems to fully understand the system architecture, responsibilities, and data flow.

---

## Core Objectives

* Simulate robotic system telemetry data
* Expose telemetry through RESTful backend services
* Visualize data on a responsive web dashboard
* Store historical telemetry data in a relational database
* Demonstrate junior-level fullstack engineering skills aligned with industrial robotics software

---

## System Architecture

```
[ Robot Telemetry Simulator ]
            |
            v
[ Flask Backend REST API ]
            |
            v
[ PostgreSQL Database ]
            |
            v
[ Web Dashboard (HTML / CSS / Bootstrap / JS) ]
```

---

## Telemetry Data Model

The system simulates robotic telemetry data with the following attributes:

* `temperature` (float, °C)
* `battery` (integer, percentage)
* `motor_rpm` (integer)
* `status` (string: idle | working | error)
* `timestamp` (ISO 8601 format)

Example telemetry payload:

```json
{
  "temperature": 42.1,
  "battery": 79,
  "motor_rpm": 1440,
  "status": "working",
  "timestamp": "2026-01-30T13:10:00"
}
```

---

## Backend

### Technology

* Python
* Flask
* REST API architecture
* PostgreSQL

### Responsibilities

* Generate simulated robotic telemetry data at configurable intervals
* Validate and process telemetry data
* Persist telemetry records into the database
* Serve telemetry data via REST endpoints
* Handle basic robot control commands (simulated)

### API Endpoints

```http
GET  /api/telemetry/latest    # Fetch latest telemetry data
GET  /api/telemetry/history   # Fetch historical telemetry data
POST /api/robot/command       # Send simulated robot commands
```

---

## Frontend

### Technology

* HTML
* CSS
* Bootstrap
* JavaScript
* Chart.js

### Features

* Responsive dashboard layout
* Live telemetry visualization
* Battery and temperature indicators
* Time-series charts for sensor data
* Robot operational status display

The frontend consumes backend REST APIs and updates the UI dynamically without page reloads.

---

## Database

### Technology

* PostgreSQL

### Schema

```sql
telemetry
---------
id (PK)
temperature
battery
motor_rpm
status
timestamp
```

---

## Project Structure

```
robot-telemetry-dashboard/
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── simulator/
├── frontend/
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   └── js/
├── database/
│   └── schema.sql
├── README.md
└── requirements.txt
```

---

## Deployment

* Application is designed to be deployed as a **single fullstack service**
* Backend and frontend are served from the same Flask application
* PostgreSQL is hosted using a managed cloud database
* Environment-based configuration is used for credentials

---

## Non-Functional Characteristics

* Modular and maintainable codebase
* Clear separation of concerns
* Input validation on all API endpoints
* Logging enabled for backend services
* Designed for extensibility and future enhancements

---

## Alignment With Job Requirements

This project intentionally includes the following competencies:

* Python backend development
* Flask-based REST APIs
* HTML / CSS / Bootstrap UI development
* JavaScript-based data visualization
* SQL database usage
* Git-based version control
* Robotics-oriented telemetry processing

---


## Future Extensions (Optional)

* WebSocket-based real-time updates
* Multi-robot telemetry support
* Authentication and authorization
* Alerting and threshold-based notifications

---

## Summary

This repository represents a **complete junior-level fullstack robotics monitoring system**, demonstrating real-world software development practices from backend services to frontend visualization and deployment.
