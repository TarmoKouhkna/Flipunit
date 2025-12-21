from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.conf import settings
import requests
import json
import logging

logger = logging.getLogger('ai_chat')


@ensure_csrf_cookie
def chat_index(request):
    """Render the AI chat page"""
    return render(request, 'ai_chat/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API endpoint to handle chat messages with Google Gemini"""
    logger.info("=== AI CHAT API CALLED ===")
    try:
        # Parse JSON request body
        if not request.body:
            return JsonResponse({
                'status': 'error',
                'error': 'Request body is required'
            }, status=400)
        
        if isinstance(request.body, bytes):
            body_str = request.body.decode('utf-8')
        else:
            body_str = request.body
        
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, body: {body_str[:200]}")
            return JsonResponse({
                'status': 'error',
                'error': 'Invalid JSON format'
            }, status=400)
        message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        
        if not message:
            return JsonResponse({
                'status': 'error',
                'error': 'Message is required'
            }, status=400)
        
        # Get API key from settings
        api_key = getattr(settings, 'GOOGLE_GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({
                'status': 'error',
                'error': 'AI service is not configured. Please contact support.'
            }, status=500)
        
        # Build conversation context
        # System context about the website
        system_context = """You are a helpful assistant for FlipUnit.eu, an online converter hub. 
        Users can convert between different units, formats, and tools. 
        Help users find the right converter or tool they need. 
        Be friendly, concise, and helpful. 
        If a user asks about a conversion that doesn't exist on the site, suggest the closest alternative or explain that it's not available.
        IMPORTANT: Always respond in the same language that the user writes in."""
        
        # Build contents array for Gemini API
        contents = []
        
        # Add conversation history (keep last 10 exchanges for context)
        # Gemini expects alternating user/assistant messages with roles
        for item in conversation_history[-10:]:  # Keep last 10 messages for context
            role = item.get('role')
            if role == 'user':
                contents.append({
                    'role': 'user',
                    'parts': [{'text': item.get('content', '')}]
                })
            elif role == 'assistant':
                contents.append({
                    'role': 'model',
                    'parts': [{'text': item.get('content', '')}]
                })
        
        # Add current user message
        contents.append({
            'role': 'user',
            'parts': [{'text': message}]
        })
        
        # Ensure we have at least one message
        if not contents:
            return JsonResponse({
                'status': 'error',
                'error': 'Failed to prepare message'
            }, status=500)
        
        # Prepare request to Google Gemini API
        # Try models in order: gemini-2.5-flash, gemini-2.0-flash-exp, gemini-1.5-flash
        models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash-exp',
            'gemini-1.5-flash'
        ]
        
        payload = {
            'contents': contents,
            'systemInstruction': {
                'parts': [{
                    'text': system_context
                }]
            },
            'tools': [{
                'google_search': {}
            }]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': api_key
        }
        
        # Try each model until one works
        response = None
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            
            # Always log request details (important for debugging production issues)
            tools_enabled = bool(payload.get('tools'))
            grounding_status = 'enabled' if tools_enabled else 'disabled'
            tools_config = payload.get('tools', [])
            logger.info(f"Gemini API request: Model={model_name}, URL={url}")
            logger.info(f"   Google Search grounding: {grounding_status}")
            logger.info(f"   Tools configuration: {tools_config}")
            logger.info(f"   Payload keys: {list(payload.keys())}")
            
            # Make API request
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                # If successful (200) or non-404 error, break and handle
                if response.status_code != 404:
                    # Always log which model was successfully used (important for debugging)
                    logger.info(f"Gemini API: Successfully using model '{model_name}' with Google Search grounding {grounding_status}")
                    break
                    
                # If 404, try next model
                logger.info(f"Model {model_name} not found (404), trying next model...")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Gemini API request failed for {model_name}: {e}")
                # If it's the last model, raise the exception
                if model_name == models_to_try[-1]:
                    raise
                # Otherwise, try next model
                continue
        
        # If no response was received (shouldn't happen, but safety check)
        if response is None:
            return JsonResponse({
                'status': 'error',
                'error': 'Failed to connect to AI service. Please try again.'
            }, status=500)
        
        if response.status_code == 200:
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini API response: {e}, response text: {response.text[:500]}")
                return JsonResponse({
                    'status': 'error',
                    'error': 'Invalid response from AI service'
                }, status=500)
            
            # Extract response text
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    if len(candidate['content']['parts']) > 0:
                        response_text = candidate['content']['parts'][0].get('text', '')
                        
                        # Check if grounding was used (always log this for debugging)
                        grounding_metadata = candidate.get('groundingMetadata', {})
                        candidate_keys = list(candidate.keys())
                        result_keys = list(result.keys())
                        
                        if grounding_metadata:
                            logger.info(f"✅ Google Search grounding WAS used - metadata keys: {list(grounding_metadata.keys())}")
                        else:
                            logger.warning(f"❌ Google Search grounding was NOT used - response may contain outdated information")
                            logger.warning(f"   Candidate keys: {candidate_keys}")
                            logger.warning(f"   Result keys: {result_keys}")
                            # Check if grounding might be at result level
                            if 'groundingMetadata' in result:
                                logger.warning(f"   Found groundingMetadata at result level: {list(result['groundingMetadata'].keys())}")
                        
                        return JsonResponse({
                            'status': 'success',
                            'message': response_text
                        })
            
            logger.warning(f"Unexpected Gemini API response format: {result}")
            return JsonResponse({
                'status': 'error',
                'error': 'Unexpected response format from AI service'
            }, status=500)
            
        elif response.status_code == 429:
            return JsonResponse({
                'status': 'error',
                'error': 'AI service is temporarily unavailable. Please try again in a moment.'
            }, status=429)
            
        elif response.status_code == 400:
            try:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Invalid request to AI service')
            except:
                error_message = response.text[:200] if response.text else 'Invalid request to AI service'
            logger.error(f"Gemini API 400 error: {error_message}")
            return JsonResponse({
                'status': 'error',
                'error': error_message
            }, status=400)
            
        elif response.status_code == 404:
            # All models failed - provide helpful error message
            try:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'No compatible model found. Please check your API tier or region availability.')
            except:
                error_message = 'No compatible model found. Please check your API tier or region availability.'
            logger.error(f"Gemini API 404 error: {error_message}, tried models: {', '.join(models_to_try)}")
            return JsonResponse({
                'status': 'error',
                'error': error_message
            }, status=404)
        else:
            return JsonResponse({
                'status': 'error',
                'error': f'AI service error (status {response.status_code}). Please try again.'
            }, status=500)
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'status': 'error',
            'error': 'Request timeout. Please try again.'
        }, status=504)
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'status': 'error',
            'error': 'Network error. Please check your connection and try again.'
        }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'error': 'Invalid request format'
        }, status=400)
        
    except Exception as e:
        logger.exception(f"Unexpected error in chat_api: {e}")
        return JsonResponse({
            'status': 'error',
            'error': f'An unexpected error occurred: {str(e)}' if settings.DEBUG else 'An unexpected error occurred. Please try again.'
        }, status=500)
