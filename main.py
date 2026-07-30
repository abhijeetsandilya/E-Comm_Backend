from datetime import datetime, UTC
from fastapi import FastAPI, Depends, HTTPException, Response
from database import engine, sessionLocal
import database_model as db_mdl
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import model as mdl

db_mdl.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = sessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.get("/", status_code=200)
async def home(db: Session = Depends(get_db)):

    products = db.query(db_mdl.product).all()

    return products


@app.get("/view/{prod_id}", status_code=200)
async def product(prod_id: int, db: Session = Depends(get_db)):

    product_req = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

    if product_req is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product_req

@app.patch("/cart", status_code=201)
async def add_to_cart(item: mdl.CartAdd, db: Session = Depends(get_db)):
    try:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == item.prod_id).first()

        if product is None:
            raise HTTPException(status_code=404,detail="Product not found")    
        
        existing_item = db.query(db_mdl.CartItem).filter(db_mdl.CartItem.prod_id == item.prod_id, db_mdl.CartItem.user_id == item.user_id).first()

        if existing_item is None:
            new_item = db_mdl.CartItem(prod_id = item.prod_id, quantity = item.quantity, user_id = item.user_id)

            db.add(new_item)
            db.commit()
            db.refresh(new_item)

            return mdl.CartItemOut(message="Item added to cart", prod_id=new_item.prod_id, cart_id=new_item.cart_id)
        
        existing_item.quantity += item.quantity

        db.commit()
        db.refresh(existing_item)

        return mdl.CartItemOut(message="Item quantity updated", prod_id=existing_item.prod_id, cart_id=existing_item.cart_id)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

@app.delete("/cart/{prod_id}")
async def remove_from_cart(prod_id: int, user_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

        if product is None:
            raise HTTPException(status_code=404,detail="Product not found")
        
        item = db.query(db_mdl.CartItem).filter(db_mdl.CartItem.prod_id == prod_id, db_mdl.CartItem.user_id == user_id).first()

        if item is None:
            raise HTTPException(status_code=404,detail="Item not found in the cart")
        
        db.delete(item)
        db.commit()

        return Response(status_code=204)
    
    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

@app.get("/cart", status_code=200)
async def view_cart(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(db_mdl.cart).filter(db_mdl.cart.user_id == user_id).all()

    return mdl.CartResponse(message="Cart retrieved successfully", cart=cart)

@app.post("/order", status_code=201, response_model=mdl.OrderResponse)
async def buy(order: mdl.OrderCreate, db: Session = Depends(get_db)):

    if order.quantity <= 0:
        raise HTTPException(status_code=400,detail="Quantity must be greater than 0")
    
    try:
        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == order.prod_id).with_for_update().first()

        address = (db.query(db_mdl.address).filter(db_mdl.address.address_id == order.address_id,db_mdl.address.user_id == order.user_id).first())

        user = db.query(db_mdl.user).filter(
        db_mdl.user.user_id == order.user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if address is None:
            raise HTTPException(status_code=404, detail="Address not found.")

        if product is None:
            raise HTTPException(status_code=404,detail="Product not found")

        if order.quantity > product.stock:
            raise HTTPException(status_code=409, detail="Requested quantity exceeds available stock :( ")

        new_order = db_mdl.order(user_id = order.user_id, total_price = product.current_price * order.quantity,
                                order_status="Pending",ordered_at=datetime.now(UTC))
        
        db.add(new_order)
        db.flush()
        
        new_order_address = db_mdl.orderAddress(
        order_id=new_order.order_id,
        name=address.name,
        phone=address.phone,
        address_line1=address.address_line1,
        address_line2=address.address_line2,
        city=address.city,
        state=address.state,
        pincode=address.pincode)
        
        
        db.add(new_order_address)

        

        new_item = db_mdl.orderItem(
            order_id=new_order.order_id,
            user_id=order.user_id,
            prod_id=order.prod_id,
            quantity=order.quantity,
            price=product.current_price
        )

        db.add(new_item)

        product.stock -= order.quantity

        db.commit()

        db.refresh(new_order)
        db.refresh(new_item)

        return mdl.OrderResponse(message="Order placed successfully", order_id=new_order.order_id, total_price=new_order.total_price)
    
    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

@app.get("/order", status_code=200)
async def order_list(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(db_mdl.order).filter(db_mdl.order.user_id == user_id).all()
    
    return orders

@app.patch("/order/{order_id}", status_code=204)
async def cancel_order(order_id: int, user_id: int, db: Session = Depends(get_db)):

    try:
        order = (db.query(db_mdl.order).filter(db_mdl.order.order_id == order_id, db_mdl.order.user_id == user_id).first())

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.order_status == "Cancelled":
            raise HTTPException(
                status_code=409,
                detail="Order is already cancelled"
            )

        item = (db.query(db_mdl.orderItem).filter(db_mdl.orderItem.order_id == order_id, db_mdl.orderItem.user_id == user_id).first())

        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Order item not found"
            )

        product = (
            db.query(db_mdl.product)
            .filter(db_mdl.product.prod_id == item.prod_id)
            .first()
        )

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        product.stock += item.quantity

        order.order_status = "Cancelled"

        db.commit()

        return Response(status_code=204)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500,detail="Database error occurred")

@app.get("/address", status_code=200)
async def addresses(user_id : int, db: Session = Depends(get_db)):
  
    add = db.query(db_mdl.address).filter(db_mdl.address.user_id == user_id).all()

    if add is None:
        raise HTTPException(status_code=404, detail="Address not found")

    return add

@app.get("/address/{address_id}", status_code=200)
async def get_address(address_id : int, db: Session = Depends(get_db)):

    add = db.query(db_mdl.address).filter(db_mdl.address.address_id == address_id).first()

    if add is None:
        raise HTTPException(status_code=404, detail="Address not found")

    return add

@app.post("/addresses", status_code=201, response_model=mdl.AddressOut)
def create_address(
    address: mdl.AddressCreate,       
    db: Session = Depends(get_db)
):

    user = db.query(db_mdl.user).filter(
        db_mdl.user.user_id == address.user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if address.is_default:
        db.query(db_mdl.address).filter(
            db_mdl.address.user_id == address.user_id,
            db_mdl.address.is_default == True
        ).update({"is_default": False})

    new_address = db_mdl.address(
        user_id=address.user_id,
        name=address.name,
        phone=address.phone,
        address_line1=address.address_line1,
        address_line2=address.address_line2,
        city=address.city,
        state=address.state,
        pincode=address.pincode,
        is_default=address.is_default
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return mdl.AddressOut(message="Address created successfully", address_id=new_address.address_id)

@app.patch("/addresses/{address_id}")
def update_address(
    address_id: int,
    address_update: mdl.AddressUpdate,
    db: Session = Depends(get_db)
):

    address = db.query(db_mdl.address).filter(
        db_mdl.address.address_id == address_id,
        db_mdl.address.user_id == address_update.user_id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    if address_update.name is not None:
        address.name = address_update.name

    if address_update.phone is not None:
        address.phone = address_update.phone

    if address_update.address_line1 is not None:
        address.address_line1 = address_update.address_line1

    if address_update.address_line2 is not None:
        address.address_line2 = address_update.address_line2

    if address_update.landmark is not None:
        address.landmark = address_update.landmark

    if address_update.city is not None:
        address.city = address_update.city

    if address_update.state is not None:
        address.state = address_update.state

    if address_update.pincode is not None:
        address.pincode = address_update.pincode

    if address_update.is_default is not None:

        if address_update.is_default:
            db.query(db_mdl.address).filter(
                db_mdl.address.user_id == address_update.user_id,
                db_mdl.address.address_id != address_id
            ).update({"is_default": False})

        address.is_default = address_update.is_default

    db.commit()
    db.refresh(address)

    return mdl.AddressOut(message="Address updated successfully", address_id=address.address_id)

@app.delete("/addresses/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    address = db.query(db_mdl.address).filter(
        db_mdl.address.address_id == address_id,
        db_mdl.address.user_id == user_id
    ).first()

    if not address:
        raise HTTPException(404, "Address not found")

    was_default = address.is_default

    db.delete(address)
    db.commit()

    new_default = None

    if was_default:
        new_default = (
            db.query(db_mdl.address)
            .filter(db_mdl.address.user_id == user_id)
            .first()
        )

    if new_default:
        new_default.is_default = True
        db.commit()

