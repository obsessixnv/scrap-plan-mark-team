from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)  # Allow requests from all origins

@app.route('/extract_team_info', methods=['POST'])
def extract_team_info():
    try:
        data = request.json
        domain = data.get('domain')

        if not domain:
            return jsonify({"error": "Domain is required"}), 400

        # Simulated result
        team_info = [
            {
                "name": "John Doe",
                "title": "CEO",
                "info": "https://example.com/john-doe"
            }
        ]

        return jsonify({
            "team": team_info,
            "team_domain": domain
        })

    except Exception as e:
        # Log the exception
        print("Error occurred:", e)
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
