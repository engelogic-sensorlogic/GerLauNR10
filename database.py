"""
GerLauNR10 - Módulo de banco de dados SQLite
"""
import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "gerlaunr10.db"

# ---------------------------------------------------------------------------
# Dados padrão do checklist (10 itens NR-10)
# ---------------------------------------------------------------------------
CHECKLIST_DEFAULT = [
    {
        "numero": 1,
        "questao": "O painel possui chave seccionadora ou dispositivo de desligamento geral com recurso para bloqueio com cadeado?",
        "justificativa": "10.3.1 - É obrigatório que os projetos de instalações elétricas especifiquem dispositivos de desligamento de circuitos que possuam recursos para impedimento de reenergização, para sinalização de advertência com indicação da condição operativa.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende Parcial - Bloqueio", 0.5),
            ("Atende Parcial - Indicador", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 2,
        "questao": "Os disjuntores internos ao painel possuem alavanca com opção de bloqueio com cadeado e indicação de seu estado operacional?",
        "justificativa": "10.3.1 - É obrigatório que os projetos de instalações elétricas especifiquem dispositivos de desligamento de circuitos que possuam recursos para impedimento de reenergização.\n10.3.2 - O projeto elétrico deve prever a instalação de dispositivo de seccionamento de ação simultânea, que permita a aplicação de impedimento de reenergização do circuito.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende Parcial - Bloqueio", 0.5),
            ("Atende Parcial - Indicador", 0.5),
            ("Atende Parcial - Dispositivos", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 3,
        "questao": "O painel possui espaço suficiente no interior do cubículo para acomodar todos os componentes necessários à operação?",
        "justificativa": "10.3.3 - O projeto de instalações elétricas deve considerar o espaço seguro, quanto ao dimensionamento e a localização de seus componentes e as influências externas, quando da operação e da realização de serviços de construção e manutenção.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende Parcial – Cabos desorganizados", 0.5),
            ("Atende Parcial – Componentes Soltos", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 4,
        "questao": "As fiações internas ao painel possuem identificação na fiação por anilhas alfanuméricas ou por cor?",
        "justificativa": "10.3.3.1 - Os circuitos elétricos com finalidades diferentes, tais como: comunicação, sinalização, controle e tensão elétrica devem ser identificados e instalados separadamente.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende Parcial", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 5,
        "questao": "O painel elétrico, portas frontais, laterais, traseiras e placas de montagem estão interligadas ao sistema de aterramento?",
        "justificativa": "10.3.4 - O projeto deve definir a configuração do esquema de aterramento, a obrigatoriedade ou não da interligação entre o condutor neutro e o de proteção e a conexão à terra das partes condutoras não destinadas à condução da eletricidade.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Porta não aterrada", 0.5),
            ("Placa não aterrada", 0.5),
            ("Porta e placa não aterradas", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 6,
        "questao": "O painel elétrico possui diagrama elétrico atualizado em local de fácil acesso e consulta?",
        "justificativa": "10.3.7 - O projeto das instalações elétricas deve ficar à disposição dos trabalhadores autorizados, das autoridades competentes e de outras pessoas autorizadas pela empresa e deve ser mantido atualizado.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Restrição no acesso", 0.5),
            ("Má conservação", 0.5),
            ("Diagrama desatualizado", 0.5),
            ("Diagrama incompleto", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 7,
        "questao": "O painel elétrico possui iluminação adequada e está localizado em local de fácil acesso com posição de trabalho segura?",
        "justificativa": "10.3.10 - Os projetos devem assegurar que as instalações proporcionem aos trabalhadores iluminação adequada e uma posição de trabalho segura, de acordo com a NR 17 - Ergonomia.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende parcial", 0.5),
            ("Atende parcial - Iluminação", 0.5),
            ("Atende parcial - Acesso", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 8,
        "questao": "\"Partes vivas\" no interior do painel elétrico possuem barreiras que impeçam o contato acidental?",
        "justificativa": "10.2.8.2.1 - Na impossibilidade de implementação das medidas coletivas primárias, devem ser utilizadas outras medidas de proteção coletiva, tais como: isolação das partes vivas, obstáculos, barreiras, sinalização, sistema de seccionamento automático de alimentação.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende parcial", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 9,
        "questao": "O painel possui etiquetas de identificação das tensões de força/comando e TAG do painel?",
        "justificativa": "10.3.9 - O memorial descritivo do projeto deve conter, no mínimo, os seguintes itens de segurança: especificação das características relativas à proteção contra choques elétricos; descrição do sistema de identificação de circuitos elétricos e equipamentos.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende Parcial – TAG", 0.5),
            ("Atende Parcial – Força / Comando", 0.5),
            ("Não avaliado", None),
        ]
    },
    {
        "numero": 10,
        "questao": "O painel possui portas de acesso com dispositivo de bloqueio por cadeado que impeça a abertura por pessoal não qualificado?",
        "justificativa": "10.4.1 - As instalações elétricas devem ser construídas, montadas, operadas, reformadas, ampliadas, reparadas e inspecionadas de forma a garantir a segurança e a saúde dos trabalhadores.\n10.4.4.1 - Os locais de serviços elétricos, compartimentos e invólucros de equipamentos e instalações elétricas são exclusivos para essa finalidade.",
        "opcoes": [
            ("Sim", 1.0),
            ("Não", 0.0),
            ("Atende parcial", 0.5),
            ("Não avaliado", None),
        ]
    },
]


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria todas as tabelas e popula checklist padrão se necessário."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razao_social TEXT NOT NULL,
            cnpj TEXT,
            filial TEXT,
            endereco TEXT,
            cep TEXT,
            cidade TEXT,
            estado TEXT,
            telefone TEXT,
            logo_path TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            empresa TEXT,
            cargo TEXT,
            setor TEXT,
            email TEXT,
            telefone TEXT
        );

        CREATE TABLE IF NOT EXISTS profissionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            empresa TEXT,
            habilitacao TEXT,
            crea TEXT,
            email TEXT,
            telefone TEXT
        );

        CREATE TABLE IF NOT EXISTS laudos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
            numero TEXT,
            titulo TEXT,
            periodo_inicio TEXT,
            periodo_fim TEXT,
            cidade_laudo TEXT,
            art_pdf_path TEXT,
            conclusoes TEXT,
            consideracoes TEXT,
            status TEXT DEFAULT 'Em andamento',
            criado_em TEXT DEFAULT (datetime('now')),
            atualizado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS laudo_profissionais (
            laudo_id INTEGER NOT NULL REFERENCES laudos(id) ON DELETE CASCADE,
            profissional_id INTEGER NOT NULL REFERENCES profissionais(id) ON DELETE CASCADE,
            PRIMARY KEY (laudo_id, profissional_id)
        );

        CREATE TABLE IF NOT EXISTS laudo_participantes (
            laudo_id INTEGER NOT NULL REFERENCES laudos(id) ON DELETE CASCADE,
            participante_id INTEGER NOT NULL REFERENCES participantes(id) ON DELETE CASCADE,
            PRIMARY KEY (laudo_id, participante_id)
        );

        CREATE TABLE IF NOT EXISTS paineis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            laudo_id INTEGER NOT NULL REFERENCES laudos(id) ON DELETE CASCADE,
            formulario_num INTEGER,
            tag TEXT,
            setor TEXT,
            tipo_painel TEXT,
            tensao_forca TEXT,
            tensao_comando TEXT,
            num_fases TEXT,
            descricao TEXT,
            data_avaliacao TEXT,
            nivel_aderencia REAL DEFAULT 0.0,
            observacoes_gerais TEXT,
            foto_frontal TEXT,
            foto_lateral_dir TEXT,
            foto_lateral_esq TEXT,
            foto_traseira TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            painel_id INTEGER NOT NULL REFERENCES paineis(id) ON DELETE CASCADE,
            item_numero INTEGER NOT NULL,
            opcao_id INTEGER REFERENCES checklist_opcoes(id),
            peso REAL,
            observacoes TEXT,
            acao_corretiva TEXT,
            UNIQUE(painel_id, item_numero)
        );

        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            painel_id INTEGER NOT NULL REFERENCES paineis(id) ON DELETE CASCADE,
            item_numero INTEGER,
            caminho TEXT NOT NULL,
            legenda TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL UNIQUE,
            questao TEXT NOT NULL,
            justificativa TEXT,
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS checklist_opcoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES checklist_items(id) ON DELETE CASCADE,
            descricao TEXT NOT NULL,
            peso REAL
        );
    """)
    conn.commit()

    # Migration: adiciona colunas de fotos de identificacao se nao existirem
    for col, tipo in [
        ("foto_frontal", "TEXT"),
        ("foto_lateral_dir", "TEXT"),
        ("foto_lateral_esq", "TEXT"),
        ("foto_traseira", "TEXT"),
    ]:
        try:
            conn.execute("ALTER TABLE paineis ADD COLUMN %s %s" % (col, tipo))
            conn.commit()
        except Exception:
            pass  # coluna ja existe

    # Popula checklist padrão se vazio
    count = c.execute("SELECT COUNT(*) FROM checklist_items").fetchone()[0]
    if count == 0:
        for item in CHECKLIST_DEFAULT:
            c.execute(
                "INSERT INTO checklist_items (numero, questao, justificativa) VALUES (?,?,?)",
                (item["numero"], item["questao"], item["justificativa"])
            )
            item_id = c.lastrowid
            for desc, peso in item["opcoes"]:
                c.execute(
                    "INSERT INTO checklist_opcoes (item_id, descricao, peso) VALUES (?,?,?)",
                    (item_id, desc, peso)
                )
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# CLIENTES
# ---------------------------------------------------------------------------
def listar_clientes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM clientes ORDER BY razao_social").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_cliente(dados: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    if dados.get("id"):
        c.execute("""UPDATE clientes SET razao_social=?, cnpj=?, filial=?, endereco=?,
                     cep=?, cidade=?, estado=?, telefone=?, logo_path=?
                     WHERE id=?""",
                  (dados["razao_social"], dados.get("cnpj"), dados.get("filial"),
                   dados.get("endereco"), dados.get("cep"), dados.get("cidade"),
                   dados.get("estado"), dados.get("telefone"), dados.get("logo_path"),
                   dados["id"]))
        cid = dados["id"]
    else:
        c.execute("""INSERT INTO clientes (razao_social, cnpj, filial, endereco,
                     cep, cidade, estado, telefone, logo_path) VALUES (?,?,?,?,?,?,?,?,?)""",
                  (dados["razao_social"], dados.get("cnpj"), dados.get("filial"),
                   dados.get("endereco"), dados.get("cep"), dados.get("cidade"),
                   dados.get("estado"), dados.get("telefone"), dados.get("logo_path")))
        cid = c.lastrowid
    conn.commit()
    conn.close()
    return cid


def excluir_cliente(cliente_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    conn.commit()
    conn.close()


def buscar_cliente(cliente_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ---------------------------------------------------------------------------
# PARTICIPANTES
# ---------------------------------------------------------------------------
def listar_participantes(cliente_id: int):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM participantes WHERE cliente_id=? ORDER BY nome",
                        (cliente_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_participante(dados: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    if dados.get("id"):
        c.execute("""UPDATE participantes SET nome=?, empresa=?, cargo=?, setor=?,
                     email=?, telefone=? WHERE id=?""",
                  (dados["nome"], dados.get("empresa"), dados.get("cargo"),
                   dados.get("setor"), dados.get("email"), dados.get("telefone"),
                   dados["id"]))
        pid = dados["id"]
    else:
        c.execute("""INSERT INTO participantes (cliente_id, nome, empresa, cargo, setor, email, telefone)
                     VALUES (?,?,?,?,?,?,?)""",
                  (dados["cliente_id"], dados["nome"], dados.get("empresa"),
                   dados.get("cargo"), dados.get("setor"), dados.get("email"), dados.get("telefone")))
        pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def excluir_participante(pid: int):
    conn = get_connection()
    conn.execute("DELETE FROM participantes WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# PROFISSIONAIS
# ---------------------------------------------------------------------------
def listar_profissionais():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM profissionais ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_profissional(dados: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    if dados.get("id"):
        c.execute("""UPDATE profissionais SET nome=?, empresa=?, habilitacao=?,
                     crea=?, email=?, telefone=? WHERE id=?""",
                  (dados["nome"], dados.get("empresa"), dados.get("habilitacao"),
                   dados.get("crea"), dados.get("email"), dados.get("telefone"), dados["id"]))
        pid = dados["id"]
    else:
        c.execute("""INSERT INTO profissionais (nome, empresa, habilitacao, crea, email, telefone)
                     VALUES (?,?,?,?,?,?)""",
                  (dados["nome"], dados.get("empresa"), dados.get("habilitacao"),
                   dados.get("crea"), dados.get("email"), dados.get("telefone")))
        pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def excluir_profissional(pid: int):
    conn = get_connection()
    conn.execute("DELETE FROM profissionais WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# LAUDOS
# ---------------------------------------------------------------------------
def listar_laudos(cliente_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM laudos WHERE cliente_id=? ORDER BY criado_em DESC", (cliente_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_laudo(dados: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    if dados.get("id"):
        c.execute("""UPDATE laudos SET numero=?, titulo=?, periodo_inicio=?, periodo_fim=?,
                     cidade_laudo=?, art_pdf_path=?, conclusoes=?, consideracoes=?,
                     status=?, atualizado_em=? WHERE id=?""",
                  (dados.get("numero"), dados.get("titulo"), dados.get("periodo_inicio"),
                   dados.get("periodo_fim"), dados.get("cidade_laudo"), dados.get("art_pdf_path"),
                   dados.get("conclusoes"), dados.get("consideracoes"), dados.get("status", "Em andamento"),
                   now, dados["id"]))
        lid = dados["id"]
    else:
        c.execute("""INSERT INTO laudos (cliente_id, numero, titulo, periodo_inicio, periodo_fim,
                     cidade_laudo, art_pdf_path, conclusoes, consideracoes, status)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (dados["cliente_id"], dados.get("numero"), dados.get("titulo"),
                   dados.get("periodo_inicio"), dados.get("periodo_fim"),
                   dados.get("cidade_laudo"), dados.get("art_pdf_path"),
                   dados.get("conclusoes"), dados.get("consideracoes"),
                   dados.get("status", "Em andamento")))
        lid = c.lastrowid
    conn.commit()
    conn.close()
    return lid


def buscar_laudo(laudo_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM laudos WHERE id=?", (laudo_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def excluir_laudo(laudo_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM laudos WHERE id=?", (laudo_id,))
    conn.commit()
    conn.close()


def vincular_profissional_laudo(laudo_id: int, profissional_id: int):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO laudo_profissionais VALUES (?,?)",
                 (laudo_id, profissional_id))
    conn.commit()
    conn.close()


def desvincular_profissional_laudo(laudo_id: int, profissional_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM laudo_profissionais WHERE laudo_id=? AND profissional_id=?",
                 (laudo_id, profissional_id))
    conn.commit()
    conn.close()


def profissionais_do_laudo(laudo_id: int):
    conn = get_connection()
    rows = conn.execute("""SELECT p.* FROM profissionais p
                           JOIN laudo_profissionais lp ON lp.profissional_id=p.id
                           WHERE lp.laudo_id=?""", (laudo_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def vincular_participante_laudo(laudo_id: int, participante_id: int):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO laudo_participantes VALUES (?,?)",
                 (laudo_id, participante_id))
    conn.commit()
    conn.close()


def desvincular_participante_laudo(laudo_id: int, participante_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM laudo_participantes WHERE laudo_id=? AND participante_id=?",
                 (laudo_id, participante_id))
    conn.commit()
    conn.close()


def participantes_do_laudo(laudo_id: int):
    conn = get_connection()
    rows = conn.execute("""SELECT p.* FROM participantes p
                           JOIN laudo_participantes lp ON lp.participante_id=p.id
                           WHERE lp.laudo_id=?""", (laudo_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# PAINEIS
# ---------------------------------------------------------------------------
def listar_paineis(laudo_id: int):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM paineis WHERE laudo_id=? ORDER BY formulario_num",
                        (laudo_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_painel(dados: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    if dados.get("id"):
        atual = c.execute("SELECT nivel_aderencia, observacoes_gerais FROM paineis WHERE id=?",
                           (dados["id"],)).fetchone()
        nivel_aderencia = dados["nivel_aderencia"] if "nivel_aderencia" in dados \
            else (atual["nivel_aderencia"] if atual else 0.0)
        observacoes_gerais = dados["observacoes_gerais"] if "observacoes_gerais" in dados \
            else (atual["observacoes_gerais"] if atual else None)
        c.execute("""UPDATE paineis SET formulario_num=?, tag=?, setor=?, tipo_painel=?,
                     tensao_forca=?, tensao_comando=?, num_fases=?, descricao=?,
                     data_avaliacao=?, nivel_aderencia=?, observacoes_gerais=?
                     WHERE id=?""",
                  (dados.get("formulario_num"), dados.get("tag"), dados.get("setor"),
                   dados.get("tipo_painel"), dados.get("tensao_forca"), dados.get("tensao_comando"),
                   dados.get("num_fases"), dados.get("descricao"), dados.get("data_avaliacao"),
                   nivel_aderencia, observacoes_gerais, dados["id"]))
        pid = dados["id"]
    else:
        c.execute("""INSERT INTO paineis (laudo_id, formulario_num, tag, setor, tipo_painel,
                     tensao_forca, tensao_comando, num_fases, descricao, data_avaliacao,
                     nivel_aderencia, observacoes_gerais) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (dados["laudo_id"], dados.get("formulario_num"), dados.get("tag"),
                   dados.get("setor"), dados.get("tipo_painel"), dados.get("tensao_forca"),
                   dados.get("tensao_comando"), dados.get("num_fases"), dados.get("descricao"),
                   dados.get("data_avaliacao"), dados.get("nivel_aderencia", 0.0),
                   dados.get("observacoes_gerais")))
        pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def salvar_fotos_identificacao(painel_id: int, frontal: str = "", lateral_dir: str = "",
                                lateral_esq: str = "", traseira: str = ""):
    """Salva os caminhos das 4 fotos de identificacao visual do painel."""
    conn = get_connection()
    conn.execute("""UPDATE paineis SET foto_frontal=?, foto_lateral_dir=?,
                    foto_lateral_esq=?, foto_traseira=? WHERE id=?""",
                 (frontal or None, lateral_dir or None, lateral_esq or None,
                  traseira or None, painel_id))
    conn.commit()
    conn.close()


def buscar_fotos_identificacao(painel_id: int) -> dict:
    """Retorna dict com caminhos das fotos de identificacao do painel."""
    conn = get_connection()
    row = conn.execute(
        "SELECT foto_frontal, foto_lateral_dir, foto_lateral_esq, foto_traseira "
        "FROM paineis WHERE id=?", (painel_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {}
    return {
        "frontal":     row["foto_frontal"] or "",
        "lateral_dir": row["foto_lateral_dir"] or "",
        "lateral_esq": row["foto_lateral_esq"] or "",
        "traseira":    row["foto_traseira"] or "",
    }


def buscar_painel(painel_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM paineis WHERE id=?", (painel_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def excluir_painel(painel_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM paineis WHERE id=?", (painel_id,))
    conn.commit()
    conn.close()


def calcular_nivel_aderencia(painel_id: int) -> float:
    """Calcula o nível de aderência com base nas avaliações (exclui 'Não avaliado')."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT peso FROM avaliacoes WHERE painel_id=? AND peso IS NOT NULL",
        (painel_id,)
    ).fetchall()
    conn.close()
    if not rows:
        return 0.0
    total = sum(r["peso"] for r in rows)
    return round(total / len(rows), 4)


def atualizar_nivel_aderencia(painel_id: int):
    nivel = calcular_nivel_aderencia(painel_id)
    conn = get_connection()
    conn.execute("UPDATE paineis SET nivel_aderencia=? WHERE id=?", (nivel, painel_id))
    conn.commit()
    conn.close()
    return nivel


# ---------------------------------------------------------------------------
# AVALIAÇÕES
# ---------------------------------------------------------------------------
def listar_avaliacoes(painel_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM avaliacoes WHERE painel_id=? ORDER BY item_numero", (painel_id,)
    ).fetchall()
    conn.close()
    return {r["item_numero"]: dict(r) for r in rows}


def salvar_avaliacao(painel_id: int, item_numero: int, opcao_id, peso, observacoes: str, acao_corretiva: str):
    conn = get_connection()
    conn.execute("""INSERT INTO avaliacoes (painel_id, item_numero, opcao_id, peso, observacoes, acao_corretiva)
                    VALUES (?,?,?,?,?,?)
                    ON CONFLICT(painel_id, item_numero) DO UPDATE SET
                    opcao_id=excluded.opcao_id, peso=excluded.peso,
                    observacoes=excluded.observacoes, acao_corretiva=excluded.acao_corretiva""",
                 (painel_id, item_numero, opcao_id, peso, observacoes, acao_corretiva))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# FOTOS
# ---------------------------------------------------------------------------
def listar_fotos(painel_id: int, item_numero: int = None):
    conn = get_connection()
    if item_numero is not None:
        rows = conn.execute(
            "SELECT * FROM fotos WHERE painel_id=? AND item_numero=?", (painel_id, item_numero)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM fotos WHERE painel_id=? ORDER BY item_numero", (painel_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_foto(painel_id: int, item_numero: int, caminho: str, legenda: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO fotos (painel_id, item_numero, caminho, legenda) VALUES (?,?,?,?)",
              (painel_id, item_numero, caminho, legenda))
    fid = c.lastrowid
    conn.commit()
    conn.close()
    return fid


def excluir_foto(foto_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM fotos WHERE id=?", (foto_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# CHECKLIST ITEMS
# ---------------------------------------------------------------------------
def listar_checklist_items():
    conn = get_connection()
    items = conn.execute(
        "SELECT * FROM checklist_items WHERE ativo=1 ORDER BY numero"
    ).fetchall()
    result = []
    for item in items:
        opcoes = conn.execute(
            "SELECT * FROM checklist_opcoes WHERE item_id=?", (item["id"],)
        ).fetchall()
        d = dict(item)
        d["opcoes"] = [dict(o) for o in opcoes]
        result.append(d)
    conn.close()
    return result


def salvar_checklist_item(dados: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    if dados.get("id"):
        c.execute("""UPDATE checklist_items SET numero=?, questao=?, justificativa=?, ativo=?
                     WHERE id=?""",
                  (dados["numero"], dados["questao"], dados.get("justificativa"), dados.get("ativo", 1), dados["id"]))
        iid = dados["id"]
        # Recria opções
        c.execute("DELETE FROM checklist_opcoes WHERE item_id=?", (iid,))
    else:
        c.execute("INSERT INTO checklist_items (numero, questao, justificativa) VALUES (?,?,?)",
                  (dados["numero"], dados["questao"], dados.get("justificativa")))
        iid = c.lastrowid
    for opc in dados.get("opcoes", []):
        c.execute("INSERT INTO checklist_opcoes (item_id, descricao, peso) VALUES (?,?,?)",
                  (iid, opc["descricao"], opc.get("peso")))
    conn.commit()
    conn.close()
    return iid


# ---------------------------------------------------------------------------
# ESTATÍSTICAS
# ---------------------------------------------------------------------------
def estatisticas_laudo(laudo_id: int) -> dict:
    """Retorna dados consolidados para gráficos do laudo."""
    conn = get_connection()
    paineis = conn.execute(
        "SELECT id, tag, setor, nivel_aderencia FROM paineis WHERE laudo_id=?", (laudo_id,)
    ).fetchall()

    items = conn.execute(
        "SELECT numero, questao FROM checklist_items WHERE ativo=1 ORDER BY numero"
    ).fetchall()

    # Por item: média dos pesos (excluindo None)
    item_stats = {}
    for item in items:
        num = item["numero"]
        rows = conn.execute("""
            SELECT a.peso FROM avaliacoes a
            JOIN paineis p ON p.id=a.painel_id
            WHERE p.laudo_id=? AND a.item_numero=? AND a.peso IS NOT NULL
        """, (laudo_id, num)).fetchall()
        if rows:
            scores = [r["peso"] for r in rows]
            item_stats[num] = {
                "questao": item["questao"],
                "media": sum(scores) / len(scores),
                "contagens": {
                    "Sim": sum(1 for s in scores if s == 1.0),
                    "Parcial": sum(1 for s in scores if 0 < s < 1.0),
                    "Não": sum(1 for s in scores if s == 0.0),
                }
            }
        else:
            item_stats[num] = {"questao": item["questao"], "media": 0.0, "contagens": {}}

    conn.close()
    return {
        "paineis": [dict(p) for p in paineis],
        "item_stats": item_stats,
        "total_paineis": len(paineis),
        "media_geral": (
            sum((p["nivel_aderencia"] or 0.0) for p in paineis) / len(paineis) if paineis else 0.0
        )
    }
