from datetime import datetime, UTC
from fastapi import FastAPI, Depends, HTTPException, Response
from database import engine, sessionLocal
import database_model as db_mdl
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

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

@app.patch("/cart/{prod_id}", status_code=201)
async def add_to_cart(prod_id: int, quantity: int, user_id: int, db: Session = Depends(get_db)):
    try:
        if quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

        if product is None:
            raise HTTPException(status_code=404,detail="Product not found")    
        
        item = db.query(db_mdl.CartItem).filter(db_mdl.CartItem.prod_id == prod_id, db_mdl.CartItem.user_id == user_id).all()

        if item is None:
            new_item = db_mdl.CartItem(prod_id = prod_id, quantity = quantity, user_id = user_id)

            db.add(new_item)
            db.commit()
            db.refresh(new_item)

            return new_item
        
        item.quantity += quantity

        db.commit()
        db.refresh(item)

        return item
    
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

    return cart

@app.post("/order", status_code=201)
async def buy(prod_id: int, quantity: int, user_id: int, address_id: int, db: Session = Depends(get_db)):

    if quantity <= 0:
        raise HTTPException(status_code=400,detail="Quantity must be greater than 0")
    
    try:
        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).with_for_update().first()

        address = (db.query(db_mdl.address).filter(db_mdl.address.address_id == address_id,db_mdl.address.user_id == user_id).first())

        user = db.query(db_mdl.user).filter(
        db_mdl.user.user_id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if address is None:
            raise HTTPException(status_code=404, detail="Address not found.")

        if product is None:
            raise HTTPException(status_code=404,detail="Product not found")

        if quantity > product.stock:
            raise HTTPException(status_code=409, detail="Requested quantity exceeds available stock :( ")

        new_order = db_mdl.order(user_id = user_id, total_price = product.Current_price * quantity,
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
            user_id=user_id,
            prod_id=prod_id,
            quantity=quantity,
            price=product.Current_price
        )

        db.add(new_item)

        product.stock -= quantity

        db.commit()

        db.refresh(new_order)
        db.refresh(new_item)

        return {
        "message": "Order placed successfully",
        "order_id": new_order.order_id, "total_price": new_order.total_price
    }
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
async def order_list(user_id: int,db: Session = Depends(get_db)):
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

@app.post("/addresses", status_code=201)
def create_address(
    user_id: int,
    name: str,
    phone: str,
    city: str,
    state: str,
    pincode: str,
    address_line1: str,
    address_line2: str | None = None,
    is_default: bool = False,        #default parameters are placed at the end, after the non-default parameters
    db: Session = Depends(get_db)
):

    user = db.query(db_mdl.user).filter(
        db_mdl.user.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if is_default:
        db.query(db_mdl.address).filter(
            db_mdl.address.user_id == user_id,
            db_mdl.address.is_default == True
        ).update({"is_default": False})

    new_address = db_mdl.address(
        user_id=user_id,
        name=name,
        phone=phone,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        pincode=pincode,
        is_default=is_default
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address

@app.patch("/addresses/{address_id}")
def update_address(
    address_id: int,
    user_id: int,
    name: str | None = None,
    phone: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    landmark: str | None = None,
    city: str | None = None,
    state: str | None = None,
    pincode: str | None = None,
    is_default: bool | None = None,
    db: Session = Depends(get_db)
):

    address = db.query(db_mdl.address).filter(
        db_mdl.address.address_id == address_id,
        db_mdl.address.user_id == user_id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    if name is not None:
        address.name = name

    if phone is not None:
        address.phone = phone

    if address_line1 is not None:
        address.address_line1 = address_line1

    if address_line2 is not None:
        address.address_line2 = address_line2

    if landmark is not None:
        address.landmark = landmark

    if city is not None:
        address.city = city

    if state is not None:
        address.state = state

    if pincode is not None:
        address.pincode = pincode

    if is_default is not None:

        if is_default:
            db.query(db_mdl.address).filter(
                db_mdl.address.user_id == user_id,
                db_mdl.address.address_id != address_id
            ).update({"is_default": False})

        address.is_default = is_default

    db.commit()
    db.refresh(address)

    return address

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

