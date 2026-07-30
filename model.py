from pydantic import BaseModel, ConfigDict
from datetime import datetime

# class UserCreate(BaseModel):
#     username: str
#     user_mail : str
#     password : str

# class UserLogin(BaseModel):
#     username : str
#     password : str
#     user_mail : str

# class UserResponse(BaseModel):
#     username : str
#     user_mail : str

#     model_config = ConfigDict(from_attributes=True)

# class AdminLogin(BaseModel):
#     Admin_id : int
#     Admin_password : str
#     Admin_mail : str

#     model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel): #done
    prod_id : int
    quantity : int
    seller_id : int
    price : float
    prod_name : str

class ProductUpdate(BaseModel): #done
    prod_name: str = None
    price: float = None
    seller_id: int = None

    model_config = ConfigDict(from_attributes=True)

class ProductResponse(BaseModel): #done
    prod_id : int
    stock : int
    prod_name : str 
    seller_id : int
    current_price : float

    model_config = ConfigDict(from_attributes=True)

class ProductOut(BaseModel): #done
    message : str
    prod_id : int

    model_config = ConfigDict(from_attributes=True)

class CartAdd(BaseModel): #done
    prod_id : int
    quantity : int
    user_id : int  

class CartItemOut(BaseModel): #done
    message : str
    prod_id : int
    cart_id : int

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel): #done
    prod_id: int
    quantity: int
    user_id: int
    address_id: int

class OrderResponse(BaseModel): #done
    message : str
    order_id : int
    total_price : float

    model_config = ConfigDict(from_attributes=True)
    
class AddressCreate(BaseModel): #done
    user_id: int
    name: str
    phone: str
    city: str
    state: str
    pincode: str
    address_line1: str
    address_line2: str | None = None
    is_default: bool = False

class AddressUpdate(BaseModel): #done
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

class AddressOut(BaseModel): #done
    message: str
    address_id: int

    model_config = ConfigDict(from_attributes=True)