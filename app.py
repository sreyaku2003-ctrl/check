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
        
        if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
            return jsonify({'error': 'Please add your Groq API key'}), 400
        
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Create chat completion with JSON mode
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a grammar and spelling checker. Analyze the text and return corrections in JSON format.

Check for:
- Verb tense errors (goes→went, has→had)
- Subject-verb agreement (I has→have, they was→were)  
- Spelling mistakes
- Wrong verb forms
- Punctuation errors
- Article errors (a→an, the)

Return a JSON object with this structure:
{
  "corrections": [
    {
      "wrong": "the incorrect word or phrase",
      "correct": "the corrected version",
      "reason": "explanation of the error"
    }
  ]
}

If no errors are found, return: {"corrections": []}"""
                },
                {
                    "role": "user",
                    "content": f"Check this text for grammar and spelling errors:\n\n{text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}  # Forces valid JSON
        )
        
        # Extract response
        content = chat_completion.choices[0].message.content.strip()
        print(f"\n{'='*60}")
        print(f"API Response:\n{content}")
        print(f"{'='*60}")
        
        # Parse JSON response
        try:
            response_data = json.loads(content)
            corrections_raw = response_data.get('corrections', [])
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw content: {content}")
            return jsonify({'corrections': []})
        
        print(f"Parsed corrections: {corrections_raw}")
        
        # Validate that we got a list
        if not isinstance(corrections_raw, list):
            print("Corrections is not a list")
            return jsonify({'corrections': []})
        
        # Convert to position-based format
        corrections = []
        text_lower = text.lower()
        
        for corr in corrections_raw:
            if not isinstance(corr, dict):
                continue
                
            wrong = corr.get('wrong', '').strip()
            correct = corr.get('correct', '').strip()
            reason = corr.get('reason', 'grammar error')
            
            if not wrong or not correct:
                continue
            
            # Find position of wrong word/phrase in text (case-insensitive)
            wrong_lower = wrong.lower()
            pos = text_lower.find(wrong_lower)
            
            if pos == -1:
                print(f"⚠️  Could not find '{wrong}' in text")
                # Try finding individual words
                words = wrong.split()
                if len(words) > 0:
                    pos = text_lower.find(words[0].lower())
                    if pos != -1:
                        wrong = words[0]
                        print(f"   Found first word '{wrong}' at position {pos}")
                    else:
                        continue
                else:
                    continue
            
            corrections.append({
                'original': text[pos:pos+len(wrong)],  # Preserve original case
                'correction': correct,
                'start': pos,
                'end': pos + len(wrong),
                'type': 'grammar',
                'reason': reason
            })
        
        print(f"\n✅ Final corrections ({len(corrections)}):")
        for i, c in enumerate(corrections, 1):
            print(f"  {i}. '{c['original']}' → '{c['correction']}' ({c['reason']})")
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
