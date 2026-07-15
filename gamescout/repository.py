from typing import List, Dict, Any
from sqlmodel import Session, select, col
from gamescout.models import Product, productType
from gamescout.database import get_session


def get_or_create_type(name: str, session: Session) -> productType:
    """
    Obtiene un tipo de producto por su nombre o lo crea si no existe.

    Args:
        name (str): Nombre del tipo de producto (categoría).
        session (Session): Sesión activa de base de datos.

    Returns:
        productType: Instancia del modelo productType existente o creado.
    """
    statement = select(productType).where(productType.name == name)
    result = session.exec(statement).first()
    if not result:
        result = productType(name=name)
        session.add(result)
        session.commit()
        session.refresh(result)
    return result


def insert_products(products_data: List[Dict[str, Any]]) -> None:
    """
    Inserta productos evitando duplicados por product_id.

    Args:
        products_data (List[Dict[str, Any]]): Lista de diccionarios
        con datos extraidos.
    """
    with get_session() as session:
        for data in products_data:
            statement = select(Product).where(Product.product_id == data["product_id"])
            existing_product = session.exec(statement).first()

            if not existing_product:
                prod_type = get_or_create_type(data["type_name"], session)

                new_product = Product(
                    product_id=data["product_id"],
                    title=data["title"],
                    price_eur=data["price_eur"],
                    type_id=prod_type.id,
                )
                session.add(new_product)
        session.commit()


def get_top_n(n: int) -> List[Product]:
    """
    Obtiene los N productos mas caros usando la relación de SQLModel.

    Args:
        n (int): Cantidad de productos a retornar.

    Returns:
        List[Product]: Lista de los N productos mas caros.
    """
    with get_session() as session:
        statement = select(Product).order_by(col(Product.price_eur).desc()).limit(n)
        results = session.exec(statement).all()

        for product in results:
            _ = product.type

        return list(results)


def get_products_by_type(type_name: str) -> List[Product]:
    """
    Obtiene todos los productos de un productType dado
    usando la relacion navegable.

    Args:
        type_name (str): Nombre de la categoria a buscar.

    Returns:
        List[Product]: Lista de productos pertenecientes a la categoria.
    """
    with get_session() as session:
        statement = select(productType).where(productType.name == type_name)
        product_type = session.exec(statement).first()

        if not product_type:
            return []

        products = product_type.products

        for product in products:
            _ = product.id

        return list(products)
