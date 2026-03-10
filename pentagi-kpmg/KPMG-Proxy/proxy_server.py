"""
KPMG Azure API Headers Injector - APIM Portal Compatible Version
================================================================
This version matches the exact format used by the APIM developer portal.
"""

import os
import json
import logging
from flask import Flask, request, Response, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dotenv import load_dotenv
load_dotenv()

# KPMG API Configuration
KPMG_API_BASE = os.getenv("KPMG_API_BASE", "https://api.workbench.kpmg/genai/azure/inference/chat/completions?api-version=2024-04-01-preview")
KPMG_SUBSCRIPTION_KEY = os.getenv("KPMG_SUBSCRIPTION_KEY", "")
KPMG_CHARGE_CODE = os.getenv("KPMG_CHARGE_CODE", "")
PORT = int(os.getenv("PORT", 8080))

# Network settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 120))
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", 60))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create session
def create_session():
    session = requests.Session()
    session.trust_env = True  # Use system proxy if configured
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry_strategy
    )
    
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    return session

session = create_session()


def build_kpmg_headers(model_deployment: str) -> dict:
    """Build headers exactly as APIM portal does."""
    headers = {
        "Content-Type": "application/json",
        "azureml-model-deployment": model_deployment,
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": KPMG_SUBSCRIPTION_KEY,
    }
    
    # Add charge code if provided
    if KPMG_CHARGE_CODE:
        headers["x-kpmg-charge-code"] = KPMG_CHARGE_CODE
    
    return headers


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Handle chat completion requests in OpenAI format, convert to KPMG format."""
    try:
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": {"message": "Invalid JSON", "type": "invalid_request"}}), 400
        
        # Extract model name
        model = data.get("model", "gpt-4o-2024-11-20-dzs-we")
        
        logger.info(f"Chat completion request - Model: {model}")
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        
        # Build KPMG URL - NO API VERSION PARAMETER
        kpmg_url = f"{KPMG_API_BASE}/chat/completions"
        
        # Build headers with model deployment
        headers = build_kpmg_headers(model)
        
        logger.info(f"Forwarding to: {kpmg_url}")
        logger.debug(f"Headers: azureml-model-deployment={model}, subscription-key={KPMG_SUBSCRIPTION_KEY[:10]}...")
        
        # Prepare request body - remove 'model' field as it goes in header
        kpmg_data = {k: v for k, v in data.items() if k != "model"}
        
        # Ensure required fields
        if "messages" not in kpmg_data:
            return jsonify({"error": {"message": "messages field is required", "type": "invalid_request"}}), 400
        
        logger.debug(f"Sending body: {json.dumps(kpmg_data, indent=2)}")
        
        # Check if streaming
        is_streaming = data.get("stream", False)
        
        try:
            if is_streaming:
                response = session.post(
                    kpmg_url,
                    headers=headers,
                    json=kpmg_data,
                    stream=True,
                    timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT),
                    verify=False
                )
                
                logger.info(f"KPMG API response status: {response.status_code}")
                
                if response.status_code >= 400:
                    error_text = response.text[:500]
                    logger.error(f"KPMG API error: {error_text}")
                    return jsonify({
                        "error": {
                            "message": f"KPMG API error: {response.status_code}",
                            "type": "api_error",
                            "details": error_text
                        }
                    }), response.status_code
                
                def generate():
                    try:
                        for chunk in response.iter_content(chunk_size=None):
                            if chunk:
                                yield chunk
                    except Exception as e:
                        logger.error(f"Error during streaming: {e}")
                
                return Response(
                    generate(),
                    content_type=response.headers.get("Content-Type", "text/event-stream"),
                    status=response.status_code
                )
            else:
                # Non-streaming request
                response = session.post(
                    kpmg_url,
                    headers=headers,
                    json=kpmg_data,
                    timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT),
                    verify=False
                )
                
                logger.info(f"KPMG API response status: {response.status_code}")
                
                if response.status_code >= 400:
                    error_text = response.text[:1000]
                    logger.error(f"KPMG API error {response.status_code}: {error_text}")
                    return jsonify({
                        "error": {
                            "message": f"KPMG API error: {response.status_code}",
                            "type": "api_error",
                            "details": error_text
                        }
                    }), response.status_code
                else:
                    logger.info(f"Success! Response length: {len(response.content)} bytes")
                    logger.debug(f"Response preview: {response.text[:200]}")
                
                return Response(
                    response.content,
                    content_type=response.headers.get("Content-Type", "application/json"),
                    status=response.status_code
                )
                
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            return jsonify({
                "error": {
                    "message": f"Request to KPMG API timed out after {REQUEST_TIMEOUT}s",
                    "type": "timeout",
                    "code": "timeout_error"
                }
            }), 504
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return jsonify({
                "error": {
                    "message": "Cannot connect to KPMG API. Check network/VPN.",
                    "type": "connection_error",
                    "code": "connection_failed",
                    "details": str(e)
                }
            }), 502
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return jsonify({
            "error": {
                "message": "Invalid JSON in request body",
                "type": "invalid_request"
            }
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "error": {
                "message": f"Internal error: {str(e)}",
                "type": "internal_error",
                "code": "internal_server_error"
            }
        }), 500


@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    """Handle embedding requests."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": {"message": "Invalid JSON", "type": "invalid_request"}}), 400
        
        model = data.get("model", "text-embedding-3-large-1-std-sdc")
        
        logger.info(f"Embedding request - Model: {model}")
        
        # Build URL - NO API VERSION
        kpmg_url = f"{KPMG_API_BASE}/embeddings"
        
        # Build headers
        headers = build_kpmg_headers(model)
        
        # Remove model from body
        kpmg_data = {k: v for k, v in data.items() if k != "model"}
        
        response = session.post(
            kpmg_url,
            headers=headers,
            json=kpmg_data,
            timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT),
            verify=False
        )
        
        logger.info(f"KPMG API response status: {response.status_code}")
        
        if response.status_code >= 400:
            logger.error(f"KPMG API error: {response.text[:500]}")
        
        return Response(
            response.content,
            content_type=response.headers.get("Content-Type", "application/json"),
            status=response.status_code
        )
        
    except Exception as e:
        logger.error(f"Error in embeddings: {str(e)}", exc_info=True)
        return jsonify({
            "error": {
                "message": f"Internal error: {str(e)}",
                "type": "internal_error"
            }
        }), 500


@app.route('/v1/models', methods=['GET'])
def list_models():
    """Return available models."""
    models = [
        {"id": "gpt-4o-2024-11-20-dzs-we", "object": "model", "owned_by": "kpmg-azure"},
        {"id": "gpt-4o-2024-08-06-dzs-we", "object": "model", "owned_by": "kpmg-azure"},
        {"id": "gpt-4o-mini-2024-07-18-dzs-we", "object": "model", "owned_by": "kpmg-azure"},
        {"id": "text-embedding-3-large-1-std-sdc", "object": "model", "owned_by": "kpmg-azure"},
    ]
    return jsonify({"object": "list", "data": models})


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "KPMG Azure API Headers Injector",
        "version": "3.0.0",
        "kpmg_api_base": KPMG_API_BASE,
        "subscription_key_set": bool(KPMG_SUBSCRIPTION_KEY),
        "charge_code_set": bool(KPMG_CHARGE_CODE),
        "note": "Matches APIM portal format exactly"
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        "service": "KPMG Azure OpenAI Headers Injector",
        "version": "3.0.0",
        "description": "OpenAI-compatible API with KPMG Azure headers",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "embeddings": "/v1/embeddings",
            "models": "/v1/models",
            "health": "/health"
        }
    })


if __name__ == "__main__":
    if not KPMG_SUBSCRIPTION_KEY:
        logger.error("=" * 70)
        logger.error("FATAL: KPMG_SUBSCRIPTION_KEY is required!")
        logger.error("=" * 70)
        exit(1)
    
    logger.info("=" * 70)
    logger.info("KPMG Azure API Headers Injector v3.0")
    logger.info("=" * 70)
    logger.info(f"KPMG API Base: {KPMG_API_BASE}")
    logger.info(f"Subscription Key: {'*' * 20}...{KPMG_SUBSCRIPTION_KEY[-4:] if len(KPMG_SUBSCRIPTION_KEY) > 4 else '****'}")
    logger.info(f"Charge Code: {KPMG_CHARGE_CODE if KPMG_CHARGE_CODE else 'Not set'}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Format: APIM Portal Compatible (no api-version)")
    logger.info("=" * 70)
    logger.info("Ready to accept requests...")
    logger.info("=" * 70)
    
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)