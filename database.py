import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LAPTOP-3GT9SESD\\SQLEXPRESS;"
    "DATABASE=TaxiManagement;"
    "Trusted_Connection=yes;"
)

print("Kết nối SQL thành công")