from app.factory import create_app
from app.routes import bp

app = create_app()
app.register_blueprint(bp)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
