from flask import Flask, request, jsonify
from flask_cors import CORS
import autogen
import json
import numpy as np
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
import requests
import PyPDF2
from io import BytesIO

from dotenv import load_dotenv
load_dotenv()

# Remove the duplicate Flask and CORS initialization
app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:3000"],
    "methods": ["GET", "POST", "OPTIONS"],  # Added OPTIONS
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

# Configure AutoGen
config_list = [
    {
        'model': 'gpt-4o-mini',
        'api_key': os.getenv('OPENAI_API_KEY')
    }
]

# Add a new translation agent
def create_translation_agent(target_language):
    return autogen.ConversableAgent(
        name="translation_agent",
        system_message=f"""
        You are an expert translator. Translate the given JSON content into {target_language}.
        Maintain the exact same JSON structure but translate all text values.
        Do not translate:
        - URLs
        - Technical terms
        - Citation numbers
        - JSON keys
        Keep all formatting and structure intact.
        """,
        llm_config={"config_list": config_list, "timeout": 60}
    )

# Add a translation function
def translate_content(content, target_language):
    if target_language.lower() == 'en':  # Skip translation if target is English
        return content
        
    translation_agent = create_translation_agent(target_language)
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config={"use_docker": False}
    )

    chat_results = user_proxy.initiate_chats(
        [
            {
                "recipient": translation_agent,
                "message": f"Translate this content: {json.dumps(content)}",
                "max_turns": 1
            }
        ]
    )
    
    return json.loads(chat_results[-1].summary)

@app.route('/test-api-key', methods=['GET'])
def test_api_key():
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return jsonify({'message': f'API key found: {api_key[:6]}...'})
    return jsonify({'error': 'No API key found'}), 403

@app.route('/analyze-paper', methods=['POST'])
def analyze_paper():
    data = request.get_json()
    language = data.get('language', 'en')
    print(f"Received request with data: {data}")  # Debug log
    print(f"Language from request: {language}")   # Debug log
    
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400
    
    pdf_url = data['url']
    
    try:
        # Download and extract PDF text
        # Download PDF
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download PDF'}), 400
        
        # Read PDF content
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n"
        
        collection_agent = autogen.ConversableAgent(
            name="collection_agent",
            system_message="""
            You are an expert at analyzing research papers. You will be given the complete text of a research paper.
            Organize the text as it is in the paper into sections. Look for obvious headers like "Introduction", "Methods", "Results", "Discussion", etc.
            Keep in all the original text, paragraph breaks, and citations.
            Ignore and filter out any images or tables or non-text content. 
            Clean up the text to remove any unnecessary whitespace or formatting eg. 'total- ly' should be 'totally' and 'gh ost' should be 'ghost'
            Return ONLY the section titles and original, cleaned up text in this format:
            {
                "sections": [
                    {
                        "title": "section title",
                        "originalText": "complete text from paper"
                    }
                ]
            }
            """,
            llm_config={"config_list": config_list, "timeout": 60}
        )

        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config={"use_docker": False}
        )

        chat_results = user_proxy.initiate_chats(
            [
                {
                    "recipient": collection_agent,
                    "message": full_text,
                    "max_turns": 1
                }
            ]
        )
        
        return jsonify(json.loads(chat_results[-1].summary))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-overall-summary', methods=['POST'])
def get_overall_summary():
    data = request.get_json()
    language = data.get('language', 'en')
    print(f"Overall summary request - Language: {language}")  # Debug log
    
    if not data or 'fullText' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        summary_agent = autogen.ConversableAgent(
            name="summary_agent",
            system_message="""
            Create a condensed, effective summary of the entire section.
            Return your response in this format:
            {
                "overallSummary": "condensed, effective summary of the paper",
                "mainFindings": ["key finding 1", "key finding 2", "key finding 3"]
            }
            """,
            llm_config={"config_list": config_list, "timeout": 60}
        )
        
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config={"use_docker": False}
        )

        chat_results = user_proxy.initiate_chats(
            [
                {
                    "recipient": summary_agent,
                    "message": f"Create a summary of this paper: {data['fullText']}",
                    "max_turns": 1
                }
            ]
        )
        
        # Get the initial summary in English
        summary_result = json.loads(chat_results[-1].summary)
        
        # Translate if needed
        translated_result = translate_content(summary_result, language)
        return jsonify(translated_result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-section', methods=['POST'])
def analyze_section():
    data = request.get_json()
    language = data.get('language', 'en')
    print(f"Section analysis request - Language: {language}")  # Debug log
    
    if not data or 'sectionText' not in data or 'analysisType' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    try:
        # Get initial analysis in English
        result = None
        
        if data['analysisType'] == 'summary':
            agent = autogen.ConversableAgent(
                name="section_summary_agent",
                system_message="""
                Create a detailed summary of this section.
                Return your response in this format:
                {
                    "sectionSummary": "detailed summary of the section",
                    "keyFindings": ["finding 1", "finding 2"]
                }
                """,
                llm_config={"config_list": config_list, "timeout": 60}
            )
        elif data['analysisType'] == 'references':
            agent = autogen.ConversableAgent(
                name="section_reference_agent",
                system_message="""
                Suggest related topics and references for this section.
                Return your response in this format:
                {
                    "relatedTopics": [
                        {
                            "title": "topic",
                            "description": "description",
                            "url": "url"
                        }
                    ],
                    "references": [
                        {
                            "citation": "citation number",
                            "title": "reference title",
                            "url": "url"
                        }
                    ]
                }
                """,
                llm_config={"config_list": config_list, "timeout": 60}
            )
        
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config={"use_docker": False}
        )

        chat_results = user_proxy.initiate_chats(
            [
                {
                    "recipient": agent,
                    "message": f"Analyze this section: {data['sectionText']}",
                    "max_turns": 1
                }
            ]
        )
        
        # Get initial result in English
        initial_result = json.loads(chat_results[-1].summary)
        
        # Translate if needed
        translated_result = translate_content(initial_result, language)
        return jsonify(translated_result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Explicitly set host and port
    app.run(host='0.0.0.0', port=5001, debug=True)