import requests

endereco = "Rua Paese, 198, Videira, SC, Brazil"

parameters = {
    'address': endereco,
    'key': 'AIzaSyBsbsxRz3S-0jMX17RB6-CbtjNHgH4qCxk'
}

base = 'https://maps.googleapis.com/maps/api/geocode/json'
response = requests.get(base, params=parameters)
answer = response.json()

print(f"Endereço: {endereco}")
print(f"Status da API: {answer.get('status')}")

# Tratamento de erro
if answer['status'] == 'OK' and len(answer['results']) > 0:
    location = answer['results'][0]['geometry']['location']
    print(f"Lat: {location['lat']}, Lng: {location['lng']}")
else:
    print("Erro: Nenhum resultado encontrado ou falha na API.")
    print(f"Detalhes: {answer}")
