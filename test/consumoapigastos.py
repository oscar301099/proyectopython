
import requests
import matplotlib.pyplot as plt
from datetime import datetime


# Reemplaza con tu URL real de GraphQL
GRAPHQL_ENDPOINT = "http://localhost:3000/api/graphql"

# Tu consulta GraphQL
query = """
query GetGastos {
  gastos {
    id
    descripcion
    monto
    fecha
  }
}
"""

# Hacer la petición
response = requests.post(GRAPHQL_ENDPOINT, json={'query': query})

# Verificar respuesta
if response.status_code == 200:
    data = response.json()
    gastos = data["data"]["gastos"]

    # Ordenar por fecha y preparar datos
    fechas = [datetime.strptime(g["fecha"], "%Y-%m-%dT%H:%M:%S.%fZ") for g in gastos]
    montos = [g["monto"] for g in gastos]

    # Mostrar gráfica
    plt.figure(figsize=(10, 5))
    plt.plot(fechas, montos, marker='o')
    plt.title("Gastos por Fecha")
    plt.xlabel("Fecha")
    plt.ylabel("Monto")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("gastos.png")
    plt.show()

else:
    print("Error al consultar la API:", response.status_code)
    print(response.text)
