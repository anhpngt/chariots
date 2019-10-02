"""
Used to run the server locally. In production, the object
app.app is run directly.
"""

from app import app

if __name__ == "__main__":
    app.run(port=5000, debug=True)
