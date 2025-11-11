import streamlit as st
import pandas as pd
import io
import openpyxl
import xlsxwriter

st.set_page_config(page_title="Inventario Automatizado", page_icon="📊", layout="wide")

st.title("📦 Reporte Automatizado de Inventario")
st.markdown("Sube tu archivo Excel para generar reportes, análisis y gráficos dinámicos.")

# --- Carga de archivo ---
archivo = st.file_uploader("Selecciona un archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        df = pd.read_excel(archivo)

        # Verificar columnas necesarias
        columnas_requeridas = {"Producto", "Categoría", "Stock", "Precio Unitario (S/)"}
        if not columnas_requeridas.issubset(df.columns):
            st.error("❌ El archivo no contiene las columnas necesarias.")
        else:
            # Calcular valores
            df["Valor Total (S/)"] = df["Stock"] * df["Precio Unitario (S/)"]

            st.success("✅ Archivo cargado correctamente.")
            st.subheader("📋 Vista previa del inventario")
            st.dataframe(df, use_container_width=True)

            # --- Resumen ---
            st.subheader("📈 Resumen general")
            total_productos = len(df)
            valor_total = df["Valor Total (S/)"].sum()
            precio_prom = df["Precio Unitario (S/)"].mean()
            producto_max = df.loc[df["Stock"].idxmax(), "Producto"]
            producto_min = df.loc[df["Stock"].idxmin(), "Producto"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total productos", total_productos)
            col2.metric("Valor total (S/)", f"{valor_total:,.2f}")
            col3.metric("Precio promedio (S/)", f"{precio_prom:,.2f}")

            col4, col5 = st.columns(2)
            col4.metric("Producto con mayor stock", producto_max)
            col5.metric("Producto con menor stock", producto_min)

            # --- Gráficos ---
            st.subheader("📊 Análisis visual")
            tab1, tab2 = st.tabs(["Gráfico de Barras", "Gráfico Circular"])

            with tab1:
                st.bar_chart(df.set_index("Producto")["Stock"])

            with tab2:
                st.bar_chart(df.set_index("Producto")["Valor Total (S/)"])

            # --- Exportar a Excel ---
            st.subheader("💾 Generar reporte Excel")

            with io.BytesIO() as buffer:
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="Inventario", index=False)
                    resumen = pd.DataFrame({
                        "Descripción": ["Total productos", "Valor total (S/)", "Precio promedio (S/)"],
                        "Valor": [total_productos, valor_total, precio_prom]
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
