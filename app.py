from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from helpers import solve_captcha_and_search_with_status
from webdriver import initialize_driver, quit_driver
import atexit
import json
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize WebDriver when app starts
print("Starting application and initializing WebDriver...")
try:
    initialize_driver()
    print("WebDriver initialized successfully!")
except Exception as e:
    print(f"Failed to initialize WebDriver: {e}")
    exit(1)

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
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h3 { color: #2980b9; margin-top: 25px; }
            pre { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }
            code { font-family: 'Courier New', monospace; }
            .endpoint { background: #e8f5e8; padding: 10px; border-left: 4px solid #27ae60; margin: 10px 0; }
            .method { color: #27ae60; font-weight: bold; }
            .status { color: #e74c3c; font-weight: bold; }
            .new { color: #3498db; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #3498db; color: white; }
            .response-example { background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏛️ CNR Details API Documentation</h1>
            <p>Welcome to the CNR Details API. This API allows you to fetch comprehensive case details from Indian eCourts using a CNR (Case Number Record) number with real-time status updates.</p>
            
            <h2>📋 Available Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span> <code>/</code> - API Documentation (this page)
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code>/api/case-details</code> - Get case details with live status updates (SSE)
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code>/api/health</code> - Health check endpoint
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <code>/api/restart-driver</code> - Restart WebDriver (admin endpoint)
            </div>
            
            <h2>🔍 Main API Endpoint</h2>
            <h3>GET /api/case-details</h3>
            <p>Fetches comprehensive case details including case status, advocate information, case history, and orders.</p>
            
            <h4>Query Parameters</h4>
            <table>
                <tr><th>Parameter</th><th>Type</th><th>Required</th><th>Description</th></tr>
                <tr><td>cnr_number</td><td>string</td><td>Yes</td><td>The CNR number for which to fetch case details</td></tr>
            </table>
            
            <h4>Response Format</h4>
            <p class="new">This endpoint uses Server-Sent Events (SSE) to provide real-time status updates during processing.</p>
            
            <h2>📊 Response Data Structure</h2>
            <p>The API returns the following case information:</p>
            <ul>
                <li><strong>case_details</strong> - Basic case information (case number, case type, filing date, etc.)</li>
                <li><strong>case_status</strong> - Current status and stage of the case</li>
                <li><strong>petitioner_advocate</strong> - Petitioner's advocate details</li>
                <li><strong>respondent_advocate</strong> - Respondent's advocate details</li>
                <li><strong>acts</strong> - Legal acts and sections under which the case is filed</li>
                <li><strong>case_history</strong> - Complete chronological history of case proceedings</li>
                <li><strong>order</strong> - Court orders and judgments</li>
            </ul>
            
            <h2>🚀 Example Usage</h2>
            
            <h3>Using cURL</h3>
            <pre><code>curl -N http://localhost:5000/api/case-details?cnr_number=MHAU010012342022</code></pre>
            
            <h3>Using JavaScript (EventSource)</h3>
            <pre><code>const eventSource = new EventSource('/api/case-details?cnr_number=MHAU010012342022');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Status:', data.status);
    console.log('Message:', data.message);
    console.log('Progress:', data.progress + '%');
    
    if (data.status === 'success') {
        console.log('Case Details:', data.data);
        eventSource.close();
    }
};</code></pre>
            
            <h2>📡 Status Update Events</h2>
            <p>During processing, you'll receive real-time updates with the following structure:</p>
            <div class="response-example">
                <pre><code>{
    "status": "processing",
    "message": "Reading CAPTCHA image...",
    "progress": 25
}</code></pre>
            </div>
            
            <h3>Final Success Response</h3>
            <div class="response-example">
                <pre><code>{
    "status": "success",
    "message": "Case details extracted successfully!",
    "progress": 100,
    "data": {
        "case_details": [...],
        "case_status": [...],
        "petitioner_advocate": [...],
        "respondent_advocate": [...],
        "acts": [...],
        "case_history": [...],
        "order": [...]
    }
}</code></pre>
            </div>
            
            <h2>❌ Error Responses</h2>
            
            <h3>400 - Missing CNR Number</h3>
            <div class="response-example">
                <pre><code>{
    "error": "CNR number is required",
    "status": "failure"
}</code></pre>
            </div>
            
            <h3>Processing Error</h3>
            <div class="response-example">
                <pre><code>{
    "status": "error",
    "message": "Failed to extract case details: [error message]",
    "progress": 0
}</code></pre>
            </div>
            
            <h2>🔧 Health Check</h2>
            <h3>GET /api/health</h3>
            <p>Check if the WebDriver is running properly:</p>
            <pre><code>curl http://localhost:5000/api/health</code></pre>
            
            <h2>⚠️ Important Notes</h2>
            <ul>
                <li>Ensure the CNR number is valid and follows the correct format</li>
                <li>The API handles CAPTCHA solving automatically using OCR</li>
                <li class="new">Uses Server-Sent Events (SSE) for real-time progress updates</li>
                <li>Processing may take 30-60 seconds depending on server response times</li>
                <li>WebDriver is initialized once at startup for optimal performance</li>
                <li>Each successful request automatically closes the browser tab to prevent memory leaks</li>
                <li>The system includes automatic retry logic for CAPTCHA failures</li>
                <li>Maximum of 2 retry attempts per request</li>
            </ul>
            
            <h2>🐳 Docker Deployment</h2>
            <p>The API is containerized and ready for deployment:</p>
            <pre><code>docker build -t cnr-details-api .
docker run -p 5000:5000 cnr-details-api</code></pre>
            
            <div style="text-align: center; margin-top: 30px; color: #7f8c8d;">
               
                <p>🔧 Built with Flask, Selenium, and Chrome WebDriver</p>
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/api/case-details', methods=['GET'])
def get_case_details_stream():
    """
    API endpoint to fetch case details with live status updates using Server-Sent Events.
    Query parameter: cnr_number (required)
    Returns: SSE stream with status updates and final result
    """
    cnr_number = request.args.get('cnr_number')
    
    if not cnr_number:
        return jsonify({
            'error': 'CNR number is required',
            'status': 'failure'
        }), 400
    
    def generate_status_stream():
        """Generator function that yields status updates as SSE events."""
        try:
            # Call the enhanced function with status callback
            for status_update in solve_captcha_and_search_with_status(cnr_number):
                # Format as Server-Sent Event
                yield f"data: {json.dumps(status_update)}\n\n"
                time.sleep(0.1)  # Small delay to ensure proper streaming
                
        except Exception as e:
            # Send error as final event
            error_event = {
                'status': 'error',
                'message': f'Failed to fetch case details: {str(e)}',
                'progress': 0
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return Response(
        generate_status_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify if the WebDriver is running.
    """
    try:
        from webdriver import get_driver
        driver = get_driver()
        return jsonify({
            'status': 'healthy',
            'webdriver_status': 'running',
            'current_url': driver.current_url
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'webdriver_status': 'error',
            'error': str(e)
        }), 503

@app.route('/api/restart-driver', methods=['POST'])
def restart_driver_endpoint():
    """
    Endpoint to restart the WebDriver if it becomes unresponsive.
    """
    try:
        from webdriver import restart_driver
        restart_driver()
        return jsonify({
            'status': 'success',
            'message': 'WebDriver restarted successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'failure',
            'error': f'Failed to restart WebDriver: {str(e)}'
        }), 500

# Ensure cleanup happens when app shuts down
def cleanup_on_exit():
    """Clean up resources when the application is shutting down."""
    print("Application shutting down, cleaning up WebDriver...")
    quit_driver()

# Register cleanup function
atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)