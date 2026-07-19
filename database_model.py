from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from database import Base

class user(Base):
    __tablename__ = "User_details"

    user_id = Column(Integer, primary_key= True)
    user_mail = Column(String)

class product(Base):
    __tablename__= "Product"

    prod_id = Column(Integer, primary_key= True)
    prod_name = Column(String)
    seller_id = Column(Integer)

class cart(Base):
    __tablename__ = "Cart"

    cart_id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey("User_details.user_id"))
    created_at = Column(DateTime)

class CartItem(Base):
    __tablename__ = "Cart_items"

    cart_item_id = Column(Integer, primary_key= True)
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
    order_id = Column(Integer, ForeignKey("Orders.order_id"))
    prod_id = Column(Integer, ForeignKey("Product.prod_id"))
    quantity = Column(Integer)
    price = Column(Integer)