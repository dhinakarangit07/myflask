from flask import Flask, request, jsonify
from flask_cors import CORS
from helpers import solve_captcha_and_search, quit_driver

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET'])
def home():
    """
    Home page with instructions on how to use the CNR details API.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CNR Details API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            pre { background: #f4f4f4; padding: 15px; border-radius: 5px; }
            code { font-family: Consolas, monospace; }
        </style>
    </head>
    <body>
        <h1>CNR Details API Documentation</h1>
        <p>Welcome to the CNR Details API. This API allows you to fetch case details using a CNR number.</p>
        
        <h2>Endpoint</h2>
        <pre><code>GET /api/case-details</code></pre>
        
        <h2>Query Parameters</h2>
        <ul>
            <li><code>cnr_number</code> (required): The CNR number for which to fetch case details.</li>
        </ul>
        
        <h2>Example Request</h2>
        <pre><code>curl http://localhost:5000/api/case-details?cnr_number=MHAU010012342022</code></pre>
        
        <h2>Example Responses</h2>
        <h3>Success Response (200)</h3>
        <pre><code>{
    "status": "success",
    "data": {
        // Case details here
    }
}</code></pre>
        
        <h3>Error Response (400 - Missing CNR number)</h3>
        <pre><code>{
    "error": "CNR number is required",
    "status": "failure"
}</code></pre>
        
        <h3>Error Response (500 - Server error)</h3>
        <pre><code>{
    "error": "Failed to fetch case details: [error message]",
    "status": "failure"
}</code></pre>
        
        <h2>Notes</h2>
        <ul>
            <li>Ensure the CNR number is valid before making a request.</li>
            <li>The API handles CAPTCHA solving internally.</li>
            <li>Contact the administrator for API access or support.</li>
        </ul>
    </body>
    </html>
    """

@app.route('/api/case-details', methods=['GET'])
def get_case_details():
    """
    API endpoint to fetch case details by CNR number.
    Query parameter: cnr_number (required)
    Returns: JSON response with case details or error message
    """
    cnr_number = request.args.get('cnr_number')
    
    if not cnr_number:
        return jsonify({
            'error': 'CNR number is required',
            'status': 'failure'
        }), 400
    
    try:
        result = solve_captcha_and_search(cnr_number)
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch case details: {str(e)}',
            'status': 'failure'
        }), 500

@app.teardown_appcontext
def cleanup(exception=None):
    """
    Ensure the WebDriver is closed when the application context is torn down.
    """
    quit_driver()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)