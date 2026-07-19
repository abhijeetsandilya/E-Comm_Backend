from fastapi import FastAPI, Depends
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


# @app.get("/view/{prod_id}")
# async def product(prod_id: int):

# @app.patch("/cart/{prod_id}")
# async def add_to_cart(prod_id: int, quantity: int):

# @app.delete("/cart/{prod_id}")
# async def remove_from_cart(prod_id: int):

# @app.get("/cart")
# async def view_cart():

# @app.post("/order")
# async def buy(prod_id: int, quantity: int):

# @app.patch("/order/{order_id}")
# async def cancel(order_id: int):
