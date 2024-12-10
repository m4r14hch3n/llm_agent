from flask import Flask, request, jsonify
from flask_cors import CORS
import autogen
import json
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
import requests
import PyPDF2
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Configure AutoGen
config_list = [
    {
        'model': 'gpt-4o-mini',
        'api_key': os.getenv('OPENAI_API_KEY')
    }
]

@app.route('/analyze-paper', methods=['POST'])
def analyze_paper():
    data = request.get_json()
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
        
        return jsonify(json.loads(chat_results[-1].summary))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-section', methods=['POST'])
def analyze_section():
    data = request.get_json()
    if not data or 'sectionText' not in data or 'analysisType' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    try:
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
                For the references, look through the text and find all citations in the text. Match the references to the citations in the text. Collect all such references and return them in the same format as the citations including the number of the citation in the references attribute. If there are no references, return an empty array.
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
        else:
            return jsonify({'error': 'Invalid analysis type'}), 400
        
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
        
        return jsonify(json.loads(chat_results[-1].summary))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
