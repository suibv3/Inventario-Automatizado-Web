import streamlit as st
import pandas as pd
import io



# =============================
# CONFIGURACIÓN DE LA PÁGINA
# =============================
st.set_page_config(
    page_title="Inventario Automatizado",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 Inventario Automatizado")
st.markdown("""
### 💡 Genera reportes automáticos de inventario desde tus archivos Excel
Sube un archivo con tus productos, categorías, stock y precios unitarios para generar análisis y gráficos dinámicos.
""")

# =============================
# SIDEBAR
# =============================
st.sidebar.header("⚙️ Configuración")
st.sidebar.info("Sube tu archivo Excel con las columnas:\n- Producto\n- Categoría\n- Stock\n- Precio Unitario (S/)")
archivo = st.sidebar.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"])

# =============================
# PROCESAMIENTO DEL ARCHIVO
# =============================
if archivo:
    try:
        df = pd.read_excel(archivo)

        # Verificar columnas mínimas requeridas
        columnas_requeridas = {"Producto", "Categoría", "Stock", "Precio Unitario (S/)"}
        if not columnas_requeridas.issubset(df.columns):
            st.error("❌ El archivo debe contener las columnas: Producto, Categoría, Stock y Precio Unitario (S/).")
        else:
            # Calcular valor total
            df["Valor Total (S/)"] = df["Stock"] * df["Precio Unitario (S/)"]

            # Mostrar vista previa
            st.subheader("📋 Vista previa del inventario")
            st.dataframe(df, use_container_width=True)

            # =============================
            # SECCIÓN: ANÁLISIS Y RESUMEN
            # =============================
            st.subheader("📊 Resumen general")

            total_productos = len(df)
            valor_total = df["Valor Total (S/)"].sum()
            precio_promedio = df["Precio Unitario (S/)"].mean()
            producto_max = df.loc[df["Stock"].idxmax(), "Producto"]
            producto_min = df.loc[df["Stock"].idxmin(), "Producto"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de productos", total_productos)
            col2.metric("Valor total del inventario (S/)", f"{valor_total:,.2f}")
            col3.metric("Precio promedio (S/)", f"{precio_promedio:,.2f}")

            col4, col5 = st.columns(2)
            col4.metric("Producto con mayor stock", producto_max)
            col5.metric("Producto con menor stock", producto_min)

            # =============================
            # FILTRO INTELIGENTE
            # =============================
            st.sidebar.subheader("🔍 Filtros dinámicos")
            categorias = df["Categoría"].unique()
            categoria_seleccionada = st.sidebar.multiselect("Selecciona categoría(s):", categorias, default=categorias)

            df_filtrado = df[df["Categoría"].isin(categoria_seleccionada)]

            # =============================
            # GRÁFICOS
            # =============================
            st.subheader("📈 Gráficos de análisis")
            tab1, tab2 = st.tabs(["📊 Stock por producto", "💰 Valor total por categoría"])

            with tab1:
                st.bar_chart(df_filtrado.set_index("Producto")["Stock"])

            with tab2:
                df_cat = df_filtrado.groupby("Categoría")["Valor Total (S/)"].sum().sort_values(ascending=False)
                st.bar_chart(df_cat)

            # =============================
            # DESCARGA DE REPORTE
            # =============================
            st.subheader("💾 Generar reporte Excel")

            with io.BytesIO() as buffer:
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_filtrado.to_excel(writer, sheet_name="Inventario", index=False)
                    resumen = pd.DataFrame({
                        "Indicador": [
                            "Total productos",
                            "Valor total del inventario (S/)",
                            "Precio promedio (S/)",
                            "Producto con mayor stock",
                            "Producto con menor stock"
                        ],
                        "Valor": [
                            total_productos,
                            round(valor_total, 2),
                            round(precio_promedio, 2),
                            producto_max,
                            producto_min
                        ]
                    })
                    resumen.to_excel(writer, sheet_name="Resumen", index=False)
                buffer.seek(0)

                st.download_button(
                    label="📥 Descargar Reporte Excel",
                    data=buffer,
                    file_name="Reporte_Inventario.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
else:
    st.info("📤 Sube un archivo Excel para comenzar el análisis.")


