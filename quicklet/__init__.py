from flask import Flask,session
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate


csrf=CSRFProtect()


def create_app():
    from quicklet import config
    from quicklet.models import db,User,Agent
    app=Flask(__name__,instance_relative_config=True)
    app.config.from_pyfile('config.py',silent=True)
    app.config.from_object(config.DevelopmentConfig)
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app,db)


    @app.context_processor
    def inject_user_and_agent():
        user = None
        agent = None
        if 'useronline' in session:
            user = User.query.get(session['useronline'])
        if 'agentonline' in session:
            agent = Agent.query.get(session['agentonline'])
        return dict(user=user, agent=agent)
    return app


app=create_app()

from quicklet import user_routes,admin_routes, agent_routes
from quicklet import models,form