from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    user_mail : str
    password : str

class UserLogin(BaseModel):
    username : str
    password : str
    user_mail : str
    user_id : int

class UserResponse(BaseModel):
    username : str
    user_mail : str

class AdminLogin(BaseModel):
    Admin_id : int
    Admin_password : str
    Admin_mail : str

class ProductCreate(BaseModel):
    prod_id : int
    quantity : int
    seller_id : int
    price : float
    prod_name : str

class ProductUpdate(BaseModel):
    prod_id: int
    prod_name: str = None
    price: float = None
    seller_id: int = None

class ProductResponse(BaseModel):
    prod_id : int
    stock : int
    prod_name : str 
    seller_id : int
    Current_price : float

class ProductOut(BaseModel):
    message : str
    prod_id : int

class CartAdd(BaseModel):
    prod_id : int
    quantity : int
    user_id : int  

class CartItemOut(BaseModel):
    message : str
    prod_id : int
    cart_id : int

class OrderCreate(BaseModel):
    prod_id: int
    quantity: int
    user_id: int
    address_id: int

class OrderResponse(BaseModel):
    message : str
    order_id : int
    total_price : float
    
class AddressCreate(BaseModel):
    ...

class AddressUpdate(BaseModel):
    ...

class AddressOut(BaseModel):
    ...