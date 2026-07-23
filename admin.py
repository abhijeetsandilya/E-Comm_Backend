from fastapi import FastAPI, Depends, HTTPException
from database import engine, sessionLocal
import database_model as db_mdl
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

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
          
    

@app.get("/admin/products")
def products(db: Session = Depends(get_db)):
    products = db.query(db_mdl.product).all()

    return {
        "total_products": len(products),
        "products": products
    }

@app.get("/admin/products/{prod_id}")
def get_product(prod_id: int, db: Session = Depends(get_db)):
    product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

    if product is None:
        raise HTTPException(status_code=404,detail="Product not found")

    return product

@app.patch("/admin/products/{prod_id}")
def update_product(prod_id: int, prod_name: str = None,price: float = None,seller_id: int = None,db: Session = Depends(get_db)):
    try:

        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

        if product is None:
            raise HTTPException(status_code=404,detail="Product not found")

        if prod_name is not None:
            product.prod_name = prod_name

        if price is not None:

            if price <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid price"
                )

            product.Current_price = price

        if seller_id is not None:

            seller = db.query(db_mdl.seller).filter(
                db_mdl.seller.seller_id == seller_id
            ).first()

            if seller is None:
                raise HTTPException(
                    status_code=404,
                    detail="Seller not found"
                )

            if seller.is_blocked:
                raise HTTPException(
                    status_code=403,
                    detail="Seller is blocked"
                )

            product.seller_id = seller_id

        db.commit()
        db.refresh(product)

        return {
            "message": "Product updated successfully",
            "product": product
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.patch("/admin/products/{prod_id}/stock")
def update_stock(prod_id: int,quantity: int,db: Session = Depends(get_db)):

    try:

        if quantity < 0:
            raise HTTPException(
                status_code=400,
                detail="Stock cannot be negative"
            )

        product = db.query(db_mdl.product).filter(
            db_mdl.product.prod_id == prod_id
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        product.stock = quantity

        db.commit()
        db.refresh(product)

        return {
            "message": "Stock updated successfully",
            "current_stock": product.stock
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.delete("/admin/products/{prod_id}")
def delete_product(prod_id: int, db: Session = Depends(get_db)):

    try:

        product = db.query(db_mdl.product).filter(db_mdl.product.prod_id == prod_id).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        cart_items = db.query(db_mdl.CartItem).filter(db_mdl.CartItem.prod_id == prod_id).first()

        ordered_items = db.query(db_mdl.orderItem).filter(db_mdl.orderItem.prod_id == prod_id).first()

        if cart_items or ordered_items:
            raise HTTPException(
                status_code=409,
                detail="Product cannot be deleted because it is referenced in carts or orders"
            )

        db.delete(product)
        db.commit()

        return {"message": "Product deleted successfully"}

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )
     

@app.get("/admin/orders")
def view_orders(db: Session = Depends(get_db)):
    orders = db.query(db_mdl.order).all()

    return {"total_orders": len(orders),"orders": orders}

@app.get("/admin/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):

    order = db.query(db_mdl.order).filter(db_mdl.order.order_id == order_id).first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    items = db.query(db_mdl.orderItem).filter(db_mdl.orderItem.order_id == order_id).all()

    address = db.query(db_mdl.orderAddress).filter(db_mdl.orderAddress.order_id == order_id).first()

    return {"order": order,"items": items,"shipping_address": address}

@app.patch("/admin/orders/{order_id}")
def update_order(order_id: int, status: str ,db: Session = Depends(get_db)):
    try:

        allowed_status = [
            "Pending",
            "Processing",
            "Shipped",
            "Delivered",
            "Cancelled"
        ]

        if status not in allowed_status:

            raise HTTPException(status_code=400, detail="Invalid order status")

        order = db.query(db_mdl.order).filter(db_mdl.order.order_id == order_id).first()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        order.order_status = status

        db.commit()
        db.refresh(order)

        return {"message": "Order updated successfully", "status": order.order_status}

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.patch("/admin/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    try:

        order = db.query(db_mdl.order).filter(
            db_mdl.order.order_id == order_id
        ).first()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.order_status == "Cancelled":
            raise HTTPException(
                status_code=400,
                detail="Order already cancelled"
            )

        items = db.query(db_mdl.orderItem).filter(
            db_mdl.orderItem.order_id == order_id
        ).all()

        for item in items:

            product = db.query(db_mdl.product).filter(
                db_mdl.product.prod_id == item.prod_id
            ).first()

            if product:
                product.stock += item.quantity

        order.order_status = "Cancelled"

        db.commit()

        return {
            "message": "Order cancelled successfully"
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.delete("/admin/orders/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    try:

        order = db.query(db_mdl.order).filter(
            db_mdl.order.order_id == order_id
        ).first()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        items = db.query(db_mdl.orderItem).filter(
            db_mdl.orderItem.order_id == order_id
        ).all()

        address = db.query(db_mdl.orderAddress).filter(
            db_mdl.orderAddress.order_id == order_id
        ).first()

        for item in items:
            db.delete(item)

        if address:
            db.delete(address)

        db.delete(order)

        db.commit()

        return {
            "message": "Order deleted successfully"
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.get("/admin/users")
def users_list(db: Session = Depends(get_db)):
    users = db.query(db_mdl.user).all()

    return {
        "total_users": len(users),
        "users": users
    }

@app.get("/admin/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):

    user = db.query(db_mdl.user).filter(db_mdl.user.user_id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    addresses = db.query(db_mdl.address).filter(db_mdl.address.user_id == user_id).all()

    orders = db.query(db_mdl.order).filter(db_mdl.order.user_id == user_id).all()

    return {
        "user": user,
        "addresses": addresses,
        "orders": orders}

@app.patch("/admin/users/{user_id}")
def block_user(user_id: int, db: Session = Depends(get_db)):

    try:

        user = db.query(db_mdl.user).filter(db_mdl.user.user_id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404,detail="User not found")

        user.is_blocked = True

        db.commit()

        return {"message": "User blocked successfully"}

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.patch("/admin/users/{user_id}/unblock")
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    try:

        user = db.query(db_mdl.user).filter(
            db_mdl.user.user_id == user_id
        ).first()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user.is_blocked = False

        db.commit()

        return {
            "message": "User unblocked successfully"
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.get("/admin/sellers")
def sellers_list(db: Session = Depends(get_db)):

    sellers = db.query(db_mdl.seller).all()

    return {"total_sellers": len(sellers), "sellers": sellers}

@app.get("/admin/sellers/{seller_id}")
def get_seller(seller_id: int,db: Session = Depends(get_db)):

    seller = db.query(db_mdl.seller).filter(db_mdl.seller.seller_id == seller_id).first()

    if seller is None:
        raise HTTPException(status_code=404, detail="Seller not found")

    products = db.query(db_mdl.product).filter(db_mdl.product.seller_id == seller_id).all()

    return {"seller": seller, "products": products}


@app.get("/admin/sellers/{seller_id}")
def get_seller(
    seller_id: int,
    db: Session = Depends(get_db)
):

    seller = db.query(db_mdl.seller).filter(
        db_mdl.seller.seller_id == seller_id
    ).first()

    if seller is None:
        raise HTTPException(
            status_code=404,
            detail="Seller not found"
        )

    products = db.query(db_mdl.product).filter(
        db_mdl.product.seller_id == seller_id
    ).all()

    return {
        "seller": seller,
        "products": products
    }

@app.patch("/admin/sellers/{seller_id}/block")
def block_seller(
    seller_id: int,
    db: Session = Depends(get_db)
):

    try:

        seller = db.query(db_mdl.seller).filter(
            db_mdl.seller.seller_id == seller_id
        ).first()

        if seller is None:
            raise HTTPException(
                status_code=404,
                detail="Seller not found"
            )

        seller.is_blocked = True

        db.commit()

        return {
            "message": "Seller blocked successfully"
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.patch("/admin/sellers/{seller_id}/unblock")
def unblock_seller(
    seller_id: int,
    db: Session = Depends(get_db)
):

    try:

        seller = db.query(db_mdl.seller).filter(
            db_mdl.seller.seller_id == seller_id
        ).first()

        if seller is None:
            raise HTTPException(
                status_code=404,
                detail="Seller not found"
            )

        seller.is_blocked = False

        db.commit()

        return {
            "message": "Seller unblocked successfully"
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database Error"
        )

@app.get("/admin/dashboard")
def analytics(db: Session = Depends(get_db)):
    
    total_users = db.query(
        func.count(db_mdl.user.user_id)
    ).scalar()

    total_sellers = db.query(
        func.count(db_mdl.seller.seller_id)
    ).scalar()

    total_products = db.query(
        func.count(db_mdl.product.prod_id)
    ).scalar()

    total_orders = db.query(
        func.count(db_mdl.order.order_id)
    ).scalar()

    total_revenue = db.query(
        func.sum(db_mdl.order.total_price)
    ).scalar() or 0

    pending_orders = db.query(
        func.count(db_mdl.order.order_id)
    ).filter(
        db_mdl.order.order_status == "Pending"
    ).scalar()

    delivered_orders = db.query(
        func.count(db_mdl.order.order_id)
    ).filter(
        db_mdl.order.order_status == "Delivered"
    ).scalar()

    cancelled_orders = db.query(
        func.count(db_mdl.order.order_id)
    ).filter(
        db_mdl.order.order_status == "Cancelled"
    ).scalar()

    return {
        "total_users": total_users,
        "total_sellers": total_sellers,
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "total_revenue": total_revenue
    }