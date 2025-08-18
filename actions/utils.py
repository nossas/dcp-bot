import requests
import os
import mimetypes
import json
import logging
import re
from typing import List, Dict
logger = logging.getLogger('actions')
logger.setLevel(logging.DEBUG) 
from datetime import datetime
def get_last_action(tracker, depth=1):
    last_action = None
    for event in reversed(tracker.events):
        if (event.get("event") == "action" and event.get("name") not in ["action_listen","action_repeat_last_message","action_fallback_buttons","action_agendar_inatividade"]):
            last_action = event.get("name")
            logger.debug(f"Last action:{last_action} depth:{depth}")
            if depth < 2: 
                logger.debug(f"Last action:{last_action} break:{depth}")
                break
            depth -= 1
    return last_action

def get_last_intent(tracker, depth=1):
    last_intent = None
    for event in reversed(tracker.events):
        if (event.get("event") == "intent" ):
            last_intent = event.get("name")
            logger.debug(f"Last intent:{last_intent} depth:{depth}")
            if depth < 2: 
                logger.debug(f"Last intent:{last_intent} break:{depth}")
                break
            depth -= 1
    return last_intent

def extrair_riscos(json_data: Dict) -> List[Dict]:
    riscos_extraidos = []
    logger.debug(f"Json data: {json_data}")

    for item in json_data.get("data", []):
        risco = {
            "id": item.get("id"),
            "data": item.get("timestamp"),
            "usuario_id": item.get("id_usuario"),
            "endereco": item.get("endereco"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "descricao": item.get("descricao"),
            "classificacao": [
                c.get("name") if isinstance(c, dict) else "Outros"
                for c in item.get("classificacao") if isinstance(item.get("classificacao"), list)
            ] if isinstance(item.get("classificacao"), list) else ["Outros"],
            "imagens": item.get("url_imagens", []),
            "videos": item.get("url_videos", []),
            "identificar": item.get("identificar", False)
        }
        riscos_extraidos.append(risco)

    return riscos_extraidos

def verificar_tipo_arquivo(caminho_arquivo):
    mime_type, _ = mimetypes.guess_type(caminho_arquivo)
    
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
    return "outro"



def enviar_risco_para_wordpress(
    endereco,
    descricao,
    midias_paths,
    latitude,
    longitude,
    nome_completo,
    email,
    telefone,
    autoriza_contato,
    classificacao,
):
    try:
        files = []
        for path in midias_paths:
            if os.path.exists(path):
                files.append(("media_files[]", open(path, "rb")))
            else:
                logger.debug(f"[WARN] Arquivo de mídia não encontrado: {path}")

        data = {
            "action": "form_single_risco_new",
            "endereco": endereco,
            "descricao": descricao,
            "nome_completo": nome_completo,
            "email": email,
            "latitude":latitude,
            "longitude":longitude,
            "telefone": telefone,
            "autoriza_contato": "true" if autoriza_contato else "false",
            "data_e_horario": __import__("datetime").datetime.utcnow().isoformat(),
            "situacao_de_risco": classificacao,
        }
        wordpress_url = os.getenv("WORDPRESS_URL")
        response = requests.post(
            f"{wordpress_url}/wp-admin/admin-ajax.php",
            data=data,
            files=files,
        )

        # Fechar arquivos após envio
        for _, file in files:
            file.close()

        if response.status_code != 200:
            logger.debug(f"[ERRO WP] Código HTTP: {response.status_code}")
            logger.debug(f"[ERRO WP] Resposta: {response.text}")
        else:
            logger.debug("[INFO] Risco enviado com sucesso para o WordPress.")
    except Exception as e:
        logger.debug(f"[ERRO] Falha ao enviar risco para WordPress: {e}")
        
        
def formata_data(data_str,formato = '%H:%M do dia %d/%m/%Y'):
    dt = datetime.fromisoformat(data_str)
    resultado = dt.strftime(formato)
    return resultado

def dentro_do_retangulo(lat, lng):
    #Restringe ao Jacarezinho, Rio de Janeiro
    # Coordenadas do retângulo delimitador
    
    X0, Y0 = -43.27, -22.87 
    X1, Y1 = -43.23, -22.91 
    return Y1 <= lat <= Y0 and X0 <= lng <= X1

def verifica_poligono(google_response):
    """
    Filtra os resultados da resposta do Google Maps, retornando apenas os que estão dentro do retângulo.
    """
    dados = google_response.json()
    resultados_filtrados = []

    for resultado in dados.get("results", []):
        location = resultado.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        if lat is not None and lng is not None and dentro_do_retangulo(lat, lng):
            resultados_filtrados.append(resultado)
    return resultados_filtrados    
    
def chamada_google_maps(*args, **kwargs):
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if kwargs.get("endereco"):
            args = f'?address={kwargs["endereco"]}'
        else:
            lat = kwargs.get("latitude")
            lng = kwargs.get("longitude")
            if lat is not None and lng is not None:
                args = f'?latlng={lat},{lng}'
            else:
                raise ValueError("Parâmetros insuficientes: é necessário 'endereco' ou 'latitude' e 'longitude'.")
        url = f"https://maps.googleapis.com/maps/api/geocode/json{args}&bounds=-22.91,-43.27|-22.87,-43.23&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Received data: {data}")
            if data["status"] == "OK":
                # logger.debug(f"Resposta do Google Maps (texto): {response.status_code} - {response.text}")
                response_filtered = verifica_poligono(response)
                return response_filtered
            else:
                logger.error(f"Erro na API do Google Maps: {data.get('status')}")
        else:
            logger.error("Erro HTTP na chamada à API do Google Maps")
            return False

def format_address(endereco):
    if not endereco:
        return ""
    """
    Formata o endereço para remover palavras irrelevantes, CEP, estado e país.
    """
    # Remove CEP (formato 5 dígitos - 3 dígitos)
    endereco = re.sub(r'\b\d{5}-\d{3}\b', '', endereco)
    # Remove país (Brazil ou Brasil)
    endereco = re.sub(r'\b(brazil|brasil)\b', '', endereco, flags=re.IGNORECASE)
    # Remove estado (ex: - RJ, RJ, - SP, SP, etc.)
    endereco = re.sub(r'-\s*[A-Z]{2}\b', '', endereco)
    endereco = re.sub(r'\b[A-Z]{2}\b', '', endereco)
    # Remove vírgulas e espaços extras
    # Remove vírgulas duplicadas ou triplicadas
    endereco = re.sub(r',\s*,+', ',', endereco)
    # Remove vírgulas no final da string (com ou sem espaços)
    endereco = re.sub(r',\s*$', '', endereco)
    endereco = re.sub(r'\s+', ' ', endereco).strip()
    return endereco

def get_endereco_latlong(latitude,longitude):
    response = chamada_google_maps(latitude=latitude,longitude=longitude )
    print(f"response do google maps:{response}")
    if response and len(response) > 0:
        resultado = response[0]
    else:
        resultado = {}
    endereco = format_address(resultado.get("formatted_address", ""))
    return endereco


def get_endereco_texto(endereco):
    logger.debug(f"Buscando endereço pelo texto: {endereco}")
    response = chamada_google_maps(endereco=endereco)
    print(f"response do google maps:{response}")
    if response and len(response) > 0:
        resultado = response[0]
        endereco = format_address(resultado.get("formatted_address", ""))
        lat = resultado["geometry"]["location"]["lat"] if "geometry" in resultado and "location" in resultado["geometry"] and "lat" in resultado["geometry"]["location"] else None
        lng = resultado["geometry"]["location"]["lng"] if "geometry" in resultado and "location" in resultado["geometry"] and "lng" in resultado["geometry"]["location"] else None
        resultado_dict = {'lat':lat,'lng':lng,'endereco':endereco}
    else:
        resultado_dict = {}
    return (resultado_dict)
    