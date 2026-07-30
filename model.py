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
    user_id: int
    name: str
    phone: str
    city: str
    state: str
    pincode: str
    address_line1: str
    address_line2: str | None = None
    is_default: bool = False

class AddressUpdate(BaseModel):
    address_id: int
    user_id: int
    name: str | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    landmark: str | None = None
    is_default: bool | None = False

class AddressOut(BaseModel):
    message: str
    address_id: int