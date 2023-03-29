from flask import Blueprint, render_template

app_blueprint =  Blueprint('app_blueprint', __name__)

@app_blueprint.route('/')
def homepage():
    return render_template("homepage.html")