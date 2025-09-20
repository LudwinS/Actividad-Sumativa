import sqlite3

DB_Name = "gastos.db"

#Funcion para crear la conexión 

def get_Conexion():
    return sqlite3.connect(DB_Name)

