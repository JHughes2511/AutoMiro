from flask import Blueprint, request, jsonify
from ..services.project_manager import ProjectManager

bp = Blueprint("agents", __name__)
_pm = ProjectManager()


@bp.route("/<project_id>/status", methods=["GET"])
def agent_status(project_id):
    project = _pm.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({
        "project_id": project_id,
        "project_status": project.status.value,
        "agents": project.agent_states,
    })
