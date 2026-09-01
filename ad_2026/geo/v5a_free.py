# -*- coding: utf-8 -*-
import streamlit as st
import folium
import sys
import asyncio
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderServiceError
# ATUALIZAÇÃO REQUERIDA: Importando o componente moderno st_folium
from streamlit_folium import st_folium

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def geocode(endereco):
    locator = Nominatim(user_agent="app_geo_streamlit_moderno_2026")
    try:
        local = locator.geocode(endereco)
        return local
    except (GeocoderUnavailable, GeocoderServiceError) as e:
        st.error(f"Erro no serviço de geocodificação: {e}")
        return None


# Configuração limpa da página
st.set_page_config(page_title="Geocodificação Python", layout="wide")

st.title("📍 Painel de Geocodificação Interativo (Versão Atualizada)")
st.markdown("Insira um endereço para gerar as coordenadas geoespaciais e o mapa local.")

# Estado de sessão para persistência
if "local_data" not in st.session_state:
    st.session_state.local_data = None

# Entrada de texto padrão direta no corpo da página
endereco = st.text_input(
    "Endereço para pesquisa:",
    value="Rua Paese, 198, Videira, SC, Brazil"
)

if st.button("Procurar Endereço"):
    if not endereco:
        st.warning("Por favor, digite um endereço.")
    else:
        with st.spinner('Consultando servidores cartográficos...'):
            local = geocode(endereco)
            if local:
                st.session_state.local_data = {
                    "lat": local.latitude,
                    "lon": local.longitude,
                    "address": local.address
                }
            else:
                st.session_state.local_data = None
                st.error("❌ Endereço não localizado.")

# --- COMPONENTES DINÂMICOS: SÓ EXIBE SE O ENDEREÇO FOR ENCONTRADO ---
if st.session_state.local_data:
    data = st.session_state.local_data

    st.success(f"**Endereço Oficial:** {data['address']}")

    col_controle, col_vazia = st.columns([1, 2])

    with col_controle:
        zoom_selecionado = st.slider(
            "Aproximação do Mapa (Zoom):",
            min_value=1,
            max_value=18,
            value=16,
            help="Arraste para aproximar ou afastar a visualização das ruas."
        )

    # Inicializa a estrutura do mapa aplicando o valor dinâmico do slider
    m = folium.Map(
        location=[data['lat'], data['lon']],
        zoom_start=zoom_selecionado,
        tiles=None
    )

    # Camada 1: Satélite (Google) com links corrigidos
    folium.TileLayer(
        tiles='http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satélite',
        name='Visualização por Satélite',
        max_zoom=20,
        subdomains=['mt0', 'mt1', 'mt2', 'mt3']
    ).add_to(m)

    # Camada 2: Vetorial (Google Maps Padrão)
    folium.TileLayer(
        tiles='http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Mapa de Ruas',
        max_zoom=20,
        subdomains=['mt0', 'mt1', 'mt2', 'mt3']
    ).add_to(m)

    # Camada 3: Radar Atmosférico WMS do Nexrad (Imagens de Nuvem e Chuva)
    folium.raster_layers.WmsTileLayer(
        url='http://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0r.cgi',
        name='Radar de Chuva (Tempo Real)',
        fmt='image/png',
        layers='nexrad-n0r-900913',
        attr='Weather data © IEM Nexrad',
        transparent=True,
        overlay=True,
        control=True,
        opacity=0.65
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Adiciona o alfinete de marcação no mapa
    folium.Marker(
        location=[data['lat'], data['lon']],
        popup=f"<b>Coordenadas:</b><br>{data['lat']}, {data['lon']}",
        tooltip="Clique para ver dados do ponto",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # RENDIMENTO MODERNO: st_folium substitui o folium_static obsoleto
    # O parâmentro returned_objects=[] evita recarregamentos infinitos ao clicar no mapa
    st_folium(m, width=950, height=550, returned_objects=[])
