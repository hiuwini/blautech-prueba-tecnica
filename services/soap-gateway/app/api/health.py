from __future__ import annotations

from flask import Blueprint, current_app, jsonify


health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health")
def health() -> tuple[object, int]:
    config = current_app.config["GATEWAY_CONFIG"]
    return jsonify({"status": "ok", "service": config.service_name}), 200
