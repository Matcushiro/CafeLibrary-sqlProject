DB_CONFIG = {
    "driver": "{ODBC Driver 17 for SQL Server}",
    "server": r"localhost\SQLEXPRESS",
    "database": "CafeLibrary",
    "trusted_connection": True,
    "uid": "",                       
    "pwd": "",
}

#Функция для сбора строки подключения к бд
def get_connection_string() -> str:
    parts = [
        f"DRIVER={DB_CONFIG['driver']}",
        f"SERVER={DB_CONFIG['server']}",
        f"DATABASE={DB_CONFIG['database']}",
    ]
    if DB_CONFIG["trusted_connection"]:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={DB_CONFIG['uid']}")
        parts.append(f"PWD={DB_CONFIG['pwd']}")
    return ";".join(parts) + ";"