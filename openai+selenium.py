from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Render! Your Flask app is running.'

