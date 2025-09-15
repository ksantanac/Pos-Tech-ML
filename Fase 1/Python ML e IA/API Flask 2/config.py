# Config
class Config:
    SECRET_KEY = "teste"
    CACHE_TYPE = "simple"
    SWAGGER = {
        'title': 'Catálogo de Receitas Gourmet',
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

    SQLALCHEMY_DATABASE_URI = 'sqlite:///recipes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "teste"