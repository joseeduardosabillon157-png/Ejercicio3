import sqlite3
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Gestión de Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para darle un toque moderno y pulido
st.markdown(
    """
    <style>
    /* Estilo del título principal */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    /* Tarjetas de métricas */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #2563EB;
    }
    /* Botones mejorados */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# BASE DE DATOS
# ---------------------------------------------------------
DB_NAME = "inventario.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
        )
    """)

  conn.commit()
  conn.close()


def get_connection():
  return sqlite3.connect(DB_NAME)


init_db()

# ---------------------------------------------------------
# ENCABEZADO
# ---------------------------------------------------------
st.markdown(
    "<h1 class='main-header'>📦 Sistema Inteligente de Inventarios</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='sub-header'>Panel de control y gestión de base de datos en"
    " tiempo real</p>",
    unsafe_allow_html=True,
)

st.sidebar.image(
    "https://cdn-icons-png.flaticon.com/512/2897/2897785.png", width=100
)
st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Selecciona una acción:",
    [
        " Panel Principal (Read)",
        " Registrar Nuevo (Create)",
        " Actualizar Datos (Update)",
        " Eliminar Registro (Delete)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(" **Tip:** Asegúrate de registrar al menos una categoría.")

if opcion == " Panel Principal (Read)":
  st.subheader(" Resumen del Inventario")

  conn = get_connection()
  df_cat = pd.read_sql_query("SELECT * FROM categorias", conn)
  query_prod = """
        SELECT p.id, p.nombre AS Producto, p.precio AS Precio, p.stock AS Stock, c.nombre AS Categoria
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
    """
  df_prod = pd.read_sql_query(query_prod, conn)
  conn.close()

  # Métricas rápidas arriba
  col_m1, col_m2, col_m3 = st.columns(3)
  col_m1.metric("Categorías Registradas", len(df_cat))
  col_m2.metric("Total de Productos", len(df_prod))
  col_m3.metric(
      "Unidades en Stock",
      int(df_prod["Stock"].sum()) if not df_prod.empty else 0,
  )

  st.markdown("---")

  # Tablas de datos
  col1, col2 = st.columns([1, 2])

  with col1:
    st.markdown("###  Categorías")
    st.dataframe(df_cat, use_container_width=True, hide_index=True)

  with col2:
    st.markdown("###  Productos Registrados")
    st.dataframe(df_prod, use_container_width=True, hide_index=True)

elif opcion == "➕ Registrar Nuevo (Create)":
  st.subheader("➕ Registro de Entidades")

  tab1, tab2 = st.tabs([" Nueva Categoría", " Nuevo Producto"])

  with tab1:
    with st.form("form_cat", clear_on_submit=True):
      nombre_cat = st.text_input(
          "Nombre de la Categoría", placeholder="Ej: Electrónica, Granos..."
      )
      submit_cat = st.form_submit_button("💾 Guardar Categoría")

      if submit_cat:
        if nombre_cat.strip():
          conn = get_connection()
          cursor = conn.cursor()
          try:
            cursor.execute(
                "INSERT INTO categorias (nombre) VALUES (?)", (nombre_cat,)
            )
            conn.commit()
            st.success(f" Categoría '{nombre_cat}' registrada con éxito.")
          except sqlite3.IntegrityError:
            st.error(" La categoría ya existe.")
          finally:
            conn.close()
        else:
          st.warning(" Escribe un nombre válido.")

  with tab2:
    conn = get_connection()
    df_cat = pd.read_sql_query("SELECT * FROM categorias", conn)
    conn.close()

    if df_cat.empty:
      st.warning(
          " Primero debes agregar al menos una categoría en la pestaña"
          " anterior."
      )
    else:
      with st.form("form_prod", clear_on_submit=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
          nombre_prod = st.text_input(
              "Nombre del Producto", placeholder="Ej: Laptop Dell"
          )
          precio_prod = st.number_input(
              "Precio ($)", min_value=0.0, format="%.2f"
          )
        with col_p2:
          stock_prod = st.number_input(
              "Stock Inicial", min_value=0, step=1, value=1
          )
          cat_dict = dict(zip(df_cat["nombre"], df_cat["id"]))
          cat_seleccionada = st.selectbox("Categoría", list(cat_dict.keys()))

        submit_prod = st.form_submit_button("💾 Guardar Producto")

        if submit_prod:
          if nombre_prod.strip():
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                            INSERT INTO productos (nombre, precio, stock, categoria_id)
                            VALUES (?, ?, ?, ?)
                        """,
                (
                    nombre_prod,
                    precio_prod,
                    stock_prod,
                    cat_dict[cat_seleccionada],
                ),
            )
            conn.commit()
            conn.close()
            st.success(f" Producto '{nombre_prod}' registrado con éxito.")
          else:
            st.warning(" Escribe un nombre válido para el producto.")


elif opcion == " Actualizar Datos (Update)":
  st.subheader(" Modificar Información de Productos")

  conn = get_connection()
  df_prod = pd.read_sql_query("SELECT * FROM productos", conn)
  df_cat = pd.read_sql_query("SELECT * FROM categorias", conn)
  conn.close()

  if df_prod.empty:
    st.info(" No hay productos disponibles para modificar.")
  else:
    prod_dict = dict(zip(df_prod["nombre"], df_prod["id"]))
    prod_sel = st.selectbox(
        "Selecciona el producto que deseas modificar:", list(prod_dict.keys())
    )

    prod_data = df_prod[df_prod["id"] == prod_dict[prod_sel]].iloc[0]

    with st.form("form_update"):
      col_u1, col_u2 = st.columns(2)
      with col_u1:
        nuevo_nombre = st.text_input("Nombre", value=prod_data["nombre"])
        nuevo_precio = st.number_input(
            "Precio ($)", value=float(prod_data["precio"]), format="%.2f"
        )
      with col_u2:
        nuevo_stock = st.number_input(
            "Stock", value=int(prod_data["stock"]), step=1
        )
        cat_dict = dict(zip(df_cat["nombre"], df_cat["id"]))
        cat_index = list(cat_dict.values()).index(prod_data["categoria_id"])
        nueva_cat = st.selectbox(
            "Categoría", list(cat_dict.keys()), index=cat_index
        )

      submit_update = st.form_submit_button(" Actualizar Producto")

      if submit_update:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
                    UPDATE productos
                    SET nombre = ?, precio = ?, stock = ?, categoria_id = ?
                    WHERE id = ?
                """,
            (
                nuevo_nombre,
                nuevo_precio,
                nuevo_stock,
                cat_dict[nueva_cat],
                prod_dict[prod_sel],
            ),
        )
        conn.commit()
        conn.close()
        st.success(" Producto actualizado exitosamente.")

elif opcion == " Eliminar Registro (Delete)":
  st.subheader(" Eliminar Producto")

  conn = get_connection()
  df_prod = pd.read_sql_query("SELECT * FROM productos", conn)
  conn.close()

  if df_prod.empty:
    st.info(" No hay productos disponibles para eliminar.")
  else:
    prod_dict = dict(zip(df_prod["nombre"], df_prod["id"]))
    prod_eliminar = st.selectbox(
        "Selecciona el producto que deseas eliminar definitivamente:",
        list(prod_dict.keys()),
    )

    st.error("⚠️ Atención: Esta acción no se puede deshacer.")
    if st.button("🗑️ Confirmar Eliminación", type="primary"):
      conn = get_connection()
      cursor = conn.cursor()
      cursor.execute(
          "DELETE FROM productos WHERE id = ?", (prod_dict[prod_eliminar],)
      )
      conn.commit()
      conn.close()
      st.success(f"🗑️ El producto '{prod_eliminar}' fue eliminado.")
