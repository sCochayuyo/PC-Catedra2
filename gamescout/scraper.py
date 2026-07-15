import logging
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def scrapping() -> List[Dict[str, Any]]:
    """
    Realiza el scrapping del catalogo
    de productos de gamescout en modo headless.

    Returns:
        List[Dict[str, Any]]: Lista de diccionarios con los datos extraidos.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    base_url = "https://sandbox.oxylabs.io/products"
    scraped_data: List[Dict[str, Any]] = []

    try:
        for page in range(1, 6):
            url = f"{base_url}?page={page}"
            driver.get(url)
            logging.info(f"--- Escaneando pagina {page} ---")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card"))
                )

            except TimeoutException:
                logging.warning(f"Timeout al cargar la pagina {url}.")
                continue

            cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")

            for card in cards:
                try:

                    link_elemnt = card.find_element(By.CSS_SELECTOR, "a.card-header")
                    href = link_elemnt.get_attribute("href") or ""
                    product_id = int(href.split("/")[-1])

                    title = card.find_element(By.CSS_SELECTOR, ".title").text.strip()

                    category_elemnt = card.find_element(By.CSS_SELECTOR, ".category span")
                    type_name = category_elemnt.text.strip()

                    price_text = card.find_element(By.CSS_SELECTOR, ".price-wrapper").text

                    clean_price = price_text.replace("€", "").replace(",", ".").strip()
                    price_eur = float(clean_price)

                    logging.info(f"Guardado: ID {product_id} | " f"{title} | " f"{price_eur} EUR")

                    scraped_data.append(
                        {
                            "product_id": product_id,
                            "title": title,
                            "type_name": type_name,
                            "price_eur": price_eur,
                        }
                    )

                except (NoSuchElementException, ValueError, IndexError) as e:
                    logging.warning(f"Error procesando tarjeta en página {page}: {e}")
                    continue

    finally:
        driver.quit()

    logging.info(f"Scraping finalizado. Total de productos: {len(scraped_data)}")

    return scraped_data
