from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Get API key from environment variable (more secure for Render)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-grammar', methods=['POST'])
def check_grammar():
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if not GROQ_API_KEY:
            return jsonify({'error': 'Please add your Groq API key'}), 400
        
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Create chat completion - FORCE valid JSON output
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a grammar checker. Return valid JSON only.

Check for:
- Verb tense errors
- Subject-verb agreement  
- Spelling mistakes
- Wrong verb forms
- Punctuation errors

Return JSON object:
{
  "corrections": [
    {"wrong": "word", "correct": "fix", "reason": "why"}
  ]
}

CRITICAL: 
- Return ONLY valid JSON
- NO extra text or explanations
- NO || operators
- Use proper string escaping"""
                },
                {
                    "role": "user",
                    "content": f"Find errors in: {text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        # Extract response
        content = chat_completion.choices[0].message.content.strip()
        print(f"\nAPI Response: {content}")
        
        # Parse JSON (response_format guarantees valid JSON)
        try:
            response_data = json.loads(content)
            corrections_raw = response_data.get('corrections', [])
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            return jsonify({'corrections': []})
        
        print(f"Parsed corrections: {corrections_raw}")
        
        # Convert to position-based format
        corrections = []
        text_lower = text.lower()
        
        for corr in corrections_raw:
            wrong = corr.get('wrong', '').strip()
            correct = corr.get('correct', '').strip()
            
            if not wrong or not correct:
                continue
            
            # Find position of wrong word in text (case-insensitive search)
            pos = text_lower.find(wrong.lower())
            if pos == -1:
                print(f"Could not find '{wrong}' in text")
                continue
            
            corrections.append({
                'original': text[pos:pos+len(wrong)],  # Use actual case from text
                'correction': correct,
                'start': pos,
                'end': pos + len(wrong),
                'type': 'grammar'
            })
        
        print(f"Final corrections: {corrections}")
        return jsonify({'corrections': corrections})
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Grammar Checker Server Starting...")
    print("=" * 50)
    
    print("\n📍 Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.methods} {rule.rule}")
    print("=" * 50)
    
    if not GROQ_API_KEY:
        print("⚠️  WARNING: Please add your Groq API key")
    else:
        print("✅ API Key configured!")
    print("=" * 50)
    print("📝 Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
