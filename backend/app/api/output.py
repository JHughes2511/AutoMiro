from flask import Blueprint, jsonify
from ..services.project_manager import ProjectManager

bp = Blueprint("output", __name__)
_pm = ProjectManager()


@bp.route("/<project_id>/report", methods=["GET"])
def get_report(project_id):
    project = _pm.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({
        "project_id": project_id,
        "morning_report": project.morning_report,
        "synthesis": project.synthesis_result,
        "status": project.status.value,
    })


@bp.route("/<project_id>/vision", methods=["GET"])
def get_vision(project_id):
    project = _pm.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    vision = project.synthesis_result.get("final_vision", {})
    return jsonify({
        "project_id": project_id,
        "vision": vision,
        "status": project.status.value,
    })
