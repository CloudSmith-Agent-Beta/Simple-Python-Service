from pydantic import BaseModel

class Item(BaseModel):
    user_id: str
    value: str
