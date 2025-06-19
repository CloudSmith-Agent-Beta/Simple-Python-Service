from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Payment(BaseModel):
    customer_id: str
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
class Customer(BaseModel):
    customer_id: str
    name: str
    email: Optional[str] = None
    account_status: Optional[str] = "active"
