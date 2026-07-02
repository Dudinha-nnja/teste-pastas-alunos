import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://localhost/documentacao_alunos"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB por requisição de upload

    # Google Drive - Service Account (mesma credencial que você já usa no
    # projeto financeiro, só precisa garantir que o escopo do Drive esteja
    # habilitado para essa service account)
    GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")

    # ID da pasta raiz no Drive dentro da qual as pastas de curso/aluno
    # serão criadas. Pegue esse ID na URL da pasta no Google Drive.
    DRIVE_PASTA_RAIZ_ID = os.environ.get("DRIVE_PASTA_RAIZ_ID", "")
