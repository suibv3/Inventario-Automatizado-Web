# app.py
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# ---------------- Page config ----------------
st.set_page_config(page_title="Inventario Automatizado", page_icon="📦", layout="wide")
st.title("📦 Inventario Automatizado")
st.markdown(
    "### 💡 Genera reportes automáticos de inventario desde tus archivos Excel\n"
    "Sube un archivo con productos, categorías, proveedores, stock y precios unitarios. "
    "El sistema detectará columnas similares automáticamente."
)

# ---------------- Helpers: flexible detection ----------------
def detectar_y_normalizar_columnas(df: pd.DataFrame):
    """
    Detecta columnas por sinónimos y renombra internamente a:
    'Producto', 'Categoría', 'Proveedor', 'Stock', 'Precio Unitario (S/)'.
    Devuelve (df_renombrado, detected_map).
    """
    posibles = {
        'Producto': ['producto', 'artículo', 'articulo', 'nombre', 'item', 'descr', 'descripcion'],
        'Categoría': ['categoria', 'categoría', 'tipo', 'clase', 'grupo', 'familia'],
        'Proveedor': ['proveedor', 'supplier', 'vendor', 'distribuidor'],
        'Stock': ['stock', 'existencias', 'cantidad', 'disponible', 'inventario', 'qty', 'unidades'],
        'Precio Unitario (S/)': ['precio unitario', 'precio', 'costo', 'valor unitario', 'price', 'cost']
    }

    cols_map = {}
    cols_lower = {c.lower().strip(): c for c in df.columns}

    for standard, synonyms in posibles.items():
        found = None
        for syn in synonyms:
            for col_lower, col_real in cols_lower.items():
                if syn in col_lower:
                    found = col_real
                    break
            if found:
                cols_map[standard] = found
                break

    # Build renaming dict: original_col -> standard_name
    ren = {orig: std for std, orig in cols_map.items()}

    df2 = df.rename(columns=ren)
    return df2, cols_map

# ---------------- Sidebar / file uploader ----------------
st.sidebar.header("⚙️ Configuración")
st.sidebar.info("Sube un archivo Excel (.xlsx/.xls). "
                "Se requieren al menos: Producto, Stock , Precio .")
archivo = st.sidebar.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"])

# ---------------- Main processing ----------------
if archivo:
    try:
        df = pd.read_excel(archivo)

        # Detect and rename flexible columns
        df_norm, detected = detectar_y_normalizar_columnas(df)

        # Required minimal
        required = ['Producto', 'Stock', 'Precio Unitario (S/)']
        missing_required = [r for r in required if r not in detected]

        if missing_required:
            st.error(
                "❌ No se detectaron las columnas mínimas: "
                f"{', '.join(missing_required)}.\n\n"
                "Ejemplos aceptables: 'Producto'/'Artículo'/'Nombre', "
                "'Stock'/'Existencias'/'Cantidad', 'Precio'/'Costo'/'Precio Unitario'."
            )
        else:
            # Use the renamed df
            df_work = df_norm.copy()

            # Ensure numeric for stock and price
            df_work['Stock'] = pd.to_numeric(df_work['Stock'], errors='coerce').fillna(0)
            df_work['Precio Unitario (S/)'] = pd.to_numeric(df_work['Precio Unitario (S/)'], errors='coerce').fillna(0)

            # Compute Valor Total
            df_work['Valor Total (S/)'] = df_work['Stock'] * df_work['Precio Unitario (S/)']

            # Show detected mapping to user
            st.sidebar.subheader("Columnas detectadas")
            for std, orig in detected.items():
                st.sidebar.write(f"- **{std}**  ←  `{orig}`")

            # Preview
            st.subheader("📋 Vista previa del inventario")
            st.dataframe(df_work.head(20), use_container_width=True)

            # Summary metrics
            st.subheader("📊 Resumen general")
            total_productos = len(df_work)
            valor_total = df_work['Valor Total (S/)'].sum()
            precio_promedio = df_work['Precio Unitario (S/)'].mean() if 'Precio Unitario (S/)' in df_work.columns else 0
            # For max/min product by stock ensure non-empty
            if total_productos > 0:
                idx_max = df_work['Stock'].idxmax()
                idx_min = df_work['Stock'].idxmin()
                producto_max = df_work.loc[idx_max, 'Producto']
                producto_min = df_work.loc[idx_min, 'Producto']
            else:
                producto_max = producto_min = None

            c1, c2, c3 = st.columns(3)
            c1.metric("Total de productos", total_productos)
            c2.metric("Valor total (S/)", f"{valor_total:,.2f}")
            c3.metric("Precio promedio (S/)", f"{precio_promedio:,.2f}")

            c4, c5 = st.columns(2)
            c4.metric("Producto con mayor stock", producto_max)
            c5.metric("Producto con menor stock", producto_min)

            # Filters: if category exists, allow multi-select
            st.sidebar.subheader("🔍 Filtros")
            if 'Categoría' in df_work.columns:
                categorias = df_work['Categoría'].dropna().unique().tolist()
                selected_cats = st.sidebar.multiselect("Filtrar por Categoría", categorias, default=categorias)
                df_filtered = df_work[df_work['Categoría'].isin(selected_cats)]
            else:
                df_filtered = df_work
                if 'Categoría' not in df_work.columns:
                    st.sidebar.info("Columna 'Categoría' no detectada: algunos gráficos/pivots no estarán disponibles.")

            # Visualization: bar (stock by product) and pie (product vs value total)
            st.subheader("📈 Visualizaciones")
            g1, g2 = st.columns(2)

            with g1:
                st.markdown("**📊 Stock por producto**")
                if 'Producto' in df_filtered.columns:
                    # ensure index unique for bar_chart
                    series_stock = df_filtered.groupby('Producto')['Stock'].sum().sort_values(ascending=False)
                    st.bar_chart(series_stock)
                else:
                    st.info("No se detectó columna 'Producto' para este gráfico.")

            with g2:
                st.markdown("**🥧 Torta: Producto vs Valor Total**")
                if 'Producto' in df_filtered.columns:
                    series_val = df_filtered.groupby('Producto')['Valor Total (S/)'].sum().sort_values(ascending=False)
                    # limit labels if too many products
                    if len(series_val) > 20:
                        series_val = series_val.nlargest(20)
                    fig, ax = plt.subplots(figsize=(5,5))
                    ax.pie(series_val, labels=series_val.index, startangle=90)
                    ax.axis('equal')
                    st.pyplot(fig)
                else:
                    st.info("No se detectó columna 'Producto' para este gráfico.")

            # Pivot dynamic: value total by category and provider (if available)
            st.subheader("📊 Tabla dinámica")
            if ('Categoría' in df_work.columns) and ('Proveedor' in df_work.columns):
                pivot = pd.pivot_table(
                    df_work,
                    values='Valor Total (S/)',
                    index='Categoría',
                    columns='Proveedor',
                    aggfunc='sum',
                    fill_value=0,
                    margins=False
                )
                st.write("**PIVOT: Valor Total por Categoría y Proveedor**")
                st.dataframe(pivot, use_container_width=True)
            elif 'Categoría' in df_work.columns:
                pivot = pd.pivot_table(
                    df_work,
                    values='Valor Total (S/)',
                    index='Categoría',
                    aggfunc='sum',
                    fill_value=0
                ).reset_index()
                st.write("**PIVOT: Valor Total por Categoría**")
                st.dataframe(pivot, use_container_width=True)
            else:
                st.info("No hay suficientes columnas para generar la tabla dinámica (se requiere 'Categoría').")

            # ---------------- Generate Excel with 3 sheets ----------------
            st.subheader("💾 Generar reporte Excel (3 hojas)")
            with io.BytesIO() as buffer:
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    workbook = writer.book

                    # --- Sheet 1: Inventario with autofilter and charts ---
                    startrow = 3  # leave space for title rows
                    df_filtered.to_excel(writer, sheet_name='Inventario', index=False, startrow=startrow)
                    ws = writer.sheets['Inventario']

                    # Title format
                    title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
                    ws.merge_range(0, 0, 0, max(4, len(df_filtered.columns)-1), 'REPORTE AUTOMATIZADO DE INVENTARIO', title_fmt)

                    # Apply autofilter over header row (header is at startrow)
                    nrows = len(df_filtered)
                    ncols = len(df_filtered.columns)
                    header_row = startrow
                    first_data_row = startrow + 1
                    last_data_row = startrow + nrows

                    # set reasonable column widths
                    for i, col in enumerate(df_filtered.columns):
                        max_len = max(df_filtered[col].astype(str).map(len).max() if nrows>0 else 0, len(str(col)))
                        ws.set_column(i, i, min(40, max_len + 4))

                    # add table (makes Excel show filters in header)
                    columns_table = [{'header': c} for c in df_filtered.columns]
                    ws.add_table(header_row, 0, last_data_row, ncols-1, {'columns': columns_table, 'style': 'Table Style Medium 9'})

                    # Charts: compute column indices
                    col_idx = {c: i for i, c in enumerate(df_filtered.columns)}

                    # Chart 1: Stock by product (categories = Producto, values = Stock)
                    if 'Producto' in col_idx and 'Stock' in col_idx:
                        chart1 = workbook.add_chart({'type': 'column'})
                        chart1.add_series({
                            'name': 'Stock por producto',
                            'categories': ['Inventario', first_data_row, col_idx['Producto'], last_data_row, col_idx['Producto']],
                            'values': ['Inventario', first_data_row, col_idx['Stock'], last_data_row, col_idx['Stock']],
                        })
                        chart1.set_title({'name': 'Stock por Producto'})
                        chart1.set_x_axis({'name': 'Producto'})
                        chart1.set_y_axis({'name': 'Stock'})
                        # insert chart at H5 (col 7, row 4)
                        ws.insert_chart('H5', chart1, {'x_scale': 1.0, 'y_scale': 1.0})

                    # Chart 2: Pie product vs Valor Total
                    if 'Producto' in col_idx and 'Valor Total (S/)' in col_idx:
                        chart2 = workbook.add_chart({'type': 'pie'})
                        chart2.add_series({
                            'name': 'Valor Total por Producto',
                            'categories': ['Inventario', first_data_row, col_idx['Producto'], last_data_row, col_idx['Producto']],
                            'values': ['Inventario', first_data_row, col_idx['Valor Total (S/)'], last_data_row, col_idx['Valor Total (S/)']],
                        })
                        chart2.set_title({'name': 'Distribución del Valor Total por Producto'})
                        ws.insert_chart('H22', chart2, {'x_scale': 1.0, 'y_scale': 1.0})

                    # --- Sheet 2: Reporte (resumen) ---
                    ws2 = workbook.add_worksheet('Reporte')
                    ws2.merge_range(0, 0, 0, 1, 'REPORTE RESUMIDO DEL INVENTARIO', title_fmt)
                    resumen_list = [
                        ['Total de productos', total_productos],
                        ['Valor total del inventario (S/)', round(valor_total, 2)],
                        ['Precio promedio (S/)', round(precio_promedio, 2)],
                        ['Producto con mayor stock', producto_max],
                        ['Producto con menor stock', producto_min]
                    ]
                    bold = workbook.add_format({'bold': True})
                    ws2.write_column(3, 0, [r[0] for r in resumen_list], bold)
                    ws2.write_column(3, 1, [r[1] for r in resumen_list])
                    ws2.set_column(0, 1, 40)

                    # --- Sheet 3: Resumen dinámico (pivot) ---
                    if ('Categoría' in df_work.columns) and ('Proveedor' in df_work.columns):
                        pivot = pd.pivot_table(df_work, values='Valor Total (S/)', index='Categoría', columns='Proveedor', aggfunc='sum', fill_value=0)
                        pivot.to_excel(writer, sheet_name='Resumen dinámico', startrow=2)
                        ws3 = writer.sheets['Resumen dinámico']
                        ws3.merge_range(0, 0, 0, max(1, len(pivot.columns)), 'TABLA DINÁMICA: VALOR TOTAL POR CATEGORÍA Y PROVEEDOR', title_fmt)
                        # format columns
                        for i, col in enumerate(pivot.reset_index().columns):
                            ws3.set_column(i, i, 20)
                    elif ('Categoría' in df_work.columns):
                        pivot = df_work.groupby('Categoría')['Valor Total (S/)'].sum().reset_index()
                        pivot.to_excel(writer, sheet_name='Resumen dinámico', index=False, startrow=2)
                        ws3 = writer.sheets['Resumen dinámico']
                        ws3.merge_range(0, 0, 0, 1, 'TABLA DINÁMICA: VALOR TOTAL POR CATEGORÍA', title_fmt)
                        ws3.set_column(0, 1, 30)
                    else:
                        # no pivot possible; write a note
                        ws3 = workbook.add_worksheet('Resumen dinámico')
                        ws3.write(0, 0, 'No hay suficientes columnas para generar la tabla dinámica (se requiere "Categoría").')

                buffer.seek(0)
                st.download_button(
                    label="📥 Descargar Reporte Excel Completo",
                    data=buffer,
                    file_name="Reporte_Inventario_Completo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el archivo: {e}")

else:
    st.info("📤 Sube un archivo Excel para comenzar el análisis.")

