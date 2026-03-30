from app import crear_app, bd
import os

app = crear_app(os.getenv('FLASK_CONFIG') or 'por_defecto')

if __name__ == '__main__':
    app.run()

@app.shell_context_processor
def make_shell_context():
    return {'bd': bd, 'app': app}
