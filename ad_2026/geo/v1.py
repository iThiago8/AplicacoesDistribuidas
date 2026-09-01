from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderServiceError

endereco = "Rua Paese, 198, Videira, SC, Brazil"

# user_agent deve ser único para identificar seu aplicativo
locator = Nominatim(user_agent="teste_script_geo_v1")

try:
    print(f"Buscando endereço: {endereco}")

    # Realiza a geocodificação
    local = locator.geocode(endereco)

    # Verifica se o resultado existe (pode ser None se não encontrar)
    if local:
        print(f"Endereço Formatado: {local.address}")
        print(f"Latitude = {local.latitude}")
        print(f"Longitude = {local.longitude}")
    else:
        print("Erro: Nenhum resultado encontrado para este endereço.")
except GeocoderUnavailable:
    print("Erro: O serviço de geocodificação está indisponível no momento.")
except GeocoderServiceError as e:
    print(f"Erro no serviço: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
