from fastapi import FastAPI, Depends, HTTPException
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

@app.post("/admin/products", status_code=200)
def create_prod(prod_id: int, quantity: int, seller_id: int, price: int ,prod_name: str , db: Session = Depends(get_db)):
    try:
        if quantity <= 0:
                raise HTTPException(status_code=400,detail="Quantity must be greater than 0")

        prod = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

        seller = prod = db.query(db_mdl.product).filter(db_mdl.product.seller_id == seller_id).first()

        if prod is not None:
            raise HTTPException(status_code=400, detail="Product id already exists")

        if seller is None:
                    raise HTTPException(status_code=404, detail="Seller not Found")

        new_prod = db_mdl.product(prod_id = prod_id, stock = quantity, prod_name = prod_name, seller_id = seller_id, current_price = price)

        db.add(new_prod)
        db.commit()
        db.refresh(new_prod)

        return {"message": "Product created", "product_id":new_prod.prod_id}       

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )
          
    

# @app.get("/admin/products")
# def products():

# @app.get("/admin/products/{prod_id}")
# def get_product(prod_id: int):

# @app.patch("/admin/products/{prod_id}")
# def update_product(prod_id: int):

# @app.delete("/admin/products/{prod_id}")
# def delete_product(prod_id: int):

# @app.get("/admin/orders")
# def view_orders():

# @app.get("/admin/orders/{order_id}")
# def get_order(order_id: int):

# @app.patch("/admin/orders/{order_id}")
# def update_order(order_id: int):

# @app.patch("/admin/products/{prod_id}/stock")
# def inventory(prod_id: int):

# @app.get("/admin/users")
# def users_list():

# @app.get("/admin/users/{user_id}")
# def get_user(user_id: int):

# @app.patch("/admin/users/{user_id}")
# def block_user(user_id: int):

# @app.get("/admin/dashboard")
# def analytics():