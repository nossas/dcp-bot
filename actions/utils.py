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
        url = f"https://maps.googleapis.com/maps/api/geocode/json{args}&key={api_key}"
        response = requests.get(url)
        # logger.debug(f"Resposta do Google Maps (texto): {response.status_code} - {response.text}")
        return response
    
def get_endereco_latlong(latitude,longitude):
    response = chamada_google_maps(latitude=latitude,longitude=longitude )
    print(f"response do google maps:{response}")
    if response.status_code == 200:
        data = response.json()
        logger.debug(f"Received data: {data}")
        if data["status"] == "OK":
            resultado = data["results"][0]
            endereco = resultado.get("formatted_address", "Endereço não encontrado.")
            return endereco
        else:
            logger.error(f"Erro na API do Google Maps: {data.get('status')}")
    else:
        logger.error("Erro HTTP na chamada à API do Google Maps")
        return False


def get_endereco_texto(endereco):
    endereco_texto = re.sub(r'jacarezinho|jacare|rj|rio de janeiro', '', endereco, flags=re.IGNORECASE)            
    endereco_texto += ",bairro Jacarezinho, Rio de Janeiro, RJ"
    logger.debug(f"Buscando endereço pelo texto: {endereco_texto}")
    response = chamada_google_maps(endereco=endereco_texto)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            resultado = data["results"][0]
            endereco = resultado.get("formatted_address", "Endereço não encontrado.")
            lat = resultado["geometry"]["location"]["lat"]
            lng = resultado["geometry"]["location"]["lng"]        
            return ({'lat':lat,'lng':lng,'endereco':endereco})
    else:
        logger.error(f"Erro na API do Google Maps: {data.get('status')} - {data.get('error_message')}")
    return False            
    