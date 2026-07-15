from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class productType(SQLModel, table=True):
    """
    Entidad que representa un tipo de producto en la base de datos.

    atributo:
    id: identificador único autoincremental del tipo de producto.
    name: nombre del tipo de producto.
    products: lista de productos asociados a este tipo.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, min_length=1)

    products: List["Product"] = Relationship(back_populates="type")


class Product(SQLModel, table=True):
    """
    Entidad que representa un producto en la base de datos.

    atributos:
    id: Identificador unico autoincremental del producto.
    product_id: identificador del producto en la url.
    title: Titulo del producto.
    price_eur: Precio del producto en euros.
    scraped_at: Fecha y hora de la extraccion.
    type_id: Llave foranea que hace referencia al tipo de producto.
    type: Relacion con la entidad productType.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(ge=1)
    title: str = Field(min_length=1)
    price_eur: float = Field(ge=0)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    type_id: int = Field(default=None, foreign_key="producttype.id")

    type: Optional[productType] = Relationship(back_populates="products")
