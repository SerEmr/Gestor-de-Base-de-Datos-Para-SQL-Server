import tkinter as tk
from tkinter import ttk, messagebox
from connect import get_databases, get_tables, get_columns, execute_query
from PIL import Image, ImageTk
import datetime
import pyodbc


# -----------------------------------------------
# Funciones de Carga de Iconos
# -----------------------------------------------
def load_icons():
    """
    Carga y redimensiona los iconos para las bases de datos, tablas, columnas, claves primarias y foráneas.
    """
    icons = {}
    size = (16, 16)
    icons['database'] = ImageTk.PhotoImage(Image.open("icons/database.png").resize(size, Image.LANCZOS))
    icons['table'] = ImageTk.PhotoImage(Image.open("icons/table.png").resize(size, Image.LANCZOS))
    icons['column'] = ImageTk.PhotoImage(Image.open("icons/column.png").resize(size, Image.LANCZOS))
    icons['pk'] = ImageTk.PhotoImage(Image.open("icons/pk.png").resize(size, Image.LANCZOS))
    icons['fk'] = ImageTk.PhotoImage(Image.open("icons/fk.png").resize(size, Image.LANCZOS))
    return icons

# -----------------------------------------------
# Funciones de Manejo de la Base de Datos
# -----------------------------------------------
def refresh_databases():
    """
    Refresca la lista de bases de datos en el Treeview.
    """
    databases, error = get_databases()
    tree_databases.delete(*tree_databases.get_children())
    if error:
        messagebox.showerror("Error", f"Error al conectar con SQL Server : {error}")
    else:
        for db in databases:
            db_id = tree_databases.insert("", "end", text=db, image=icons['database'], open=False)
            tree_databases.insert(db_id, "end", text="dummy")
        if databases:
            selected_database.set(databases[0])
            update_query_label(databases[0])

def on_tree_item_expand(event):
    """
    Maneja la expansión de elementos en el Treeview para cargar tablas y columnas.
    """
    item_id = tree_databases.focus()
    item_text = tree_databases.item(item_id, "text")
    parent_id = tree_databases.parent(item_id)

    if parent_id == "":
        # Es una base de datos
        database = item_text
        tables, error = get_tables(database)
        if error:
            messagebox.showerror("Error", f"Error al encotrar las tablas de la base de datos {database}: {error}")
        else:
            tree_databases.delete(*tree_databases.get_children(item_id))
            for table in tables:
                table_id = tree_databases.insert(item_id, "end", text=table, image=icons['table'], open=False)
                tree_databases.insert(table_id, "end", text="dummy")
    else:
        # Es una tabla
        database = tree_databases.item(parent_id, "text")
        table = item_text
        columns, error = get_columns(database, table)
        if error:
            messagebox.showerror("Error", f"Error al encontrar las columnas de la tabla {table} en la base de datos {database}: {error}")
        else:
            tree_databases.delete(*tree_databases.get_children(item_id))
            for col_name, col_type, key_type in columns:
                if key_type == 'PK':
                    tree_databases.insert(item_id, "end", text=f"{col_name} (PK)", image=icons['pk'], open=False)
                elif key_type == 'FK':
                    tree_databases.insert(item_id, "end", text=f"{col_name} (FK)", image=icons['fk'], open=False)
                else:
                    tree_databases.insert(item_id, "end", text=col_name, image=icons['column'], open=False)

def on_database_select(event):
    """
    Maneja la selección de una base de datos en el Treeview.
    """
    selected_item = tree_databases.focus()
    parent_item = tree_databases.parent(selected_item)

    if parent_item:
        selected_database.set(tree_databases.item(parent_item, "text"))
    else:
        selected_database.set(tree_databases.item(selected_item, "text"))

    update_query_label(selected_database.get())

def update_query_label(db_name):
    """
    Actualiza la etiqueta que muestra la base de datos seleccionada.
    """
    query_label.config(text=f"Consultas SQL (Base de datos en uso: {db_name})")

# -----------------------------------------------
# Funciones de Ejecución de Consultas
# -----------------------------------------------
def execute_sql():
    """
    Ejecuta la consulta SQL ingresada por el usuario.
    """
    query = text_query.get("1.0", tk.END).strip()
    if not query:
        messagebox.showerror("Error", "No puedes enviar una consulta vacia")
        return

    # Manejo de la consulta USE
    if query.lower().startswith("use "):
        try:
            new_db = query.split()[1]  # Obtener el nombre de la base de datos
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=servidor;'
                'DATABASE=' + new_db + ';'
                'Trusted_Connection=yes;',
                autocommit=True
            )
            selected_database.set(new_db)
            update_query_label(new_db)
            messagebox.showinfo("Éxito", f"Base de datos cambiada a {new_db}\nConsulta ejecutada:\n{query}")
            return  # Salir de la función después de cambiar la base de datos
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar a la base de datos {new_db}: {e}")
            return

    # Manejo de la consulta DROP DATABASE
    if query.lower().startswith("drop database "):
        try:
            db_to_drop = query.split()[2]  # Obtener el nombre de la base de datos a eliminar
            if db_to_drop == selected_database.get():
                # Desconectar de la base de datos seleccionada si es la que se va a eliminar
                selected_database.set("")
                update_query_label("None")
            
            # Ejecutar la consulta de eliminación de la base de datos
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=servidor;'
                'DATABASE=master;'
                'Trusted_Connection=yes;',
                autocommit=True
            )
            cursor = conn.cursor()
            cursor.execute(query)
            messagebox.showinfo("Éxito", f"Base de datos {db_to_drop} eliminada correctamente\nConsulta ejecutada:\n{query}")
            refresh_databases()
            return  # Salir de la función después de eliminar la base de datos
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la base de datos {db_to_drop}: {e}")
            return

    database = selected_database.get()
    if not database:
        messagebox.showerror("Error", "No haz seleccionado una base de datos")
        return

    # Verificar si la consulta es un SELECT
    if query.lower().startswith("select "):
        columns, results, error = execute_query(query, database)
        if error:
            messagebox.showerror("Error", f"Error: {error}")
        else:
            display_results(columns, results)
            messagebox.showinfo("Éxito", f"Consulta SELECT ejecutada correctamente\nConsulta ejecutada:\n{query}")
    else:
        # Para otras consultas, simplemente ejecutarlas y mostrar el texto
        try:
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=servidor;'
                'DATABASE=' + database + ';'
                'Trusted_Connection=yes;',
                autocommit=True
            )
            cursor = conn.cursor()
            cursor.execute(query)
            messagebox.showinfo("Éxito", f"Consulta ejecutada correctamente\nConsulta ejecutada:\n{query}")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

# -----------------------------------------------
# Funciones de Visualización de Resultados
# -----------------------------------------------
def display_results(columns, results):
    """
    Muestra los resultados de una consulta SELECT en un Treeview.
    """
    for widget in frame_results.winfo_children():
        widget.destroy()

    if not columns and not results:
        return

    tree = ttk.Treeview(frame_results, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center', stretch=True)

    for row in results:
        formatted_row = []
        for value in row:
            if isinstance(value, (datetime.date, datetime.datetime)):
                formatted_value = value.strftime('%Y-%m-%d')
            else:
                formatted_value = str(value)
            formatted_row.append(formatted_value)

        tree.insert("", tk.END, values=formatted_row)

    tree.pack(fill=tk.BOTH, expand=True)

def display_query(query):
    """
    Muestra la consulta ejecutada en lugar de una tabla de resultados.
    """
    for widget in frame_results.winfo_children():
        widget.destroy()

    label = tk.Label(frame_results, text=query, wraplength=frame_results.winfo_width(), justify="left")
    label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# -----------------------------------------------
# Funciones de Creación de Bases de Datos y Tablas
# -----------------------------------------------
def open_create_db_window():
    """
    Abre una ventana para crear una nueva base de datos.
    """
    db_window = tk.Toplevel(root)
    db_window.title("Create Database")

    tk.Label(db_window, text="Nombre de la base de datos:").pack(pady=5)
    db_name_entry = tk.Entry(db_window)
    db_name_entry.pack(pady=5)

    def create_database():
        db_name = db_name_entry.get().strip()
        if db_name:
            create_db_and_open_table_window(db_window, db_name)
        else:
            messagebox.showerror("Error", "El Nombre de la base de datos no puede estar vacia")
    
    tk.Button(db_window, text="Crear base de datos", command=create_database).pack(pady=10)

def create_db_and_open_table_window(db_window, db_name):
    """
    Crea una nueva base de datos y abre una ventana para crear una tabla.
    """
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=servidor;'
            'Trusted_Connection=yes;',
            autocommit=True
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {db_name}")
        messagebox.showinfo("Exito", f"La base de de datos {db_name} fue creada exitosamente!")
        db_window.destroy()
        open_create_table_window(db_name)
    except Exception as e:
        messagebox.showerror("Error", f"Error al crear la base de datos: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def open_create_table_window(database):
    """
    Abre una ventana para crear una nueva tabla en la base de datos seleccionada.
    """
    table_window = tk.Toplevel(root)
    table_window.title(f"Añadir una tabla a la base de datos {database}")

    tk.Label(table_window, text="Nombre de la tabla:").grid(row=0, column=0, padx=5, pady=5)
    table_name_entry = tk.Entry(table_window)
    table_name_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=3)

    # Definir los tipos de datos disponibles para SQL Server
    data_types = [
        "INT", "BIGINT", "SMALLINT", "TINYINT", "BIT",
        "DECIMAL", "NUMERIC", "MONEY", "SMALLMONEY",
        "FLOAT", "REAL",
        "DATE", "TIME", "DATETIME", "DATETIME2",
        "CHAR", "VARCHAR", "TEXT", "NCHAR", "NVARCHAR", "NTEXT",
        "BINARY", "VARBINARY", "IMAGE"
    ]

    # Lista para almacenar las filas de entrada de columnas
    column_rows = []

    def add_column_row():
        """
        Añade una fila para la entrada de una nueva columna en la tabla.
        """
        row = len(column_rows) + 1
        
        # Nombre de la columna
        col_name_entry = tk.Entry(table_window)
        col_name_entry.grid(row=row, column=0, padx=5, pady=5)
        
        # Tipo de dato
        col_type_var = tk.StringVar(table_window)
        col_type_menu = ttk.Combobox(table_window, textvariable=col_type_var, values=data_types)
        col_type_menu.grid(row=row, column=1, padx=5, pady=5)

        # Longitud de tipo de dato (para tipos de cadena)
        length_label = tk.Label(table_window, text="Length")
        col_length_entry = tk.Entry(table_window, width=5)
        length_label.grid_forget()  # Ocultar inicialmente
        col_length_entry.grid_forget()  # Ocultar inicialmente

        def show_length_field(event):
            selected_type = col_type_var.get()
            if selected_type in ["VARCHAR", "CHAR", "NVARCHAR", "NCHAR"]:
                length_label.grid(row=row, column=2, padx=5, pady=5)
                col_length_entry.grid(row=row, column=3, padx=5, pady=5)
            else:
                length_label.grid_forget()
                col_length_entry.grid_forget()
                col_length_entry.delete(0, tk.END)

        col_type_menu.bind("<<ComboboxSelected>>", show_length_field)
        
        # Permitir nulo
        col_null_var = tk.BooleanVar()
        col_null_check = tk.Checkbutton(table_window, variable=col_null_var)
        col_null_check.grid(row=row, column=4, padx=5, pady=5)
        null_label = tk.Label(table_window, text="Null")
        null_label.grid(row=row, column=4, padx=(60, 0), pady=5, sticky="w")

        # Clave primaria (PK)
        col_pk_var = tk.BooleanVar()
        col_pk_check = tk.Checkbutton(table_window, variable=col_pk_var)
        col_pk_check.grid(row=row, column=5, padx=5, pady=5)
        pk_label = tk.Label(table_window, text="PK")
        pk_label.grid(row=row, column=5, padx=(60, 0), pady=5, sticky="w")

        # Autoincremento (AI)
        col_ai_var = tk.BooleanVar()
        col_ai_check = tk.Checkbutton(table_window, variable=col_ai_var)
        col_ai_check.grid(row=row, column=6, padx=5, pady=5)
        ai_label = tk.Label(table_window, text="AI")
        ai_label.grid(row=row, column=6, padx=(60, 0), pady=5, sticky="w")

        # Botón para eliminar la columna
        def remove_row():
            col_name_entry.grid_forget()
            col_type_menu.grid_forget()
            col_length_entry.grid_forget()
            col_null_check.grid_forget()
            col_pk_check.grid_forget()
            col_ai_check.grid_forget()
            null_label.grid_forget()
            pk_label.grid_forget()
            ai_label.grid_forget()
            remove_button.grid_forget()
            column_rows.remove((col_name_entry, col_type_var, col_length_entry, col_null_var, col_pk_var, col_ai_var))

        remove_button = tk.Button(table_window, text="X", command=remove_row, bg="red", fg="white")
        remove_button.grid(row=row, column=7, padx=5, pady=5)

        column_rows.append((col_name_entry, col_type_var, col_length_entry, col_null_var, col_pk_var, col_ai_var))

    # Botón para agregar más columnas
    tk.Button(table_window, text="Añadir columna", command=add_column_row).grid(row=1, column=8, padx=5, pady=5)

    # Botón para crear la tabla
    def create_table():
        """
        Crea la tabla con las columnas especificadas por el usuario.
        """
        table_name = table_name_entry.get().strip()
        if not table_name:
            messagebox.showerror("Error", "El nombre de la tabla no puede estar vacio")
            return
        
        columns = []
        identity_columns = []

        for col_name_entry, col_type_var, col_length_entry, col_null_var, col_pk_var, col_ai_var in column_rows:
            col_name = col_name_entry.get().strip()
            col_type = col_type_var.get()
            col_length = col_length_entry.get().strip() if col_length_entry.winfo_ismapped() else ""
            col_null = "NULL" if col_null_var.get() else "NOT NULL"
            col_pk = "PRIMARY KEY" if col_pk_var.get() else ""
            col_ai = "IDENTITY(1,1)" if col_ai_var.get() else ""

            if col_length:  # Para tipos de cadena con longitud
                column_def = f"{col_name} {col_type}({col_length}) {col_null} {col_ai} {col_pk}".strip()
            else:
                column_def = f"{col_name} {col_type} {col_null} {col_ai} {col_pk}".strip()
            
            if col_name and col_type:
                columns.append(column_def)
                if col_ai_var.get():
                    identity_columns.append(col_name)
        
        if not columns:
            messagebox.showerror("Error", "La tabla debe tener almenos una columna")
            return

        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
        
        try:
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=servidor;'
                'DATABASE=' + database + ';'
                'Trusted_Connection=yes;',
                autocommit=True
            )
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            messagebox.showinfo("Exito", f"Tabla  {table_name} creada exitosamente en {database}!")
            refresh_databases()
            table_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"al crear la base de datos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    tk.Button(table_window, text="Crear tabla", command=create_table).grid(row=2, column=8, padx=5, pady=10)

    # Agregar una fila inicial por defecto
    add_column_row()


# -----------------------------------------------
# Configuración de la Ventana Principal y Widgets
# -----------------------------------------------
root = tk.Tk()
root.title("GBD SQLSERVER")

# Cargar iconos
icons = load_icons()

# Marco izquierdo para la lista de bases de datos
frame_left = tk.Frame(root, width=300)
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

tk.Label(frame_left, text="Bases de datos").pack(anchor=tk.NW)
tree_databases = ttk.Treeview(frame_left)
tree_databases.pack(fill=tk.BOTH, expand=True)
tree_databases.bind("<<TreeviewOpen>>", on_tree_item_expand)
tree_databases.bind("<<TreeviewSelect>>", on_database_select)

button_refresh = tk.Button(frame_left, text="Refrescar", command=refresh_databases)
button_refresh.pack(pady=5)

# Botón para crear una nueva base de datos
button_create_db = tk.Button(frame_left, text="Crear base de datos", command=open_create_db_window)
button_create_db.pack(pady=5)

# Marco derecho para la consulta y resultados
frame_right = tk.Frame(root)
frame_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

query_label = tk.Label(frame_right, text="Consultas SQL(Base de datos en uso: None)")
query_label.pack(anchor=tk.NW)
text_query = tk.Text(frame_right, height=10)
text_query.pack(fill=tk.X)

button_execute = tk.Button(frame_right, text="Ejecutar consulta", command=execute_sql)
button_execute.pack(pady=5)

frame_results = tk.Frame(frame_right)
frame_results.pack(fill=tk.BOTH, expand=True)

# Variable para almacenar la base de datos seleccionada
selected_database = tk.StringVar()

# Mostrar las bases de datos al iniciar la aplicación
refresh_databases()

# Ejecutar la aplicación
root.mainloop()
