from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# ⚠️ IMPORTANT: Replace this with your actual Groq API key
GROQ_API_KEY = "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"
API_KEY = os.getenv('GROQ_API_KEY')

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
        
        if GROQ_API_KEY == "your_groq_api_key_here":
            return jsonify({'error': 'Please add your Groq API key in app.py file'}), 400
        
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Create chat completion - Ask for structured JSON output
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a strict grammar and spelling checker. Find ALL errors.

Check for:
1. Verb tense errors (goes→went, has→had, is→was)
2. Subject-verb agreement (I has→have, they was→were)
3. Spelling mistakes (forgetter→forgot, dont→don't)
4. Wrong verb forms
5. Punctuation errors
6. Article errors (a→an, the)

BE THOROUGH. Even if sentence seems okay, check carefully.

Return ONLY valid JSON array with proper escaping:
[
  {"wrong": "exact word", "correct": "fixed", "reason": "why"}
]

Examples:
Input: "She goes to store yesterday"
Output: [{"wrong": "goes", "correct": "went", "reason": "past tense needed"}]

Input: "I forgetter the keys"
Output: [{"wrong": "forgetter", "correct": "forgot", "reason": "wrong verb form"}]

Input: "They was happy"
Output: [{"wrong": "was", "correct": "were", "reason": "subject-verb agreement"}]

Return [] ONLY if genuinely perfect. Otherwise find the errors."""
                },
                
                {
                    "role": "user",
                    "content": f"Check this sentence carefully for ALL grammar and spelling errors:\n\n\"{text}\"\n\nFind every mistake."
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=2000,
        )
        
        # Extract response
        content = chat_completion.choices[0].message.content.strip()
        print(f"\nAPI Response: {content}")
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if not json_match:
            print("No JSON found in response")
            return jsonify({'corrections': []})
        
        # FIX: Better JSON parsing with error handling
        try:
            corrections_raw = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Attempted to parse: {json_match.group()}")
            
            # Try to fix common issues
            json_str = json_match.group()
            # Remove markdown code blocks if present
            json_str = re.sub(r'```json|```', '', json_str)
            # Fix unescaped quotes in strings
            json_str = json_str.replace("\\'", "'")
            
            try:
                corrections_raw = json.loads(json_str)
            except:
                print("Could not parse JSON even after cleaning")
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
    
    # ADD THESE LINES TO SEE ALL ROUTES:
    print("\n📍 Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.methods} {rule.rule}")
    print("=" * 50)
    
    if GROQ_API_KEY == "your_groq_api_key_here":
        print("⚠️  WARNING: Please add your Groq API key in app.py")
    else:
        print("✅ API Key configured!")
    print("=" * 50)
    print("📝 Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
