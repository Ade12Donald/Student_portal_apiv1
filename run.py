from dotenv import load_dotenv

load_dotenv()  # reads .env before the app starts, if one exists

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
