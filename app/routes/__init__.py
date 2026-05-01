"""
Routes package - registers all blueprints.
"""


def register_routes(app):
    from .auth_routes import auth_bp
    from .llm_routes import llm_bp
    from .diary_routes import diary_bp
    from .conversation_routes import conversation_bp
    from .chat_routes import chat_bp
    from .mood_routes import mood_bp
    from .stats_routes import stats_bp
    from .garden_routes import garden_bp
    from .info_routes import info_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(diary_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(garden_bp)
    app.register_blueprint(info_bp)
