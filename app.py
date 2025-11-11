import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ============================================================
# FUNCIÓN: Detectar columnas según sinónimos
# ============================================================
def detectar_columnas(df):
    posibles = {
        'producto': ['producto', 'artículo', 'nombre', 'item', 'descripcion'],
        'categoria': ['categoria', 'tipo', 'clase', 'grupo'],
        'stock': ['stock', 'existencias', 'cantidad', 'disponible', 'inventario'],
        'precio': ['precio', 'costo', 'unitario', 'valor']
    }

    columnas_detectadas = {}
    columnas_norm = {col.lower().strip(): col for col in df.columns}

    for clave, sinonimos in posibles.items():
        for s in sinonimos:
            for col_norm, col_real in columnas_norm.items():
                if s in col_norm:
                    columnas_detectadas[clave] = col_real
                    break
            if clave in columnas_detectadas:
                break

    return columnas_detectadas


# ============================================================
# FUNCIÓN: Generar reporte Excel descargable
# ============================================================
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
        workbook = writer.book
        worksheet = writer.sheets['Inventario']

        # Formato y tabla
        formato_titulo = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center'
        })
        worksheet.merge_range('A1:F1', 'REPORTE AUTOMATIZADO DE INVENTARIO', formato_titulo)
        worksheet.set_column('A:F', 18)

        filas = len(df) + 1
        columnas = len(df.columns) - 1
        worksheet.add_table(1, 0, filas, columnas, {
            'columns': [{'header': col} for col in df.columns],
            'style': 'Table Style Medium 9'
        })

    return output.getvalue()


# ============================================================
# FUNCIÓN: Generar el reporte visual
# ============================================================
def generar_reporte(df, columnas):
    col_prod = columnas.get('producto')
    col_cat = columnas.get('categoria')
    col_stock = columnas.get('stock')
    col_precio = columnas.get('precio')

    # Calcular valor total
    df['Valor Total (S/)'] = df[col_stock] * df[col_precio]

    # Sección de tabla
    st.subheader("📋 Vista previa del inventario")
    st.dataframe(df.head(15))

    # Resumen
    st.subheader("📊 Resumen general del inventario")
    resumen = {
        "Total de productos registrados": len(df),
        "Valor total del inventario (S/)": round(df["Valor Total (S/)"].sum(), 2),
        "Producto con mayor stock": df.loc[df[col_stock].idxmax(), col_prod],
        "Producto con menor stock": df.loc[df[col_stock].idxmin(), col_prod],
        "Precio promedio (S/)": round(df[col_precio].mean(), 2)
    }
    st.write(resumen)

    # ============================
    # Gráficos
    # ============================
    st.subheader("📈 Visualizaciones del inventario")

    if col_cat:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Stock total por categoría**")
            st.bar_chart(df.groupby(col_cat)[col_stock].sum(), use_container_width=True)

        with col2:
            st.markdown("**Distribución del valor total (gráfico de torta)**")
            valor_por_categoria = df.groupby(col_cat)['Valor Total (S/)'].sum()
            st.pyplot(valor_por_categoria.plot.pie(autopct='%1.1f%%', figsize=(5, 5), ylabel="").get_figure())

        # Gráfico adicional de tendencia
        st.markdown("**Tendencia del valor total por categoría**")
        st.line_chart(df.groupby(col_cat)['Valor Total (S/)'].sum(), use_container_width=True)
    else:
        st.warning("No se detectó una columna de categoría para generar gráficos por grupo.")

    # ============================
    # Tabla dinámica
    # ============================
    if col_cat:
        pivot = pd.pivot_table(
            df,
            values="Valor Total (S/)",
            index=[col_cat],
            columns=[col_prod],
            aggfunc=np.sum,
            fill_value=0
        )
        st.subheader("📊 Tabla dinámica (Valor Total por categoría y producto)")
        st.dataframe(pivot)

    # ============================
    # Botón para descargar Excel
    # ============================
    excel_data = generar_excel(df)
    st.download_button(
        label="📥 Descargar reporte Excel",
        data=excel_data,
        file_name="Reporte_Inventario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("✅ Reporte generado correctamente.")


# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.set_page_config(page_title="Automatizador de Reportes", page_icon="📊", layout="wide")

st.title("📊 Automatizador de Reportes de Inventario")
st.markdown(
    "Carga un archivo **Excel (.xlsx o .xls)** con cualquier estructura de columnas. "
    "El sistema detectará automáticamente las cabeceras relacionadas y generará el reporte."
)

archivo = st.file_uploader("📂 Selecciona un archivo Excel", type=["xlsx", "xls"])

if archivo:
    try:
        df = pd.read_excel(archivo)
        columnas = detectar_columnas(df)

        obligatorias = ['producto', 'stock', 'precio']
        faltantes = [c for c in obligatorias if c not in columnas]

        if faltantes:
            st.error(f"❌ No se detectaron las columnas necesarias: {', '.join(faltantes)}.\n\n"
                     f"Verifica que tu archivo tenga nombres relacionados (ejemplo: 'Artículo', 'Costo', 'Existencias').")
        else:
            generar_reporte(df, columnas)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
else:
    st.info("👆 Carga un archivo Excel para comenzar.")

st.markdown("---")
st.caption("Desarrollado con ❤️ en Python y Streamlit")
