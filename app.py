from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
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
        
        if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
            return jsonify({'error': 'Please add your Groq API key'}), 400
        
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Create chat completion with JSON mode
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a precise grammar and spelling checker. Only flag ACTUAL errors.

Check ONLY for these real errors:
1. Spelling mistakes (e.g., "recieve" → "receive")
2. Wrong verb tense (e.g., "She go yesterday" → "She went yesterday")
3. Subject-verb agreement (e.g., "He don't" → "He doesn't")
4. Wrong verb forms (e.g., "I have ate" → "I have eaten")
5. Missing articles where required (e.g., "I am student" → "I am a student")

DO NOT flag:
- Capitalization choices (unless it's clearly wrong)
- Style preferences
- Correctly spelled words
- Valid contractions

Return JSON format:
{
  "corrections": [
    {
      "wrong": "exact error text",
      "correct": "fixed version",
      "reason": "brief explanation"
    }
  ]
}

If no errors: {"corrections": []}"""
                },
                {
                    "role": "user",
                    "content": f"Check for grammar and spelling errors:\n\n{text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Extract and parse response
        content = chat_completion.choices[0].message.content.strip()
        print(f"\n{'='*60}")
        print(f"Input: {text}")
        print(f"API Response: {content}")
        
        response_data = json.loads(content)
        corrections_raw = response_data.get('corrections', [])
        
        print(f"Parsed: {corrections_raw}")
        
        # Convert to exact position-based format
        corrections = []
        
        for corr in corrections_raw:
            if not isinstance(corr, dict):
                continue
                
            wrong = corr.get('wrong', '').strip()
            correct = corr.get('correct', '').strip()
            reason = corr.get('reason', '')
            
            if not wrong or not correct:
                continue
            
            # Find exact position in original text (case-sensitive)
            pos = text.find(wrong)
            
            # If not found, try case-insensitive
            if pos == -1:
                text_lower = text.lower()
                wrong_lower = wrong.lower()
                pos = text_lower.find(wrong_lower)
                
                if pos != -1:
                    # Get the actual text from original
                    wrong = text[pos:pos+len(wrong)]
            
            if pos == -1:
                print(f"⚠️ Skipping: '{wrong}' not found in text")
                continue
            
            corrections.append({
                'original': wrong,
                'correction': correct,
                'start': pos,
                'end': pos + len(wrong),
                'type': 'grammar',
                'reason': reason
            })
        
        # Sort by position
        corrections.sort(key=lambda x: x['start'])
        
        # Remove reason field for cleaner output (optional)
        for c in corrections:
            del c['reason']
        
        print(f"Final output: {corrections}")
        print(f"{'='*60}\n")
        
        return jsonify({'corrections': corrections})
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Grammar Checker Server Starting...")
    print("=" * 60)
    
    print("\n📍 Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.methods} {rule.rule}")
    
    print("=" * 60)
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print("⚠️  WARNING: Please add your Groq API key")
    else:
        print("✅ API Key configured!")
    print("=" * 60)
    print("📝 Server: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
