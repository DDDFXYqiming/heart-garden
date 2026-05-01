"""
心语花园 - Heart Garden
AI 驱动的情感陪伴应用

Entry point.
"""

import os
from app import create_app, logger

app = create_app()

if __name__ == '__main__':
    try:
        from app.db import init_db

        port = int(os.environ.get('PORT', '5000'))
        debug = os.getenv('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
        with app.app_context():
            init_db()
        logger.info("=== 心语花园 v2.2 已启动 ===")
        logger.info(f"=== API: http://0.0.0.0:{port} ===")
        print("=== 心语花园 v2.2 已启动 ===")
        print(f"=== API: http://0.0.0.0:{port} ===")
        app.run(debug=debug, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
