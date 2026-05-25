from flask import Blueprint, request, jsonify
from ..services.project_manager import ProjectManager

bp = Blueprint("projects", __name__)
_pm = ProjectManager()


@bp.route("/", methods=["GET"])
def list_projects():
    return jsonify(_pm.list_projects())


@bp.route("/", methods=["POST"])
def create_project():
    data = request.json or {}
    name = data.get("name", "").strip()
    brief = data.get("brief", "").strip()
    if not name or not brief:
        return jsonify({"error": "name and brief are required"}), 400
    project = _pm.create_project(name, brief)
    return jsonify(project.to_dict()), 201


@bp.route("/<project_id>", methods=["GET"])
def get_project(project_id):
    project = _pm.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project.to_dict())


@bp.route("/<project_id>/clarify", methods=["GET"])
def get_clarifying_questions(project_id):
    try:
        questions = _pm.generate_clarifying_questions(project_id)
        return jsonify({"questions": questions})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp.route("/<project_id>/clarify", methods=["POST"])
def submit_clarifications(project_id):
    data = request.json or {}
    clarifications = data.get("clarifications", {})
    try:
        scope = _pm.submit_clarifications(project_id, clarifications)
        return jsonify({"scope": scope})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp.route("/<project_id>/add", methods=["POST"])
def add_to_brief(project_id):
    data = request.json or {}
    additional = data.get("input", "").strip()
    if not additional:
        return jsonify({"error": "input is required"}), 400
    try:
        scope = _pm.add_to_brief(project_id, additional)
        return jsonify({"scope": scope})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp.route("/<project_id>/start", methods=["POST"])
def start_research(project_id):
    try:
        thread_name = _pm.start_research(project_id)
        return jsonify({"status": "started", "thread": thread_name})
    except (ValueError, Exception) as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<project_id>/chat/<domain>", methods=["POST"])
def chat_with_agent(project_id, domain):
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    try:
        response = _pm.chat_with_agent(project_id, domain, message)
        return jsonify({"response": response})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
