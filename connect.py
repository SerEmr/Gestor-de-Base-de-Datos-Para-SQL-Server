import pyodbc

# -----------------------------------------------
# Funciones para Obtener Información de la Base de Datos
# -----------------------------------------------
def get_databases():
    """
    Obtiene la lista de bases de datos disponibles en el servidor SQL Server.

    Retorna:
        - databases: Lista de nombres de bases de datos.
        - error: Mensaje de error en caso de fallo.
    """
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=servidor;'
            'Trusted_Connection=yes;'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases")
        databases = [row[0] for row in cursor.fetchall()]
        return databases, None
    except Exception as e:
        return None, str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_tables(database):
    """
    Obtiene la lista de tablas en una base de datos específica.

    Parámetros:
        - database: Nombre de la base de datos de la cual obtener las tablas.

    Retorna:
        - tables: Lista de nombres de tablas.
        - error: Mensaje de error en caso de fallo.
    """
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=servidor;'
            'DATABASE=' + database + ';'
            'Trusted_Connection=yes;'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.tables")
        tables = [row[0] for row in cursor.fetchall()]
        return tables, None
    except Exception as e:
        return None, str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_columns(database, table):
    """
    Obtiene la lista de columnas de una tabla específica, incluyendo sus tipos de datos y claves.

    Parámetros:
        - database: Nombre de la base de datos.
        - table: Nombre de la tabla.

    Retorna:
        - columns: Lista de tuplas con (nombre de columna, tipo de dato, tipo de clave).
        - error: Mensaje de error en caso de fallo.
    """
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=servidor;'
            'DATABASE=' + database + ';'
            'Trusted_Connection=yes;'
        )
        cursor = conn.cursor()

        # Obtener columnas
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH, 
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table}'
        """)
        columns_info = cursor.fetchall()
        
        # Obtener claves primarias
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_NAME), 'IsPrimaryKey') = 1
            AND TABLE_NAME = '{table}'
        """)
        pk_columns = {row.COLUMN_NAME for row in cursor.fetchall()}
        
        # Obtener claves foráneas
        cursor.execute(f"""
            SELECT KCU.COLUMN_NAME
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU 
            ON RC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME
            WHERE KCU.TABLE_NAME = '{table}'
        """)
        fk_columns = {row.COLUMN_NAME for row in cursor.fetchall()}
        
        # Combinar la información y agregar el tipo de clave
        columns = []
        for col in columns_info:
            col_name = col.COLUMN_NAME
            if col_name in pk_columns:
                key_type = 'PK'
            elif col_name in fk_columns:
                key_type = 'FK'
            else:
                key_type = None
            columns.append((col_name, col.DATA_TYPE, key_type))

        return columns, None
    except Exception as e:
        return None, str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# -----------------------------------------------
# Función para Ejecutar Consultas SQL
# -----------------------------------------------
def execute_query(query, database):
    """
    Ejecuta una consulta SQL en la base de datos especificada.

    Parámetros:
        - query: Consulta SQL a ejecutar.
        - database: Nombre de la base de datos en la cual ejecutar la consulta.

    Retorna:
        - columns: Lista de nombres de columnas (si aplica).
        - results: Lista de resultados de la consulta (si aplica).
        - error: Mensaje de error en caso de fallo.
    """
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
        if cursor.description:  # Verificar si la consulta devuelve resultados
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
        else:
            columns = []
            results = []
        return columns, results, None
    except Exception as e:
        return None, None, str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
