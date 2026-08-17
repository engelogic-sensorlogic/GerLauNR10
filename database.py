"""
GerLauNR10 - Módulo de banco de dados SQLite
"""
import sqlite3
import os
import sys
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent

if getattr(sys, "frozen", False):
    # Rodando como executavel compilado (PyInstaller): a pasta de instalacao
    # (ex.: C:\Program Files (x86)\GerLauNR10) costuma ser somente leitura
    # para usuarios sem privilegio de administrador, entao os dados do
    # aplicativo (banco SQLite) ficam numa pasta gravavel do usuario.
    _DATA_ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "GerLauNR10"
else:
    _DATA_ROOT = BASE_DIR

DB_PATH = _DATA_ROOT / "data" / "gerlaunr10.db"

# ---------------------------------------------------------------------------
# Dados padrão do checklist (10 itens NR-10)
# ---------------------------------------------------------------------------
_OBS_OK = "Nenhuma ação necessária, painel atende ao requisito da norma."
_OBS_NA = "Elemento não presente ou não necessário neste tipo de painel."

CHECKLIST_DEFAULT = [
    {
        "numero": 1,
        "questao": "O painel possui chave seccionadora ou dispositivo de desligamento geral com recurso para bloqueio com cadeado?",
        "justificativa": "10.3.1 - É obrigatório que os projetos de instalações elétricas especifiquem dispositivos de desligamento de circuitos que possuam recursos para impedimento de reenergização, para sinalização de advertência com indicação da condição operativa.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "O painel deve ter a possibilidade de desligamento emergencial externo de forma rápida e eficaz, para ser utilizado em caso de emergência ou em procedimentos de operação e manutenção.",
             "Providenciar a instalação de dispositivo de seccionamento com opção de bloqueio externo por cadeado. Exemplo: chave seccionadora, chave LOTO, disjuntor geral com manopla de acionamento externa, chave seccionadora do tipo Pacco ou semelhantes."),
            ("Atende Parcial - Bloqueio", 0.5,
             "O painel deve ter a possibilidade de desligamento emergencial externo de forma rápida e eficaz, para ser utilizado em caso de emergência ou em procedimentos de operação e manutenção.",
             "Implementar recurso para bloqueio da operação do mecanismo, como instalação de porta-cadeado ou recurso semelhante, que impeça o usuário não autorizado de proceder com a manobra do dispositivo."),
            ("Atende Parcial - Indicador", 0.5,
             "O usuário deverá identificar de forma clara e objetiva a condição de energização do painel.",
             "Implementar sistema de indicação de estado de operação, por luz sinalizadora ou indicação visual gráfica (adesivos), para a correta identificação do estado atual do dispositivo: Ligado/Desligado, Aberto/Fechado, ou semelhantes."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 2,
        "questao": "Os disjuntores internos ao painel possuem alavanca com opção de bloqueio com cadeado e indicação de seu estado operacional?",
        "justificativa": "10.3.1 - É obrigatório que os projetos de instalações elétricas especifiquem dispositivos de desligamento de circuitos que possuam recursos para impedimento de reenergização.\n10.3.2 - O projeto elétrico deve prever a instalação de dispositivo de seccionamento de ação simultânea, que permita a aplicação de impedimento de reenergização do circuito.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Para operações de manutenção, o responsável deverá ter opções de seccionamento dos circuitos internos de forma individual, bem como realizar os bloqueios necessários para a execução de suas atividades de forma segura.",
             "Providenciar a instalação de dispositivo de bloqueio por cadeado nos disjuntores internos. Exemplo: acessórios mecânicos de bloqueio da haste ou alavanca de acionamento, ou a substituição do dispositivo por outro que possua tal recurso de bloqueio nativo."),
            ("Atende Parcial - Bloqueio", 0.5,
             "Para operações de manutenção, o responsável deverá ter opções de seccionamento dos circuitos internos de forma individual, bem como realizar os bloqueios necessários para a execução de suas atividades de forma segura.",
             "Implementar recurso para bloqueio da operação do mecanismo, como instalação de porta-cadeado ou recurso semelhante, que impeça o usuário não autorizado de proceder com a manobra do dispositivo."),
            ("Atende Parcial - Indicador", 0.5,
             "O usuário deverá identificar de forma clara e objetiva a condição de energização dos circuitos individuais internos do painel.",
             "Implementar sistema de indicação de estado de operação, com indicação visual gráfica (adesivos ou marcações), para a correta verificação do estado atual do dispositivo: Ligado/Desligado, Aberto/Fechado, ou semelhantes."),
            ("Atende Parcial - Dispositivos", 0.5,
             "Os disjuntores internos possuem parcialmente os recursos de bloqueio e indicação de estado exigidos, porém não de forma completa.",
             "Complementar os disjuntores com os dispositivos de bloqueio e indicação de estado faltantes, ou substituí-los por modelos que já possuam esses recursos nativamente."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 3,
        "questao": "O painel possui espaço suficiente no interior do cubículo para acomodar todos os componentes necessários à operação?",
        "justificativa": "10.3.3 - O projeto de instalações elétricas deve considerar o espaço seguro, quanto ao dimensionamento e a localização de seus componentes e as influências externas, quando da operação e da realização de serviços de construção e manutenção.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Devido ao alto risco de choque elétrico, os painéis devem ser mantidos organizados, limpos e sem improvisações de instalação.",
             "Providenciar a organização interna do painel para acomodação de todos os componentes de forma segura, fixados corretamente na placa de montagem ou nos trilhos, garantindo assim a segurança operacional do dispositivo. Se necessário, avaliar o retrofit do painel em questão."),
            ("Atende Parcial – Cabos desorganizados", 0.5,
             "Devido ao alto risco de choque elétrico, os painéis devem ser mantidos organizados, limpos e sem improvisações de instalação.",
             "Executar procedimento de manutenção corretiva para organização dos cabos no interior das canaletas ou baias de montagem, ajustando as tampas das canaletas ou adotando solução adequada para a correta fixação e proteção dos cabos."),
            ("Atende Parcial – Componentes Soltos", 0.5,
             "Devido ao alto risco de choque elétrico, os painéis devem ser mantidos organizados, limpos e sem improvisações de instalação.",
             "Executar procedimento de manutenção corretiva para fixação dos componentes nos trilhos ou na placa de montagem. O dispositivo deve estar fixado firmemente à infraestrutura, para garantia da segurança operacional e do correto aterramento funcional (se aplicável)."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 4,
        "questao": "As fiações internas ao painel possuem identificação na fiação por anilhas alfanuméricas ou por cor?",
        "justificativa": "10.3.3.1 - Os circuitos elétricos com finalidades diferentes, tais como: comunicação, sinalização, controle e tensão elétrica devem ser identificados e instalados separadamente.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Para evitar falhas de interpretação dos circuitos elétricos e mitigar possíveis falhas humanas que possam ocasionar acidentes nos processos de operação e manutenção, os circuitos devem estar identificados e documentados.",
             "Providenciar a identificação das fiações elétricas dos circuitos internos do painel, utilizando anilhas fixas com gravação legível do circuito específico, de acordo com o diagrama elétrico do painel. Sempre que possível, utilizar anilhas com proteção extra para a gravação (luvas ou recurso compatível). Caso seja adotada identificação dos circuitos por cores, essa codificação deve estar demonstrada no painel (etiqueta com a codificação ou documento visível), fixada em local de fácil visualização e compreensão."),
            ("Atende Parcial", 0.5,
             "Para evitar falhas de interpretação dos circuitos elétricos e mitigar possíveis falhas humanas que possam ocasionar acidentes nos processos de operação e manutenção, os circuitos devem estar identificados e documentados.",
             "Executar procedimento de manutenção corretiva para codificação dos condutores sem marcação, utilizando anilhas impressas do tipo luva ou anilhas do tipo inserção. Caso a identificação existente adote esquema de cores para os circuitos, a codificação deve seguir o padrão já existente, de acordo com o diagrama elétrico específico."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 5,
        "questao": "O painel elétrico, portas frontais, laterais, traseiras e placas de montagem estão interligadas ao sistema de aterramento?",
        "justificativa": "10.3.4 - O projeto deve definir a configuração do esquema de aterramento, a obrigatoriedade ou não da interligação entre o condutor neutro e o de proteção e a conexão à terra das partes condutoras não destinadas à condução da eletricidade.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Para evitar ou minimizar os riscos de choques elétricos aos usuários, todas as instalações elétricas energizadas devem possuir circuito de aterramento específico, equipotencializado com as demais infraestruturas eletromecânicas do local de instalação.",
             "Providenciar condutor de aterramento e a equipotencialização dos componentes internos ao ponto de aterramento: placa de montagem, porta frontal, portas laterais e porta traseira. O ponto de aterramento principal deve estar acessível para a condução de aterramentos temporários em caso de manutenção, e deve estar identificado pela cor verde ou verde-amarelo."),
            ("Porta não aterrada", 0.5,
             "Para evitar ou minimizar os riscos de choques elétricos aos usuários, todas as instalações elétricas energizadas devem possuir circuito de aterramento específico, equipotencializado com as demais infraestruturas eletromecânicas do local de instalação.",
             "Providenciar a equipotencialização da porta do painel ao ponto de aterramento, com condutor específico de diâmetro compatível ao nível de curto-circuito, identificado pela cor verde ou verde-amarelo."),
            ("Placa não aterrada", 0.5,
             "Para evitar ou minimizar os riscos de choques elétricos aos usuários, todas as instalações elétricas energizadas devem possuir circuito de aterramento específico, equipotencializado com as demais infraestruturas eletromecânicas do local de instalação.",
             "Providenciar a equipotencialização da placa de montagem ao ponto de aterramento, com condutor específico de diâmetro compatível ao nível de curto-circuito, identificado pela cor verde ou verde-amarelo."),
            ("Porta e placa não aterradas", 0.5,
             "Para evitar ou minimizar os riscos de choques elétricos aos usuários, todas as instalações elétricas energizadas devem possuir circuito de aterramento específico, equipotencializado com as demais infraestruturas eletromecânicas do local de instalação.",
             "Providenciar a equipotencialização das portas de acesso e da placa de montagem ao ponto de aterramento, com condutor específico de diâmetro compatível ao nível de curto-circuito, identificado pela cor verde ou verde-amarelo."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 6,
        "questao": "O painel elétrico possui diagrama elétrico atualizado em local de fácil acesso e consulta?",
        "justificativa": "10.3.7 - O projeto das instalações elétricas deve ficar à disposição dos trabalhadores autorizados, das autoridades competentes e de outras pessoas autorizadas pela empresa e deve ser mantido atualizado.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Todas as instalações elétricas devem possuir a documentação técnica necessária para os procedimentos de operação e manutenção.",
             "Providenciar a elaboração de documentação técnica que identifique de forma clara e legível os circuitos internos do painel. Esse diagrama deverá contemplar todos os circuitos internos ao painel, além de identificar os componentes de forma clara, com suas especificações técnicas."),
            ("Restrição no acesso", 0.5,
             "Diagrama elétrico existente, contudo não está disponível para a equipe de manutenção elétrica. O diagrama deve estar acessível a todos os responsáveis com permissão de acesso ao interior do painel.",
             "Providenciar cópia legível e atualizada do diagrama, em local de fácil acesso para a equipe de manutenção."),
            ("Má conservação", 0.5,
             "Diagrama elétrico existente, contudo mantido em más condições de conservação.",
             "Providenciar cópia legível e atualizada do diagrama."),
            ("Diagrama desatualizado", 0.5,
             "Diagrama elétrico existente, contudo a cópia disponível está desatualizada: o painel passou por melhorias ou aumento de circuitos e a documentação técnica não foi atualizada.",
             "Providenciar a atualização do diagrama elétrico do painel em questão."),
            ("Diagrama incompleto", 0.5,
             "Diagrama elétrico existente, contudo a cópia disponível está incompleta ou com páginas faltantes.",
             "Providenciar cópia legível e completa do diagrama."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 7,
        "questao": "O painel elétrico possui iluminação adequada e está localizado em local de fácil acesso com posição de trabalho segura?",
        "justificativa": "10.3.10 - Os projetos devem assegurar que as instalações proporcionem aos trabalhadores iluminação adequada e uma posição de trabalho segura, de acordo com a NR 17 - Ergonomia.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Os locais de trabalho e de acesso aos painéis elétricos deverão possuir livre acesso e iluminação adequada ao seu uso.",
             "O interior do painel e seus componentes devem estar visíveis mesmo em período noturno. O acesso ao painel deve estar livre e desobstruído, mantendo uma área de segurança de no mínimo 1,2 metros ao seu redor."),
            ("Atende parcial", 0.5,
             "Os locais de trabalho e de acesso aos painéis elétricos deverão possuir livre acesso e iluminação adequada ao seu uso.",
             "Providenciar iluminação adequada no interior do painel ou em seu entorno, e providenciar a liberação dos espaços de acesso ao painel e ao seu redor."),
            ("Atende parcial - Iluminação", 0.5,
             "Os locais de trabalho e de acesso aos painéis elétricos deverão possuir livre acesso e iluminação adequada ao seu uso.",
             "Providenciar iluminação adequada no interior do painel ou em seu entorno."),
            ("Atende parcial - Acesso", 0.5,
             "Os locais de trabalho e de acesso aos painéis elétricos deverão possuir livre acesso e iluminação adequada ao seu uso.",
             "Providenciar a liberação dos espaços de acesso ao painel e ao seu redor."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 8,
        "questao": "\"Partes vivas\" no interior do painel elétrico possuem barreiras que impeçam o contato acidental?",
        "justificativa": "10.2.8.2.1 - Na impossibilidade de implementação das medidas coletivas primárias, devem ser utilizadas outras medidas de proteção coletiva, tais como: isolação das partes vivas, obstáculos, barreiras, sinalização, sistema de seccionamento automático de alimentação.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "Os painéis elétricos devem ser projetados e construídos de forma a não proporcionar riscos adicionais aos usuários e às equipes de manutenção.",
             "Providenciar o isolamento das partes energizadas expostas no interior do painel."),
            ("Atende parcial", 0.5,
             "Alguns pontos energizados não possuem bloqueios contra o contato acidental.",
             "Providenciar o isolamento das partes energizadas expostas no interior do painel."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 9,
        "questao": "O painel possui etiquetas de identificação das tensões de força/comando e TAG do painel?",
        "justificativa": "10.3.9 - O memorial descritivo do projeto deve conter, no mínimo, os seguintes itens de segurança: especificação das características relativas à proteção contra choques elétricos; descrição do sistema de identificação de circuitos elétricos e equipamentos.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "O painel deve possuir indicações legíveis dos riscos pertinentes ao equipamento e informações técnicas aos usuários, visíveis a todos que estiverem próximos às áreas de instalação.",
             "Providenciar etiquetas de sinalização e identificação do painel: etiqueta com a inscrição da tensão máxima de operação, etiqueta de TAG de identificação do painel (número ou identificação no inventário de equipamentos do prontuário da NR-10) e etiqueta de advertência sobre os riscos de choque elétrico."),
            ("Atende Parcial – TAG", 0.5,
             "O painel deve possuir formas de identificação para controle e registro de manutenções, alterações e melhorias.",
             "Providenciar etiqueta de TAG de identificação do painel, com número ou identificação no inventário de equipamentos do prontuário da NR-10."),
            ("Atende Parcial – Força / Comando", 0.5,
             "O painel deve possuir indicações legíveis dos riscos pertinentes ao equipamento e informações técnicas aos usuários, visíveis a todos que estiverem próximos às áreas de instalação.",
             "Providenciar etiqueta da tensão máxima de operação e etiqueta de advertência sobre os riscos de choque elétrico."),
            ("Não avaliado", None, _OBS_NA, ""),
        ]
    },
    {
        "numero": 10,
        "questao": "O painel possui portas de acesso com dispositivo de bloqueio por cadeado que impeça a abertura por pessoal não qualificado?",
        "justificativa": "10.4.1 - As instalações elétricas devem ser construídas, montadas, operadas, reformadas, ampliadas, reparadas e inspecionadas de forma a garantir a segurança e a saúde dos trabalhadores.\n10.4.4.1 - Os locais de serviços elétricos, compartimentos e invólucros de equipamentos e instalações elétricas são exclusivos para essa finalidade.",
        "opcoes": [
            ("Sim", 1.0, _OBS_OK, ""),
            ("Não", 0.0,
             "O painel deve possuir recursos que impeçam sua abertura e acesso por pessoal não habilitado.",
             "Providenciar mecanismo que impeça a abertura e o acesso por pessoal não habilitado e/ou não autorizado: fecho ou tranca com bloqueio por cadeado, ou fechadura com abertura por chave específica, de posse dos responsáveis pelas ações de manutenção."),
            ("Atende parcial", 0.5,
             "O painel deve possuir recursos que impeçam sua abertura e acesso por pessoal não habilitado.",
             "Providenciar mecanismo que impeça a abertura e o acesso por pessoal não habilitado e/ou não autorizado: fecho ou tranca com bloqueio por cadeado, ou fechadura com abertura por chave específica, de posse dos responsáveis pelas ações de manutenção."),
            ("Não avaliado", None, _OBS_NA, ""),
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
            peso REAL,
            observacao_padrao TEXT,
            acao_corretiva_padrao TEXT
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

    # Migration: adiciona colunas de textos padrao de observacao/acao corretiva
    # nas opcoes do checklist, se nao existirem
    for col in ("observacao_padrao", "acao_corretiva_padrao"):
        try:
            conn.execute("ALTER TABLE checklist_opcoes ADD COLUMN %s TEXT" % col)
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
            for desc, peso, obs_pad, ac_pad in item["opcoes"]:
                c.execute(
                    """INSERT INTO checklist_opcoes
                       (item_id, descricao, peso, observacao_padrao, acao_corretiva_padrao)
                       VALUES (?,?,?,?,?)""",
                    (item_id, desc, peso, obs_pad, ac_pad)
                )
        conn.commit()
    else:
        # Backfill: bancos criados antes da existencia dos textos padrao tem
        # as opcoes do checklist ja populadas, mas sem observacao_padrao/
        # acao_corretiva_padrao. Preenche apenas onde ainda estiver vazio,
        # sem sobrescrever eventual customizacao feita pelo usuario.
        for item in CHECKLIST_DEFAULT:
            row = c.execute(
                "SELECT id FROM checklist_items WHERE numero=?", (item["numero"],)
            ).fetchone()
            if not row:
                continue
            item_id = row["id"]
            for desc, peso, obs_pad, ac_pad in item["opcoes"]:
                c.execute(
                    """UPDATE checklist_opcoes
                       SET observacao_padrao=COALESCE(NULLIF(observacao_padrao, ''), ?),
                           acao_corretiva_padrao=COALESCE(NULLIF(acao_corretiva_padrao, ''), ?)
                       WHERE item_id=? AND descricao=?
                         AND (observacao_padrao IS NULL OR observacao_padrao=''
                              OR acao_corretiva_padrao IS NULL OR acao_corretiva_padrao='')""",
                    (obs_pad, ac_pad, item_id, desc)
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


def sincronizar_participantes_laudo(laudo_id: int) -> int:
    """Garante que todos os participantes do cliente estejam vinculados ao laudo.

    O vinculo era feito uma unica vez, na criacao do laudo, com os participantes
    que existiam naquele instante -- quem fosse cadastrado depois nunca aparecia
    no item 1.3 nem na folha de assinaturas do PDF. Retorna quantos vinculos
    novos foram criados.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO laudo_participantes (laudo_id, participante_id)
                 SELECT ?, p.id FROM participantes p
                 JOIN laudos l ON l.cliente_id = p.cliente_id
                 WHERE l.id = ?""", (laudo_id, laudo_id))
    novos = c.rowcount
    conn.commit()
    conn.close()
    return novos


def participantes_do_laudo(laudo_id: int):
    conn = get_connection()
    rows = conn.execute("""SELECT p.* FROM participantes p
                           JOIN laudo_participantes lp ON lp.participante_id=p.id
                           WHERE lp.laudo_id=? ORDER BY p.id""", (laudo_id,)).fetchall()
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
    """Salva um item do checklist e suas opcoes.

    As opcoes sao atualizadas "no lugar" (casando pela descricao) em vez de
    apagar e recriar tudo -- avaliacoes ja registradas referenciam
    checklist_opcoes.id via FOREIGN KEY, entao recriar as opcoes quebraria
    essas avaliacoes (ou falharia com IntegrityError, ja que a FK impede
    apagar uma opcao ainda referenciada).
    """
    conn = get_connection()
    c = conn.cursor()
    if dados.get("id"):
        c.execute("""UPDATE checklist_items SET numero=?, questao=?, justificativa=?, ativo=?
                     WHERE id=?""",
                  (dados["numero"], dados["questao"], dados.get("justificativa"), dados.get("ativo", 1), dados["id"]))
        iid = dados["id"]
        existentes = c.execute(
            "SELECT id, descricao FROM checklist_opcoes WHERE item_id=?", (iid,)
        ).fetchall()
        existentes_por_desc = {row["descricao"]: row["id"] for row in existentes}
    else:
        c.execute("INSERT INTO checklist_items (numero, questao, justificativa) VALUES (?,?,?)",
                  (dados["numero"], dados["questao"], dados.get("justificativa")))
        iid = c.lastrowid
        existentes_por_desc = {}

    descricoes_novas = set()
    for opc in dados.get("opcoes", []):
        desc = opc["descricao"]
        descricoes_novas.add(desc)
        if desc in existentes_por_desc:
            c.execute(
                """UPDATE checklist_opcoes
                   SET peso=?, observacao_padrao=?, acao_corretiva_padrao=?
                   WHERE id=?""",
                (opc.get("peso"), opc.get("observacao_padrao"), opc.get("acao_corretiva_padrao"),
                 existentes_por_desc[desc]))
        else:
            c.execute(
                """INSERT INTO checklist_opcoes
                   (item_id, descricao, peso, observacao_padrao, acao_corretiva_padrao)
                   VALUES (?,?,?,?,?)""",
                (iid, desc, opc.get("peso"),
                 opc.get("observacao_padrao"), opc.get("acao_corretiva_padrao")))

    # Remove opcoes que nao estao mais na lista -- se alguma ja tiver
    # avaliacoes vinculadas, a FK impede a exclusao; nesse caso a opcao
    # antiga fica orfa (nao aparece mais no formulario, mas preserva o
    # historico de avaliacoes ja registradas).
    for desc, opc_id in existentes_por_desc.items():
        if desc not in descricoes_novas:
            try:
                c.execute("DELETE FROM checklist_opcoes WHERE id=?", (opc_id,))
            except sqlite3.IntegrityError:
                pass

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
