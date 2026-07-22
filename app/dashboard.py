import time
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlmodel import select
from app.stats import category_stats, price_zscores, price_zscores_pure_python
from gamescout.database import get_session
from gamescout.models import Product


def load_data() -> pd.DataFrame:
    """
    Carga productos y su tipo desde la base de datos.

    Returns:
        pd.DataFrame: columnas product_id, title, type_id, type_name, price_eur.
    """
    with get_session() as session:
        products = session.exec(select(Product)).all()
        return pd.DataFrame(
            [
                {
                    "product_id": p.product_id,
                    "title": p.title,
                    "type_id": p.type_id or 0,
                    "type_name": p.type.name if p.type else "Sin categoría",
                    "price_eur": p.price_eur,
                }
                for p in products
            ]
        )


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza los filtros del sidebar y devuelve el DataFrame filtrado.

    Args:
        df: DataFrame completo de productos.

    Returns:
        pd.DataFrame: subconjunto filtrado según selección del usuario.
    """
    st.sidebar.header("Filtros")

    types = st.sidebar.multiselect(
        "Categoría de Producto",
        sorted(df["type_name"].unique()),
        placeholder="Seleccione Opcion"
    )
    lo, hi = float(df["price_eur"].min()), float(df["price_eur"].max())
    price_range = st.sidebar.slider("Rango de Precio (€)", lo, hi, (lo, hi))
    search = st.sidebar.text_input("Buscar por título")

    out = df
    if types:
        out = out[out["type_name"].isin(types)]
    out = out[out["price_eur"].between(*price_range)]
    if search:
        out = out[out["title"].str.contains(search, case=False, na=False)]
    return out


def render_charts(df: pd.DataFrame) -> None:
    """
    Dibuja las visualizaciones de Plotly y la tabla del catalogo filtrado.

    Args:
        df: DataFrame ya filtrado.
    """
    st.header("Visualizaciones del Catálogo")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Productos Más Caros")
        top10 = df.nlargest(10, "price_eur").sort_values("price_eur")
        fig_top10 = px.bar(
            top10, x="price_eur", y="title", orientation="h", text="price_eur",
            labels={"price_eur": "Precio (€)", "title": "Título"},
        )
        fig_top10.update_traces(texttemplate="%{text:.2f} €", textposition="outside")
        st.plotly_chart(fig_top10, use_container_width=True)

    with col2:
        st.subheader("Distribución de Precios")
        st.plotly_chart(
            px.histogram(df, x="price_eur", nbins=20, labels={"price_eur": "Precio (€)"}),
            use_container_width=True,
        )

    st.subheader("Precio Promedio por Categoría de Producto")
    avg_price = (
        df.groupby("type_name")["price_eur"]
        .mean()
        .reset_index()
        .sort_values(by="price_eur")
    )
    fig_avg = px.bar(
        avg_price, x="price_eur", y="type_name", orientation="h", text="price_eur",
        labels={"price_eur": "Precio Promedio (€)", "type_name": "Categoría"},
    )
    fig_avg.update_traces(texttemplate="%{text:.2f} €", textposition="outside")
    st.plotly_chart(fig_avg, use_container_width=True)

    st.subheader("Catálogo Filtrado")
    table = df[["product_id", "title", "type_name", "price_eur"]].copy()
    table["price_eur"] = table["price_eur"].map(lambda x: f"{x:.2f} €")
    st.dataframe(table, use_container_width=True)


def render_numba_analysis(df: pd.DataFrame) -> None:
    """
    Calcula y muestra estadisticas por categoria, outliers y benchmark Numba vs Python puro.

    Args:
        df: DataFrame completo (sin filtrar) de productos.
    """
    st.header("Analisis Numerico con Numba")

    prices = df["price_eur"].to_numpy(dtype=np.float64)
    type_ids = df["type_id"].to_numpy(dtype=np.int64)
    if len(prices) == 0:
        return

    st.subheader("Resumen por Categoría")
    counts, mins, maxs, means, stds = category_stats(prices, type_ids)
    type_mapping = dict(zip(df["type_id"], df["type_name"]))
    stats_rows = [
        {
            "Categoría": name,
            "Cantidad": int(counts[tid]),
            "Min": f"{mins[tid]:.2f} €",
            "Max": f"{maxs[tid]:.2f} €",
            "Promedio": f"{means[tid]:.2f} €",
            "Desv. Estándar": f"{stds[tid]:.4f}",
        }
        for tid, name in type_mapping.items()
        if counts[tid] > 0
    ]
    st.table(pd.DataFrame(stats_rows))

    st.subheader("Outliers / Ofertas")
    umbral = st.slider("Umbral de Z-Score", 0.0, 5.0, 2.0, 0.1)
    df_z = df.copy()
    df_z["z_score"] = price_zscores(prices, type_ids)
    outliers = df_z[df_z["z_score"].abs() > umbral]
    if outliers.empty:
        st.info("No se detectaron outliers con el umbral actual.")
    else:
        st.dataframe(
            outliers[["title", "type_name", "price_eur", "z_score"]],
            use_container_width=True,
        )

    st.subheader("Benchmark de Rendimiento")
    price_zscores(prices[:1], type_ids[:1])

    start = time.perf_counter()
    price_zscores_pure_python(prices, type_ids)
    time_pure = time.perf_counter() - start

    start = time.perf_counter()
    price_zscores(prices, type_ids)
    time_numba = time.perf_counter() - start

    c1, c2, c3 = st.columns(3)
    c1.metric("Python Puro (seg)", f"{time_pure:.6f}")
    c2.metric("Numba @njit (seg)", f"{time_numba:.6f}")
    c3.metric("Aceleración Numba", f"{(time_pure / time_numba if time_numba > 0 else 0):.2f}x")


def main() -> None:
    """
    Punto de entrada del dashboard: carga datos, filtra y renderiza todas las secciones.
    """
    st.set_page_config(page_title="GameScout Dashboard", layout="wide")
    st.title("GameScout Dashboard Analítico")

    df = load_data()
    if df.empty:
        st.warning("No hay datos en la base de datos.")
        return

    filtered_df = apply_filters(df)
    render_charts(filtered_df)
    render_numba_analysis(df)


if __name__ == "__main__":
    main()
