import sqlite3
import pandas as pd
import streamlit as st


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

st.set_page_config(
    page_title="Sistema de Inventario", layout="wide"
)

st.title(" Gestión de Inventario y Categorías")
st.write("Aplicación CRUD con base de datos integrada.")

opcion = st.sidebar.selectbox(
    "Selecciona una opción:",
    [
        " Ver Datos (Read)",
        " Agregar (Create)",
        " Editar (Update)",
        " Eliminar (Delete)",
    ],
)


if opcion == " Ver Datos (Read)":
  st.header(" Listado Actual")

  col1, col2 = st.columns(2)

  with col1:
    st.subheader("Categorías")
    conn = get_connection()
    df_cat = pd.read_sql_query("SELECT * FROM categorias", conn)
    conn.close()
    st.dataframe(df_cat, use_container_width=True)

  with col2:
    st.subheader("Productos")
    conn = get_connection()
    query = """
            SELECT p.id, p.nombre AS Producto, p.precio AS Precio, p.stock AS Stock, c.nombre AS Categoria
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
        """
    df_prod = pd.read_sql_query(query, conn)
    conn.close()
    st.dataframe(df_prod, use_container_width=True)


elif opcion == " Agregar (Create)":
  st.header(" Agregar Nuevos Registros")

  tab1, tab2 = st.tabs(["Nueva Categoría", "Nuevo Producto"])

  with tab1:
    with st.form("form_cat"):
      nombre_cat = st.text_input("Nombre de la Categoría")
      submit_cat = st.form_submit_button("Guardar Categoría")

      if submit_cat:
        if nombre_cat.strip():
          conn = get_connection()
          cursor = conn.cursor()
          try:
            cursor.execute(
                "INSERT INTO categorias (nombre) VALUES (?)", (nombre_cat,)
            )
            conn.commit()
            st.success(f"Categoría '{nombre_cat}' agregada correctamente.")
          except sqlite3.IntegrityError:
            st.error("Esa categoría ya existe.")
          finally:
            conn.close()
        else:
          st.warning("Escribe un nombre válido.")

  with tab2:
    conn = get_connection()
    df_cat = pd.read_sql_query("SELECT * FROM categorias", conn)
    conn.close()

    if df_cat.empty:
      st.warning("Primero debes agregar al menos una categoría.")
    else:
      with st.form("form_prod"):
        nombre_prod = st.text_input("Nombre del Producto")
        precio_prod = st.number_input("Precio", min_value=0.0, format="%.2f")
        stock_prod = st.number_input("Stock/Cantidad", min_value=0, step=1)

        cat_dict = dict(zip(df_cat["nombre"], df_cat["id"]))
        cat_seleccionada = st.selectbox(
            "Categoría", list(cat_dict.keys())
        )

        submit_prod = st.form_submit_button("Guardar Producto")

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
            st.success(f"Producto '{nombre_prod}' guardado correctamente.")
          else:
            st.warning("El nombre del producto no puede estar vacío.")


elif opcion == "Editar (Update)":
  st.header(" Actualizar Registro")

  conn = get_connection()
  df_prod = pd.read_sql_query("SELECT * FROM productos", conn)
  df_cat = pd.read_sql_query("SELECT * FROM categorias", conn)
  conn.close()

  if df_prod.empty:
    st.info("No hay productos registrados para editar.")
  else:
    prod_dict = dict(zip(df_prod["nombre"], df_prod["id"]))
    prod_sel = st.selectbox(
        "Selecciona el producto a actualizar:", list(prod_dict.keys())
    )

    prod_data = df_prod[df_prod["id"] == prod_dict[prod_sel]].iloc[0]

    with st.form("form_update"):
      nuevo_nombre = st.text_input("Nombre", value=prod_data["nombre"])
      nuevo_precio = st.number_input(
          "Precio", value=float(prod_data["precio"]), format="%.2f"
      )
      nuevo_stock = st.number_input(
          "Stock", value=int(prod_data["stock"]), step=1
      )

      cat_dict = dict(zip(df_cat["nombre"], df_cat["id"]))
      cat_index = list(cat_dict.values()).index(prod_data["categoria_id"])
      nueva_cat = st.selectbox(
          "Categoría", list(cat_dict.keys()), index=cat_index
      )

      submit_update = st.form_submit_button("Actualizar Producto")

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
        st.success("Producto actualizado exitosamente.")


elif opcion == " Eliminar (Delete)":
  st.header(" Eliminar Registro")

  conn = get_connection()
  df_prod = pd.read_sql_query("SELECT * FROM productos", conn)
  conn.close()

  if df_prod.empty:
    st.info("No hay productos para eliminar.")
  else:
    prod_dict = dict(zip(df_prod["nombre"], df_prod["id"]))
    prod_eliminar = st.selectbox(
        "Selecciona el producto que deseas eliminar:", list(prod_dict.keys())
    )

    if st.button("Eliminar Producto", type="primary"):
      conn = get_connection()
      cursor = conn.cursor()
      cursor.execute(
          "DELETE FROM productos WHERE id = ?", (prod_dict[prod_eliminar],)
      )
      conn.commit()
      conn.close()
      st.warning(f"Producto '{prod_eliminar}' eliminado de la base de datos.")