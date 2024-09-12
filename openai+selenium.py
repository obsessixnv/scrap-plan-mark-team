from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Render! Your Flask app is running.'

@app.route('/process', methods=['POST'])
def process_string():
    # Get the JSON data from the request
    data = request.get_json()
    
    # Ensure the data contains a 'text' field
    if 'text' not in data:
        return jsonify({'error': 'Missing "text" field'}), 400
    
    text = data['text']
    
    # Process the text (you can modify this as needed)
    processed_text = f"Received text: {text}"
    
    # Return JSON response
    return jsonify({'status': 'success', 'processed_text': processed_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
