from flask import Flask

# 'create_app' is called in main.py
def create_app():
    app= Flask(__name__)
    app.config['SECRET_KEY'] = 'groupfive'

    from .app_blueprint import app_blueprint
    # from .dash_application import create_dash_application

    app.register_blueprint(app_blueprint)
    
    # create_dash_application(app)
    return app