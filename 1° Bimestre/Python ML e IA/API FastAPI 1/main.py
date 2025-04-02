from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from models import *

app = FastAPI(
    title="My FastAPI API",
    version="1.0.0",
    description="API de Exemplo com FastAPI"
)

users = {
    "user1": "teste1",
    "user2": "teste2"
}

security = HTTPBasic()

# Função para verificar as credenciais de acesso (usuário e senha)
def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    # Extrai o nome de usuário das credenciais fornecidas
    username = credentials.username
    # Extrai a senha das credenciais fornecidas
    password = credentials.password

    # Verifica se o usuário existe no dicionário de usuários e se a senha está correta
    if username in users and users[username] == password:
        # Se as credenciais estiverem corretas, retorna o nome de usuário
        return username
    
    # Se as credenciais estiverem incorretas, levanta uma exceção HTTP 401 (Não Autorizado)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Basic"}
    )

@app.get("/")
async def home():
    return "Hello, FastAPI!"

@app.get("/hello")
async def hello(username: str = Depends(verify_password)):
    return {"message": f"Hello, {username}!"}

@app.get("/items")
async def get_items():
    return items

@app.post("/items", status_code=201)
async def create_item(item: Item):
    items.append(item.dict())
    return item

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):

    if 0 <= item_id < len(items):
        items[item_id].update(item.dict())
        return  items[item_id]
    
    raise HTTPException(status_code=404, detail="Item não encontrado.")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if 0 <= item_id < len(items):
        removed_item = items.pop(item_id)

        return  removed_item
    
    raise HTTPException(status_code=404, detail="Item não encontrado.")