"""
Converte a imagem enviada pelo aluno em um PDF.

Usa img2pdf para a conversão da imagem em si, porque ele não recomprime
a imagem (ao contrário do Pillow), preservando a qualidade da foto do
documento -- importante pra manter o texto legível.
"""

import io
import re
import unicodedata

import img2pdf
from PIL import Image


def sanitizar_nome(texto: str) -> str:
    """
    Remove acentos, espaços e caracteres especiais para gerar nomes de
    arquivo seguros. Ex: "João Silva" -> "joao-silva"
    """
    texto_sem_acento = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    )
    texto_limpo = re.sub(r"[^a-zA-Z0-9]+", "-", texto_sem_acento).strip("-").lower()
    return texto_limpo


def imagem_para_pdf(imagem_bytes: bytes) -> bytes:
    """
    Recebe os bytes de uma imagem (jpg/png/etc, incluindo fotos tiradas
    direto da câmera do celular) e devolve os bytes de um PDF de 1 página.

    Faz uma normalização prévia com Pillow (corrige orientação EXIF de
    fotos de celular, converte para RGB) antes de passar pro img2pdf,
    porque img2pdf é estrito quanto ao formato de entrada.
    """
    imagem = Image.open(io.BytesIO(imagem_bytes))

    # Corrige rotação automática de fotos tiradas com celular (muito comum
    # a imagem vir "deitada" nos metadados EXIF sem isso).
    try:
        from PIL import ImageOps

        imagem = ImageOps.exif_transpose(imagem)
    except Exception:
        pass

    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")

    buffer_imagem = io.BytesIO()
    imagem.save(buffer_imagem, format="JPEG", quality=90)
    buffer_imagem.seek(0)

    pdf_bytes = img2pdf.convert(buffer_imagem.read())
    return pdf_bytes
