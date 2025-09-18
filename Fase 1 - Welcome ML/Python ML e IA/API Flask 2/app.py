from flask import Flask, jsonify, request
from config import Config
from flasgger import Swagger

from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)


app = Flask(__name__)

app.config.from_object(Config)

app.config['SWAGGER'] = {
    'title': 'My flask API',
    'uiversion': 3,
    'specs_route': '/docs/',
}

# Adicione isto para verificar o caminho absoluto
current_dir = Path(__file__).parent
swagger_file = current_dir / 'swagger_2.yml'
print(f"Tentando carregar: {swagger_file}") 

swagger = Swagger(app, template_file=str(swagger_file))

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    time_minutes = db.Column(db.Integer, nullable=False)

print(app.config['SECRET_KEY'])

# CREATE USER
@app.route('/register', methods=['POST'])
def create_user():
    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 400
    
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": f"User '{new_user} created!'"}), 201


# CREATE LOGIN 
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and user.password == data['password']:
        # Converter o ID para String
        token = create_access_token(identity=str(user.id))
        
        return jsonify({"acess_token": token}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401


# PROTECTED
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity() # Retorna o 'identity' usado na criação do token
    
    return jsonify({"msg": f"Usuário com ID {current_user_id} acessou a rota protegida!"}), 200


# CREATE RECIPES
@app.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    data = request.get_json()

    # Verificação básica dos campos (opcional, mas recomendado)
    if not all(key in data for key in ['title', 'ingredients', 'time_minutes']):
        return jsonify({"error": "Missing required fields"}), 400

    new_recipe = Recipe(
        title = data['title'],
        ingredients = data['ingredients'],
        time_minutes = data['time_minutes']
    )

    db.session.add(new_recipe)
    db.session.commit()

    return jsonify({"msg": "Recipe created"}), 201


# GET RECIPES
@app.route('/recipes', methods=['GET'])
@jwt_required()
def get_recipe():
    """
    Endpoint para buscar receitas com filtros opcionais
    
    Parâmetros de Consulta (Query Parameters):
        ingredient (str): Opcional - filtra receitas que contenham este ingrediente
        max_time (int): Opcional - filtra receitas com tempo de preparo <= este valor
    
    Retorna:
        Um array JSON de objetos de receita que correspondem aos critérios
    """
    
    # Obtém os parâmetros de consulta da URL
    # request.args.get() captura os parâmetros depois do '?' na URL
    # Ex: /recipes?ingredient=chocolate&max_time=30
    ingredient = request.args.get('ingredient')  # Obtém o parâmetro 'ingredient'
    max_time = request.args.get('max_time', type=int)  # Obtém 'max_time' convertendo para inteiro
    
    # Inicia a consulta base - SELECT * FROM recipe
    query = Recipe.query
    
    # Adiciona filtro por ingrediente se foi fornecido
    if ingredient:
        # ilike faz busca case-insensitive (não diferencia maiúsculas/minúsculas)
        # % são curingas - busca o texto em qualquer posição dos ingredientes
        query = query.filter(Recipe.ingredients.ilike(f"%{ingredient}%"))
    
    # Adiciona filtro por tempo máximo se foi fornecido
    if max_time is not None:
        # Filtra receitas com tempo menor ou igual ao especificado
        query = query.filter(Recipe.time_minutes <= max_time)
    
    # Executa a consulta e obtém todos os resultados
    recipes = query.all()  # Retorna uma lista de objetos Recipe
    
    # Converte os resultados para uma lista de dicionários
    recipes_list = [
        {
            "id": r.id,                   # ID da receita
            "title": r.title,             # Título da receita
            "ingredients": r.ingredients, # Ingredientes
            "time_minutes": r.time_minutes # Tempo de preparo
        }
        for r in recipes  # Para cada receita na lista de resultados
    ]
    
    # Converte a lista de dicionários para JSON e retorna
    return jsonify(recipes_list)


# GET RECIPE BYID
@app.route('/recipes/<int:recipe_id>', methods=['GET'])
@jwt_required()
def get_recipe_by_id(recipe_id):
    """
    Obtém uma receita específica pelo seu ID
    
    Parâmetros:
        recipe_id (int): ID da receita a ser buscada
    
    Retorna:
        JSON com os dados da receita ou 404 se não encontrada
    """
    # Busca a receita pelo ID ou retorna 404 se não existir
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Retorna os dados da receita em formato JSON
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'ingredients': recipe.ingredients,
        'time_minutes': recipe.time_minutes
    })



# UPDATE RECIPES
@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
@jwt_required()
def update_recipe(recipe_id):
    """
    Atualiza uma receita existente
    
    Args:
        recipe_id (int): ID da receita a ser atualizada
    
    Requer:
        - Autenticação via JWT
        - Corpo da requisição em JSON com pelo menos um dos campos atualizáveis
    
    Campos atualizáveis:
        - title (string): Novo título da receita
        - ingredients (string): Novos ingredientes
        - time_minutes (int): Novo tempo de preparo
    
    Retorna:
        - Mensagem de sucesso (200) se a atualização for bem-sucedida
        - Erro 404 se a receita não for encontrada
        - Erro 401 se não estiver autenticado
    """
    
    # Obtém os dados JSON do corpo da requisição
    data = request.get_json()
    
    # Busca a receita no banco de dados ou retorna 404 se não existir
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Atualiza apenas os campos que foram enviados na requisição
    if 'title' in data:
        recipe.title = data['title']
    if 'ingredients' in data:
        recipe.ingredients = data['ingredients']
    if 'time_minutes' in data:
        recipe.time_minutes = data['time_minutes']
    
    # Salva as alterações no banco de dados
    db.session.commit()
    
    # Retorna mensagem de sucesso
    return jsonify({"msg": "Recipe Updated"}), 200



# DELETE RECIPES
@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@jwt_required()
def delete_recipe(recipe_id):
    """
    Remove uma receita do banco de dados
    
    Args:
        recipe_id (int): ID da receita a ser removida
    
    Requer:
        - Autenticação via JWT
    
    Fluxo:
        1. Busca a receita pelo ID
        2. Se não existir, retorna 404
        3. Remove a receita do banco de dados
        4. Confirma a transação
    
    Retorna:
        - Mensagem de sucesso (200) se a remoção for bem-sucedida
        - Erro 404 se a receita não for encontrada
        - Erro 401 se não estiver autenticado
    """
    
    # Busca a receita ou retorna 404 se não existir
    recipe = Recipe.query.get_or_404(recipe_id)
    
    try:
        # Remove a receita do banco de dados
        db.session.delete(recipe)
        
        # Confirma a transação
        db.session.commit()
        
        return jsonify({"msg": "Recipe deleted successfully"}), 200
    
    except Exception as e:
        # Em caso de erro, faz rollback e retorna erro 500
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500


    



# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#         print("Banco de dados criado!")

if __name__ == '__main__':
    app.run(debug=True)  # Ativa modo debug