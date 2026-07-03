from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(20), nullable=True)
    curso = db.Column(db.String(200), nullable=False)
    sexo = db.Column(db.String(20), nullable=True)  # usado na regra do reservista
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    documentos = db.relationship("DocumentoEnviado", backref="aluno", lazy=True)


class DocumentoEnviado(db.Model):
    __tablename__ = "documentos_enviados"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)

    tipo_documento = db.Column(db.String(50), nullable=False)  # ex: "rg_frente"
    nome_arquivo = db.Column(db.String(300), nullable=False)
    drive_file_id = db.Column(db.String(200), nullable=True)
    drive_url = db.Column(db.String(500), nullable=True)

    status = db.Column(db.String(20), default="enviado")  # enviado / aprovado / rejeitado
    enviado_em = db.Column(db.DateTime, default=datetime.utcnow)
