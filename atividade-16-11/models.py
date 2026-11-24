"""Modelo de domínio da biblioteca e contratos públicos da API."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field as PydanticField
from pydantic import field_validator
from sqlmodel import Field, SQLModel


class LivroEntrada(SQLModel):
    model_config = {"extra": "forbid"}
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    ano_publicacao: int = Field(ge=1)
    exemplares: int = Field(ge=0, le=100000)

    @field_validator("titulo", "autor", mode="before")
    @classmethod
    def limpar_texto(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("ano_publicacao")
    @classmethod
    def validar_ano(cls, valor):
        if valor > datetime.now(UTC).year + 1:
            raise ValueError("O ano deve ser, no máximo, o próximo ano.")
        return valor


class Livro(LivroEntrada, table=True):
    id: int | None = Field(default=None, primary_key=True)


class LivroSaida(LivroEntrada):
    id: int


class UsuarioCadastro(SQLModel):
    model_config = {"extra": "forbid"}
    username: str = PydanticField(min_length=3, max_length=50, pattern=r"^[a-z0-9_.-]+$")
    senha: str = Field(min_length=6, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalizar_nome(cls, valor):
        return valor.strip().lower() if isinstance(valor, str) else valor


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    senha_hash: str
    role: str = "usuario"


class UsuarioSaida(SQLModel):
    id: int
    username: str
    role: str


class Perfil(UsuarioSaida):
    scopes: list[str]
    sessao_id: str


class Sessao(SQLModel, table=True):
    id: str = Field(primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    scopes: str
    ultima_atividade: int
    encerrada: bool = False


class RefreshToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sessao_id: str = Field(foreign_key="sessao.id", index=True)
    token_hash: str = Field(unique=True, index=True)
    expira_em: int
    revogado: bool = False


class RefreshEntrada(SQLModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class TokenResposta(SQLModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    refresh_expires_in: int
    session_idle_seconds: int
    usuario: Perfil


class AuditoriaSaida(SQLModel):
    id: int
    usuario: str
    operacao: str
    recurso: str
    recurso_id: int | None
    data_hora: datetime
    resultado: str
    detalhes: str | None


class LogAuditoria(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    usuario: str = Field(index=True)
    operacao: str
    recurso: str
    recurso_id: int | None = None
    data_hora: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resultado: str
    detalhes: str | None = None


class ControleInicializacao(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)


class ResumoAcervo(SQLModel):
    titulos: int
    exemplares: int
    autores: int


class Mensagem(SQLModel):
    mensagem: str
