from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

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
        
        client = Groq(api_key=GROQ_API_KEY)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a grammar checker. Find individual word errors ONLY.

IMPORTANT RULES:
1. Return ONLY individual words that are wrong, NOT phrases
2. Each error should be a SINGLE WORD
3. Do not include surrounding words

Examples:
Text: "the girls was sung"
Correct response:
{
  "corrections": [
    {"wrong": "was", "correct": "were", "reason": "subject-verb agreement"},
    {"wrong": "sung", "correct": "singing", "reason": "wrong verb form"}
  ]
}

WRONG response:
{"wrong": "the girls was sung", ...}  ❌ Too many words!

Text: "She go to store"
Correct response:
{
  "corrections": [
    {"wrong": "go", "correct": "went", "reason": "verb tense"}
  ]
}

Return format:
{
  "corrections": [
    {"wrong": "single_word", "correct": "fixed_word", "reason": "why"}
  ]
}

Only return individual wrong words, never phrases!"""
                },
                {
                    "role": "user",
                    "content": f"Find individual word errors in: {text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        content = chat_completion.choices[0].message.content.strip()
        print(f"\nInput: {text}")
        print(f"API Response: {content}")
        
        response_data = json.loads(content)
        corrections_raw = response_data.get('corrections', [])
        
        corrections = []
        
        for corr in corrections_raw:
            wrong = corr.get('wrong', '').strip()
            correct = corr.get('correct', '').strip()
            
            if not wrong or not correct:
                continue
            
            # Skip if wrong text has multiple words
            if ' ' in wrong.strip():
                print(f"⚠️ Skipping phrase: '{wrong}'")
                continue
            
            # Find position (case-insensitive)
            text_lower = text.lower()
            wrong_lower = wrong.lower()
            pos = text_lower.find(wrong_lower)
            
            if pos == -1:
                print(f"⚠️ Not found: '{wrong}'")
                continue
            
            # Get actual word from original text
            actual_word = text[pos:pos+len(wrong)]
            
            corrections.append({
                'original': actual_word,
                'correction': correct,
                'start': pos,
                'end': pos + len(wrong),
                'type': 'grammar'
            })
        
        corrections.sort(key=lambda x: x['start'])
        
        print(f"Output: {corrections}\n")
        
        return jsonify({'corrections': corrections})
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    print("="*60)
    print("🚀 Grammar Checker Started")
    print("="*60)
    
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print("⚠️  WARNING: Add your Groq API key")
    else:
        print("✅ API Key OK")
    
    print("📝 Server: http://127.0.0.1:5000")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
