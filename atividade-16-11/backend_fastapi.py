"""Biblioteca distribuída: adaptação do estudo de caso até a versão 9."""

import hashlib
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, NoReturn
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import event, func, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, col, create_engine, select

from models import (
    AuditoriaSaida,
    ControleInicializacao,
    Livro,
    LivroEntrada,
    LivroSaida,
    LogAuditoria,
    Mensagem,
    Perfil,
    RefreshEntrada,
    RefreshToken,
    ResumoAcervo,
    Sessao,
    TokenResposta,
    Usuario,
    UsuarioCadastro,
    UsuarioSaida,
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv(
    "JWT_SECRET", "chave-local-didatica-biblioteca-versao-9-troque-em-producao"
)
if len(SECRET_KEY.encode()) < 32:
    raise RuntimeError("JWT_SECRET deve ter pelo menos 32 bytes.")
ACCESS_SECONDS = 15 * 60
REFRESH_SECONDS = 7 * 24 * 60 * 60
IDLE_SECONDS = 30 * 60
SCOPES = {
    "livros:read": "Consultar o acervo",
    "livros:create": "Cadastrar livros",
    "livros:update": "Alterar livros",
    "livros:delete": "Excluir livros",
    "auditoria:read": "Consultar auditoria",
}
password_hash = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="token", scopes=SCOPES, auto_error=False)


def scopes_do_perfil(role: str) -> set[str]:
    if role == "admin":
        return set(SCOPES)
    if role == "usuario":
        return {"livros:read", "livros:create", "livros:update"}
    return set()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def auditar(
    db, usuario, operacao, recurso, resultado="sucesso", recurso_id=None, detalhes=None
):
    """A auditoria participa da mesma transação da operação principal."""
    db.add(
        LogAuditoria(
            usuario=usuario,
            operacao=operacao,
            recurso=recurso,
            resultado=resultado,
            recurso_id=recurso_id,
            detalhes=detalhes,
        )
    )


def negar(
    db: Session,
    usuario: str,
    operacao: str,
    recurso: str,
    detalhe: str,
    codigo: int = 401,
) -> NoReturn:
    auditar(db, usuario, operacao, recurso, "negado", detalhes=detalhe)
    db.commit()
    headers = {"WWW-Authenticate": "Bearer"} if codigo == 401 else None
    raise HTTPException(codigo, detalhe, headers=headers)


def encerrar_sessao(db, sessao):
    sessao.encerrada = True
    db.add(sessao)
    db.exec(
        update(RefreshToken)
        .where(col(RefreshToken.sessao_id) == sessao.id)
        .values(revogado=True)
    )


def create_app(database_url: str | None = None) -> FastAPI:
    """Uma instância independente permite testes com SQLite temporário."""
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        (BASE_DIR / "data").mkdir(exist_ok=True)
        url = f"sqlite:///{BASE_DIR / 'data' / 'biblioteca.db'}"
    engine = create_engine(
        url, connect_args={"check_same_thread": False, "timeout": 20}
    )

    @event.listens_for(engine, "connect")
    def configurar_sqlite(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

    @asynccontextmanager
    async def lifespan(app):
        SQLModel.metadata.create_all(engine)
        admin = UsuarioCadastro(
            username=os.getenv("ADMIN_USERNAME", "admin"),
            senha=os.getenv("ADMIN_INITIAL_PASSWORD", "admin123"),
        )
        with Session(engine) as db:
            if not db.exec(
                select(Usuario).where(Usuario.username == admin.username)
            ).first():
                db.add(
                    Usuario(
                        username=admin.username,
                        senha_hash=password_hash.hash(admin.senha),
                        role="admin",
                    )
                )
            # Marcador persistente impede recriar livros excluídos ao reiniciar.
            if db.get(ControleInicializacao, 1) is None:
                if os.getenv("SEED_DEMO", "1") == "1":
                    db.add_all(
                        [
                            Livro(
                                titulo="Dom Casmurro",
                                autor="Machado de Assis",
                                ano_publicacao=1899,
                                exemplares=4,
                            ),
                            Livro(
                                titulo="O Cortiço",
                                autor="Aluísio Azevedo",
                                ano_publicacao=1890,
                                exemplares=3,
                            ),
                            Livro(
                                titulo="Memórias Póstumas de Brás Cubas",
                                autor="Machado de Assis",
                                ano_publicacao=1881,
                                exemplares=2,
                            ),
                        ]
                    )
                db.add(ControleInicializacao())
            db.commit()
        yield
        engine.dispose()

    app = FastAPI(
        title="API da Biblioteca",
        version="9.0",
        lifespan=lifespan,
        description="Catálogo com OAuth2/JWT, scopes, refresh, sessões e auditoria.",
    )
    app.state.engine = engine

    def emitir_tokens(
        db: Session, usuario: Usuario, sessao: Sessao, scopes: set[str]
    ) -> TokenResposta:
        assert usuario.id is not None
        agora = int(time.time())
        refresh = secrets.token_urlsafe(64)
        db.add(
            RefreshToken(
                sessao_id=sessao.id,
                token_hash=hash_token(refresh),
                expira_em=agora + REFRESH_SECONDS,
            )
        )
        access = jwt.encode(
            {
                "sub": usuario.username,
                "sid": sessao.id,
                "role": usuario.role,
                "scope": " ".join(sorted(scopes)),
                "iat": agora,
                "exp": agora + ACCESS_SECONDS,
            },
            SECRET_KEY,
            algorithm="HS256",
        )
        return TokenResposta(
            access_token=access,
            refresh_token=refresh,
            expires_in=ACCESS_SECONDS,
            refresh_expires_in=REFRESH_SECONDS,
            session_idle_seconds=IDLE_SECONDS,
            usuario=Perfil(
                id=usuario.id,
                username=usuario.username,
                role=usuario.role,
                scopes=sorted(scopes),
                sessao_id=sessao.id,
            ),
        )

    def validar_sessao(
        db: Session,
        sessao: Sessao | None,
        usuario: Usuario | None,
        operacao: str,
        recurso: str,
    ) -> tuple[Sessao, Usuario]:
        agora = int(time.time())
        if sessao is None or sessao.encerrada or usuario is None:
            negar(
                db,
                usuario.username if usuario else "desconhecido",
                operacao,
                recurso,
                "Sessão encerrada ou inválida",
            )
        if agora - sessao.ultima_atividade >= IDLE_SECONDS:
            encerrar_sessao(db, sessao)
            negar(
                db,
                usuario.username,
                "SESSION_TIMEOUT",
                "sessao",
                "Sessão encerrada por inatividade",
            )
        ativo = db.exec(
            select(RefreshToken).where(
                col(RefreshToken.sessao_id) == sessao.id,
                col(RefreshToken.revogado).is_(False),
                col(RefreshToken.expira_em) > agora,
            )
        ).first()
        if ativo is None:
            encerrar_sessao(db, sessao)
            negar(db, usuario.username, operacao, recurso, "Sessão expirada")

        return sessao, usuario

    def obter_usuario(
        request: Request,
        security_scopes: SecurityScopes,
        token: Annotated[str | None, Depends(oauth2)],
    ):
        with Session(engine) as db:
            if not token:
                negar(
                    db,
                    "desconhecido",
                    request.method,
                    request.url.path,
                    "Token ausente",
                )
            try:
                payload = jwt.decode(
                    token,
                    SECRET_KEY,
                    algorithms=["HS256"],
                    options={"require": ["exp", "sub", "sid", "scope"]},
                )
                if not all(
                    isinstance(payload[k], str) for k in ("sub", "sid", "scope")
                ):
                    raise InvalidTokenError("Claims inválidos")
            except ExpiredSignatureError:
                # Expiração normal permite renovação sem registrar um ataque.
                raise HTTPException(
                    401, "Access token expirado", headers={"WWW-Authenticate": "Bearer"}
                )
            except InvalidTokenError:
                negar(
                    db,
                    "desconhecido",
                    request.method,
                    request.url.path,
                    "Token inválido",
                )
            sessao = db.get(Sessao, payload["sid"])
            usuario = db.get(Usuario, sessao.usuario_id) if sessao else None
            sessao, usuario = validar_sessao(
                db, sessao, usuario, request.method, request.url.path
            )
            if usuario.username != payload["sub"]:
                negar(
                    db,
                    "desconhecido",
                    request.method,
                    request.url.path,
                    "Token incompatível com a sessão",
                )
            scopes = (
                set(payload["scope"].split())
                & set(sessao.scopes.split())
                & scopes_do_perfil(usuario.role)
            )
            if not set(security_scopes.scopes) <= scopes:
                negar(
                    db,
                    usuario.username,
                    request.method,
                    request.url.path,
                    "Permissão insuficiente",
                    403,
                )
            sessao.ultima_atividade = int(time.time())
            db.add(sessao)
            db.commit()
            assert usuario.id is not None
            return Perfil(
                id=usuario.id,
                username=usuario.username,
                role=usuario.role,
                scopes=sorted(scopes),
                sessao_id=sessao.id,
            )

    @app.get("/", response_model=Mensagem)
    def status_api():
        return {"mensagem": "API da Biblioteca disponível — versão 9"}

    @app.post("/usuarios", response_model=UsuarioSaida, status_code=201)
    def cadastrar_usuario(dados: UsuarioCadastro):
        with Session(engine) as db:
            usuario = Usuario(
                username=dados.username, senha_hash=password_hash.hash(dados.senha)
            )
            try:
                db.add(usuario)
                db.flush()
                auditar(
                    db, usuario.username, "CREATE", "usuario", recurso_id=usuario.id
                )
                db.commit()
            except IntegrityError:
                db.rollback()
                negar(
                    db,
                    dados.username,
                    "CREATE",
                    "usuario",
                    "Usuário já cadastrado",
                    409,
                )
            db.refresh(usuario)
            return usuario

    @app.post("/token", response_model=TokenResposta)
    def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
        with Session(engine) as db:
            username = form.username.strip().lower()
            usuario = db.exec(
                select(Usuario).where(Usuario.username == username)
            ).first()
            if usuario is None or not password_hash.verify(
                form.password, usuario.senha_hash
            ):
                negar(
                    db,
                    username[:50] or "desconhecido",
                    "LOGIN",
                    "autenticacao",
                    "Usuário ou senha incorretos",
                )
            permitidos = scopes_do_perfil(usuario.role)
            scopes = set(form.scopes) if form.scopes else permitidos
            if not scopes <= permitidos:
                negar(
                    db,
                    usuario.username,
                    "LOGIN",
                    "autenticacao",
                    "Escopos não permitidos para este perfil",
                    400,
                )
            assert usuario.id is not None
            sessao = Sessao(
                id=uuid4().hex,
                usuario_id=usuario.id,
                scopes=" ".join(sorted(scopes)),
                ultima_atividade=int(time.time()),
            )
            db.add(sessao)
            db.flush()
            resposta = emitir_tokens(db, usuario, sessao, scopes)
            auditar(db, usuario.username, "LOGIN", "autenticacao")
            db.commit()
            return resposta

    @app.post("/refresh", response_model=TokenResposta)
    def renovar(dados: RefreshEntrada):
        with Session(engine) as db:
            registro = db.exec(
                select(RefreshToken).where(
                    RefreshToken.token_hash == hash_token(dados.refresh_token)
                )
            ).first()
            if registro is None:
                negar(
                    db,
                    "desconhecido",
                    "REFRESH",
                    "autenticacao",
                    "Refresh token inválido",
                )
            sessao = db.get(Sessao, registro.sessao_id)
            usuario = db.get(Usuario, sessao.usuario_id) if sessao else None
            nome = usuario.username if usuario else "desconhecido"
            if registro.revogado or registro.expira_em <= int(time.time()):
                negar(
                    db,
                    nome,
                    "REFRESH",
                    "autenticacao",
                    "Refresh token expirado ou já utilizado",
                )
            sessao, usuario = validar_sessao(
                db, sessao, usuario, "REFRESH", "autenticacao"
            )
            scopes = set(sessao.scopes.split()) & scopes_do_perfil(usuario.role)
            if not scopes:
                negar(
                    db,
                    nome,
                    "REFRESH",
                    "autenticacao",
                    "Nenhum escopo válido para renovar",
                )
            # Compare-and-set: somente uma requisição pode consumir o token.
            resultado = db.exec(
                update(RefreshToken)
                .where(
                    col(RefreshToken.id) == registro.id,
                    col(RefreshToken.revogado).is_(False),
                    col(RefreshToken.expira_em) > int(time.time()),
                )
                .values(revogado=True)
            )
            if resultado.rowcount != 1:
                db.rollback()
                negar(db, nome, "REFRESH", "autenticacao", "Refresh token já utilizado")
            sessao.ultima_atividade = int(time.time())
            sessao.scopes = " ".join(sorted(scopes))
            db.add(sessao)
            resposta = emitir_tokens(db, usuario, sessao, scopes)
            auditar(db, nome, "REFRESH", "autenticacao")
            db.commit()
            return resposta

    @app.post("/logout", response_model=Mensagem)
    def logout(dados: RefreshEntrada):
        with Session(engine) as db:
            registro = db.exec(
                select(RefreshToken).where(
                    RefreshToken.token_hash == hash_token(dados.refresh_token)
                )
            ).first()
            sessao = db.get(Sessao, registro.sessao_id) if registro else None
            usuario = db.get(Usuario, sessao.usuario_id) if sessao else None
            ativo = sessao is not None and not sessao.encerrada
            if ativo:
                encerrar_sessao(db, sessao)
            auditar(
                db,
                usuario.username if usuario else "desconhecido",
                "LOGOUT",
                "autenticacao",
                "sucesso" if ativo else "ignorado",
            )
            db.commit()
        return {"mensagem": "Logout realizado"}

    @app.get("/me", response_model=Perfil)
    def minha_conta(usuario: Annotated[Perfil, Security(obter_usuario, scopes=[])]):
        return usuario

    @app.get("/auditoria", response_model=list[AuditoriaSaida])
    def auditoria(
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["auditoria:read"])],
        limite: int = Query(100, ge=1, le=500),
    ):
        with Session(engine) as db:
            return db.exec(
                select(LogAuditoria).order_by(col(LogAuditoria.id).desc()).limit(limite)
            ).all()

    @app.get("/livros/resumo", response_model=ResumoAcervo)
    def resumo(
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["livros:read"])],
    ):
        with Session(engine) as db:
            titulos, exemplares, autores = db.exec(
                select(
                    func.count(col(Livro.id)),
                    func.coalesce(func.sum(col(Livro.exemplares)), 0),
                    func.count(func.distinct(col(Livro.autor))),
                )
            ).one()
            return ResumoAcervo(titulos=titulos, exemplares=exemplares, autores=autores)

    @app.get("/livros", response_model=list[LivroSaida])
    def listar(
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["livros:read"])],
        titulo: str | None = Query(None, max_length=200),
        autor: str | None = Query(None, max_length=150),
        min_exemplares: int | None = Query(None, ge=0),
    ):
        consulta = select(Livro)
        if titulo and titulo.strip():
            consulta = consulta.where(
                col(Livro.titulo).icontains(titulo.strip(), autoescape=True)
            )
        if autor and autor.strip():
            consulta = consulta.where(
                col(Livro.autor).icontains(autor.strip(), autoescape=True)
            )
        if min_exemplares is not None:
            consulta = consulta.where(col(Livro.exemplares) >= min_exemplares)
        with Session(engine) as db:
            return db.exec(consulta.order_by(col(Livro.id))).all()

    def buscar_livro(db, id_livro, usuario, operacao):
        livro = db.get(Livro, id_livro)
        if livro is None:
            auditar(
                db,
                usuario.username,
                operacao,
                "livro",
                "falha",
                id_livro,
                "Livro não encontrado",
            )
            db.commit()
            raise HTTPException(404, "Livro não encontrado")
        return livro

    @app.get("/livros/{id_livro}", response_model=LivroSaida)
    def consultar(
        id_livro: int,
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["livros:read"])],
    ):
        with Session(engine) as db:
            return buscar_livro(db, id_livro, usuario, "READ")

    @app.post("/livros", response_model=LivroSaida, status_code=201)
    def criar(
        dados: LivroEntrada,
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["livros:create"])],
    ):
        with Session(engine) as db:
            livro = Livro.model_validate(dados)
            db.add(livro)
            db.flush()
            auditar(
                db,
                usuario.username,
                "CREATE",
                "livro",
                recurso_id=livro.id,
                detalhes=livro.titulo,
            )
            db.commit()
            db.refresh(livro)
            return livro

    @app.put("/livros/{id_livro}", response_model=LivroSaida)
    def alterar(
        id_livro: int,
        dados: LivroEntrada,
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["livros:update"])],
    ):
        with Session(engine) as db:
            livro = buscar_livro(db, id_livro, usuario, "UPDATE")
            livro.sqlmodel_update(dados.model_dump())
            db.add(livro)
            auditar(
                db,
                usuario.username,
                "UPDATE",
                "livro",
                recurso_id=livro.id,
                detalhes=livro.titulo,
            )
            db.commit()
            db.refresh(livro)
            return livro

    @app.delete("/livros/{id_livro}", response_model=Mensagem)
    def excluir(
        id_livro: int,
        usuario: Annotated[Perfil, Security(obter_usuario, scopes=["livros:delete"])],
    ):
        with Session(engine) as db:
            livro = buscar_livro(db, id_livro, usuario, "DELETE")
            auditar(
                db,
                usuario.username,
                "DELETE",
                "livro",
                recurso_id=livro.id,
                detalhes=livro.titulo,
            )
            db.delete(livro)
            db.commit()
        return {"mensagem": f"Livro {id_livro} excluído"}

    return app


app = create_app()
