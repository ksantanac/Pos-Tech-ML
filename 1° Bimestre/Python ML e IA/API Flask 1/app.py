from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth

from flasgger import Swagger

from pathlib import Path

from utils import get_title

app = Flask(__name__)

app.config['SWAGGER'] = {
    'title': 'My flask API',
    'uiversion': 3,
    'specs_route': '/docs/',
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/apispec_1.json',
            'rule_filter': lambda rule: True,  # Todas as rotas
            'model_filter': lambda tag: True,  # Todos os modelos
        }
    ]
}

# Adicione isto para verificar o caminho absoluto
current_dir = Path(__file__).parent
swagger_file = current_dir / 'swager_config.yml'
print(f"Tentando carregar: {swagger_file}") 

swagger = Swagger(app, template_file=str(swagger_file))

auth = HTTPBasicAuth()

users = {
    "user1": "teste1",
    "user2": "teste2"
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route('/hello')
@auth.login_required
def home():
    return jsonify({"message": "Hello Word!"})

items = []

@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(items)


@app.route('/scrape/title', methods=['GET'])
@auth.login_required
def scrape_title():
    
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    return get_title(url)

@app.route('/items', methods=['POST'])
def createa_item():
    data = request.get_json()
    items.append(data)
    
    return jsonify(data), 201

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()

    if 0 <= item_id < len(items):
        items[item_id].update(data)
        return  jsonify(items[item_id])
    
    return jsonify({"error": "Item not found"}), 404


@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if 0 <= item_id < len(items):
        removed = items.pop(item_id)

        return  jsonify(removed)


if __name__ == '__main__':
    app.run(debug=True)