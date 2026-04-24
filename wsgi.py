from app import create_app

app = create_app()

if __name__ == '__main__':
    # simple runner for debugging the WSGI entrypoint
    app.run(host='0.0.0.0', port=8000)
