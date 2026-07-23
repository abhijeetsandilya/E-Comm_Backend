from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from database import Base

class user(Base):
    __tablename__ = "User_details"

    user_id = Column(Integer, primary_key= True)
    user_mail = Column(String)
    username = Column(String)
    user_number = Column(String(10))
    is_blocked = Column(Boolean, default=False)

class seller(Base):
    __tablename__ = "Seller_details"

    seller_id = Column(Integer, primary_key=True)
    seller_name = Column(String)
    seller_mail = Column(String, nullable=False, unique=True)
    seller_number = Column(String(10))
    is_blocked = Column(Boolean, default=False)

class product(Base):
    __tablename__= "Product"

    prod_id = Column(Integer, primary_key= True)
    stock = Column(Integer, nullable=False)
    prod_name = Column(String)
    seller_id = Column(Integer, ForeignKey("Seller_details.seller_id"))
    Current_price =  Column(Float, nullable=False)
    
class cart(Base):
    __tablename__ = "Cart"

    cart_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("User_details.user_id"))
    created_at = Column(DateTime)

class CartItem(Base):
    __tablename__ = "Cart_items"

    cart_item_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("User_details.user_id"))
    prod_id = Column(Integer, ForeignKey("Product.prod_id"))
    cart_id = Column(Integer, ForeignKey("Cart.cart_id"))
    quantity = Column(Integer)

class order(Base):
    __tablename__ = "Orders"

    order_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("User_details.user_id"))
    order_status = Column(String)
    total_price = Column(Float)
    ordered_at = Column(DateTime)

class orderItem(Base):
    __tablename__ = "Ordered_item"

    order_item_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("User_details.user_id"))
    order_id = Column(Integer, ForeignKey("Orders.order_id"))
    prod_id = Column(Integer, ForeignKey("Product.prod_id"))
    quantity = Column(Integer)
    price = Column(Integer)

class orderAddress(Base):
    __tablename__ = "Order_address"

    order_id = Column(Integer, ForeignKey("Orders.order_id"), primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String(10), nullable=False)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String(6), nullable=False)

class address(Base):
    __tablename__ = "Address"

    address_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User_details.user_id"))
    name = Column(String, nullable=False)
    phone = Column(String(10), nullable=False)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String(6), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)