import datetime

from fastapi import FastAPI, Depends, HTTPException, Response
from database import engine, sessionLocal
import database_model as db_mdl
from sqlalchemy.orm import Session

db_mdl.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = sessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(db: Session = Depends(get_db)):

    products = db.query(db_mdl.product).all()
    return products


@app.get("/view/{prod_id}")
async def product(prod_id: int, db: Session = Depends(get_db)):

    product_req = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

    return product_req

@app.patch("/cart/{prod_id}")
async def add_to_cart(prod_id: int, quantity: int, user_id: int, db: Session = Depends(get_db)):

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

    if product is None:
        raise HTTPException(status_code=404,detail="Product not found")    
    
    item = db.query(db_mdl.CartItem).filter(db_mdl.CartItem.prod_id == prod_id, db_mdl.CartItem.user_id == user_id).first()

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

@app.delete("/cart/{prod_id}")
async def remove_from_cart(prod_id: int, db: Session = Depends(get_db)):

    product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

    if product is None:
        raise HTTPException(status_code=404,detail="Product not found")
    
    item = db.query(db_mdl.CartItem).filter(db_mdl.CartItem.prod_id == prod_id).first()

    if item is None:
        raise HTTPException(status_code=404,detail="Item not found in the cart")
    
    db.delete(item)
    db.commit()

    return Response(status_code=204)

@app.get("/cart")
async def view_cart(db: Session = Depends(get_db)):
    cart = db.query(db_mdl.cart).all()

    return cart

@app.post("/order", status_code=201)
async def buy(prod_id: int, quantity: int, user_id: int, db: Session = Depends(get_db)):

    if quantity <= 0:
        raise HTTPException(status_code=400,detail="Quantity must be greater than 0")
    
    product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).with_for_update().first()

    if product is None:
        raise HTTPException(status_code=404,detail="Product not found")

    if quantity > product.stock:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available stock :( ")

    new_order = db_mdl.order(prod_id = prod_id, quantity = quantity,
                              user_id = user_id, total_price = product.Current_price * quantity,
                              order_status="Placed",ordered_at=datetime.utcnow())
    
    db.add(new_order)

    db.flush()

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
    "order_id": new_order.order_id
}

# @app.get("/order")
# async def order_list():
    


# @app.patch("/order/{order_id}")
# async def cancel_order(order_id: int):
