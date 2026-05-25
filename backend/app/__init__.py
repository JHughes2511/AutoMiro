import os
from flask import Flask
from flask_cors import CORS
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    os.makedirs(Config.PROJECTS_DIR, exist_ok=True)
    os.makedirs(Config.REPORTS_DIR, exist_ok=True)

    from .api.projects import bp as projects_bp
    from .api.briefs import bp as briefs_bp
    from .api.agents import bp as agents_bp
    from .api.output import bp as output_bp

    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(briefs_bp, url_prefix="/api/briefs")
    app.register_blueprint(agents_bp, url_prefix="/api/agents")
    app.register_blueprint(output_bp, url_prefix="/api/output")

    return app
