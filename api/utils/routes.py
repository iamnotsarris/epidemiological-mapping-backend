from flask import render_template, request, jsonify
import os
import google.generativeai as genai
from .utils.embedding_manager import EmbeddingManager

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-embedding-001')

embedding_manager = EmbeddingManager(os.getenv('GOOGLE_API_KEY'))


#@app.route('/')
#def home():
#    return render_template('index.html')


@app.route('/suporte', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')

        context = embedding_manager.search_query(user_message)

        prompt = f"""Com base apenas no seguinte contexto: 
        {context}

        Responda à pergunta: {user_message}

        Responda de forma concisa e direta, em português."""

        response = model.generate_content(prompt)

        return jsonify({
            'response': response.text,
            'status': 'success'
        })

    except Exception as e:
        print(f"Erro: {str(e)}")
        return jsonify({
            'response': 'Desculpe, ocorreu um erro ao processar sua mensagem.',
            'status': 'error'
        }), 500