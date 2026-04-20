from app import create_app

app = create_app()

if __name__ == '__main__':
    # simple runner for debugging the WSGI entrypoint
    app.run(host='127.0.0.1', port=8000)
