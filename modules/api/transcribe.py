"""
Voice Transcription API - Groq Integration
DOES: Transcribes audio to text & extracts customer name/phone
INPUTS: Audio blob (webm format)
OUTPUTS: JSON with extracted name and phone
"""
import os
import requests
from flask import jsonify, request
from .blueprint import api_bp

# Groq API Configuration - Key from environment variable
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_TRANSCRIBE_URL = 'https://api.groq.com/openai/v1/audio/transcriptions'
GROQ_CHAT_URL = 'https://api.groq.com/openai/v1/chat/completions'


@api_bp.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Voice-to-form transcription endpoint
    - Step 1: Transcribe audio using Groq Whisper
    - Step 2: Extract name & phone using LLM
    """
    # Check if audio file was uploaded
    if 'audio' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No audio file provided'
        }), 400
    
    audio_file = request.files['audio']
    if not audio_file:
        return jsonify({
            'status': 'error',
            'message': 'Empty audio file'
        }), 400
    
    try:
        # Step 1: Transcribe audio with Groq Whisper
        transcribe_response = requests.post(
            GROQ_TRANSCRIBE_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}'
            },
            files={
                'file': (audio_file.filename or 'audio.webm', audio_file.stream, 'audio/webm')
            },
            data={
                'model': 'whisper-large-v3-turbo',
                'language': 'vi',  # Vietnamese
                'response_format': 'json'
            }
        )
        
        if transcribe_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'Transcription failed: {transcribe_response.text}'
            }), 500
        
        transcription = transcribe_response.json().get('text', '')
        
        if not transcription.strip():
            return jsonify({
                'status': 'error',
                'message': 'No speech detected'
            }), 400
        
        # Step 2: Extract name, phone, and service using LLM
        extraction_prompt = f"""Analyze the following Vietnamese transcription and extract:
1. Customer name (tên khách hàng)
2. Phone number (số điện thoại)
3. Service interest (dịch vụ quan tâm) - what service/treatment they want

Transcription: "{transcription}"

Important rules:
- Convert spoken numbers to digits (e.g., "không chín" → "09", "một hai ba" → "123")
- Remove all spaces and dashes from phone numbers
- Vietnamese phone numbers typically start with 0 and have 10-11 digits
- For service, look for keywords like: muốn làm, quan tâm, cần, dịch vụ, etc.
- Common services: nâng mũi, cắt mí, tiêm filler, botox, trẻ hóa da, nha khoa, niềng răng, etc.
- If any field is not detected, return empty string

Respond ONLY with valid JSON in this exact format:
{{"name": "extracted name or empty string", "phone": "extracted phone or empty string", "service": "extracted service or empty string"}}"""

        chat_response = requests.post(
            GROQ_CHAT_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {'role': 'user', 'content': extraction_prompt}
                ],
                'temperature': 0.1,
                'max_tokens': 300
            }
        )
        
        if chat_response.status_code != 200:
            # If LLM fails, return just the transcription
            return jsonify({
                'status': 'partial',
                'transcription': transcription,
                'name': '',
                'phone': '',
                'service': '',
                'message': 'Transcription successful but extraction failed'
            })
        
        # Parse LLM response
        llm_text = chat_response.json()['choices'][0]['message']['content']
        
        # Try to extract JSON from response
        import json
        import re
        
        # Find JSON in response (handle potential markdown wrapping)
        json_match = re.search(r'\{[^}]+\}', llm_text)
        if json_match:
            extracted = json.loads(json_match.group())
            name = extracted.get('name', '').strip()
            phone = extracted.get('phone', '').strip()
            service = extracted.get('service', '').strip()
            
            # Clean phone number - remove any non-digits
            phone = re.sub(r'[^\d]', '', phone)
            
            return jsonify({
                'status': 'success',
                'transcription': transcription,
                'name': name,
                'phone': phone,
                'service': service
            })
        else:
            # JSON parsing failed, return transcription only
            return jsonify({
                'status': 'partial',
                'transcription': transcription,
                'name': '',
                'phone': '',
                'service': '',
                'message': 'Could not parse extracted data'
            })
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'API request failed: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500
