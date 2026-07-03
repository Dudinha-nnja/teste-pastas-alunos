from flask import Blueprint, current_app, jsonify, render_template, request

from models import db, Aluno, DocumentoEnviado
from services.capacitacao_generator import ModeloNaoEncontrado, gerar_pdf_capacitacao
from services.documentos_config import documentos_aplicaveis
from services.drive_client import DriveClient
from services.pdf_converter import documentos_para_pdf_unico, juntar_pdfs, sanitizar_nome

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/")
def formulario():
    return render_template("upload.html")


@upload_bp.route("/enviar", methods=["POST"])
def enviar():
    nome = request.form.get("nome", "").strip()
    curso = request.form.get("curso", "").strip()
    cpf = request.form.get("cpf", "").strip()
    sexo = request.form.get("sexo", "").strip()
    tipo_certidao = request.form.get("tipo_certidao", "").strip()
    rg_sem_cpf = request.form.get("rg_sem_cpf") == "on"

    if not nome or not curso or not sexo or not cpf:
        return jsonify({"erro": "Nome, curso, CPF e sexo são obrigatórios."}), 400

    respostas = {
        "sexo": sexo,
        "rg_tem_cpf": not rg_sem_cpf,
        "tipo_certidao": tipo_certidao,
    }
    obrigatorios = documentos_aplicaveis(respostas)

    # Valida que todos os arquivos exigidos por essas respostas realmente
    # vieram na requisição -- o front já faz isso, mas o backend não confia
    # cegamente no front.
    faltando = [doc.label for doc in obrigatorios if doc.id not in request.files]
    if faltando:
        return jsonify({"erro": f"Documentos faltando: {', '.join(faltando)}"}), 400

    aluno = Aluno(nome=nome, cpf=cpf, curso=curso, sexo=sexo)
    db.session.add(aluno)
    db.session.commit()

    # Junta as fotos de todos os documentos exigidos em um único PDF,
    # uma página por documento, na ordem em que aparecem em DOCUMENTOS.
    imagens = [request.files[doc.id].read() for doc in obrigatorios]
    pdf_documentos = documentos_para_pdf_unico(imagens)

    # Gera o certificado de capacitação preenchido com nome e CPF do aluno
    # a partir do modelo .docx do curso, e junta como páginas extras no
    # mesmo PDF -- se não existir modelo cadastrado pra esse curso, segue
    # o fluxo sem a capacitação (não trava o envio do aluno por isso).
    try:
        pdf_capacitacao = gerar_pdf_capacitacao(sanitizar_nome(curso), nome, cpf)
        pdf_bytes = juntar_pdfs([pdf_documentos, pdf_capacitacao])
    except ModeloNaoEncontrado:
        current_app.logger.warning(
            "Sem modelo de capacitação para o curso '%s' -- enviando só os documentos.",
            curso,
        )
        pdf_bytes = pdf_documentos

    drive = DriveClient(current_app.config["GOOGLE_CREDENTIALS_JSON"])

    # Pasta do curso (nivel 1) e, dentro dela, a pasta do aluno (nivel 2).
    # Se quiser SEM subpasta de curso, troque pasta_pai_id abaixo por
    # current_app.config["DRIVE_PASTA_RAIZ_ID"] diretamente.
    pasta_curso_id = drive.obter_ou_criar_pasta(
        sanitizar_nome(curso), current_app.config["DRIVE_PASTA_RAIZ_ID"]
    )
    pasta_aluno_id = drive.obter_ou_criar_pasta(
        sanitizar_nome(nome), pasta_curso_id
    )

    nome_arquivo = f"{sanitizar_nome(nome)}_{sanitizar_nome(curso)}.pdf"

    # Um único upload pro Drive, em vez de um por documento -- bem mais
    # rápido e evita o timeout que acontecia com 10 chamadas sequenciais.
    upload_resultado = drive.enviar_pdf(nome_arquivo, pdf_bytes, pasta_aluno_id)

    registro = DocumentoEnviado(
        aluno_id=aluno.id,
        tipo_documento="documentacao_completa",
        nome_arquivo=nome_arquivo,
        drive_file_id=upload_resultado["id"],
        drive_url=upload_resultado["url"],
    )
    db.session.add(registro)
    db.session.commit()

    return jsonify({"status": "ok", "aluno_id": aluno.id, "arquivo_enviado": nome_arquivo})
