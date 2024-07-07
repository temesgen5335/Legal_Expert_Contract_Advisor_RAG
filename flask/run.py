import os, sys
from flask import Flask, render_template, jsonify, request
from rag_app import configure_retrieval_chain
from flask_cors import CORS

rpath = os.path.abspath('..')
if rpath not in sys.path:
    sys.path.insert(0, rpath)

from scripts.utils import MEMORY, load_data, load_qna_data

app = Flask(__name__)
CORS(app)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

@app.route('/api/chat', methods=['POST'])
def chat():
    print("inside chat api")
    data = request.form     
    user_question = data.get('user_question')
    uploaded_files = request.files.getlist('files')

    print("Received user question:", user_question)
    print("Received files:", uploaded_files)
    if not user_question:
        return jsonify({"error": "User question is required"}), 400


    CONV_CHAIN = configure_retrieval_chain(
        uploaded_files
    )
    
    response = CONV_CHAIN.run({
        "question": user_question,
        "chat_history": MEMORY.chat_memory.messages
    })
    print("Response:", response)
    return jsonify({"response": response})


@app.route('/api/messages', methods=['GET'])
def messages():
    messages = [] 

    for msg in MEMORY.chat_memory.messages:
        messages.append(msg)
    
    return jsonify({"messages": messages})

if __name__ == '__main__':
    app.run(debug=True)
