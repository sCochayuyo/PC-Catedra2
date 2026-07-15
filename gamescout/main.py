import os
from typing import List, Dict, Any

from gamescout.database import create_db_and_tables
from gamescout.repository import (
    get_products_by_type,
    get_top_n,
    insert_products,
)
from gamescout.scraper import scrapping


def main() -> None:
    """
    Funcion principal que ejecuta el flujo completo del programa:
    Crea base de datos, ejecuta el scraper, guarda los datos
    en la base de datos y ejecuta consultas.
    """

    os.mkdir("data") if not os.path.exists("data") else None

    print("Creando base de datos y tablas...")
    create_db_and_tables()

    print("Iniciando scraping...")
    scraped_data: List[Dict[str, Any]] = scrapping()

    print("Guardando datos en la base de datos...")
    insert_products(scraped_data)

    # Ejecucion de consultas
    print("\n Top 3 productos mas caros")
    top_3 = get_top_n(3)
    for product in top_3:
        type_name = product.type.name if product.type else "Desconocido"
        print(
            f"ID: {product.product_id}, Titulo: {product.title}, "
            f"Precio: {product.price_eur} EUR, Tipo: {type_name}"
        )

    print("\n Productos de la categoria 'Action'")
    products_action = get_products_by_type("Action")

    if products_action:
        for game in products_action:
            print(f"ID: {game.product_id}, Titulo: {game.title}, " f"Precio: {game.price_eur} EUR")
    else:
        print("No se encontraron productos en la categoria 'Action'.")


if __name__ == "__main__":
    main()
