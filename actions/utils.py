import mimetypes

def verificar_tipo_arquivo(caminho_arquivo):
    mime_type, _ = mimetypes.guess_type(caminho_arquivo)
    
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
    return "outro"