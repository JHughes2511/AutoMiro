from flask import Blueprint, request, jsonify

bp = Blueprint("briefs", __name__)


@bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "service": "AutoMiro Briefs"})
