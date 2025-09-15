from pydantic import BaseModel

items = []

class Item(BaseModel):
    name: str
    description: str = None
    price: float = None
    quantity: int = None