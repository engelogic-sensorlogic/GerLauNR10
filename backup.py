"""
GerLauNR10 - Exportacao e importacao de dados (backup e transferencia)

Um pacote e um arquivo .gnr10 -- um ZIP contendo:

    manifest.json   metadados: formato, versao, tipo, data, resumo do conteudo
    dados.json      os registros exportados
    fotos/          as imagens referenciadas pelos registros

As fotos viajam dentro do pacote porque o banco guarda caminhos absolutos
(ex.: D:/Imagens/Paineis/foto.jpg) que nao existem na maquina de destino. Na
importacao elas sao gravadas em data/fotos/ e os caminhos sao reescritos.

Dois escopos:

    cliente   o cliente, seus participantes, laudos, paineis, avaliacoes e fotos
    painel    um unico painel com checklist e fotos, para ser anexado a um
              laudo existente na maquina de destino

O escopo "painel" e o mesmo formato que um aplicativo de campo (celular)
precisaria gerar: ele descreve um painel completo sem depender de nenhum id do
banco de origem.
"""
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import database as db

FORMATO = "gerlaunr10-backup"
VERSAO = 1
EXTENSAO = ".gnr10"

# O checklist vai para o aplicativo de campo (celular) como JSON puro, nao como
# pacote ZIP: nao ha imagens envolvidas e assim o app o le direto, sem precisar
# descompactar nada.
FORMATO_CHECKLIST = "gerlaunr10-checklist"
EXTENSAO_CHECKLIST = ".json"

FOTOS_DIR = db.DB_PATH.parent / "fotos"

# Colunas copiadas de cada tabela. Ids nunca sao exportados: o destino gera os
# seus proprios e as ligacoes sao refeitas por conteudo.
_CAMPOS_CLIENTE = ["razao_social", "cnpj", "filial", "endereco", "cep",
                   "cidade", "estado", "telefone"]
_CAMPOS_PARTICIPANTE = ["nome", "empresa", "cargo", "setor", "email", "telefone"]
_CAMPOS_PROFISSIONAL = ["nome", "empresa", "habilitacao", "crea", "email", "telefone"]
_CAMPOS_LAUDO = ["numero", "titulo", "periodo_inicio", "periodo_fim", "cidade_laudo",
                 "conclusoes", "consideracoes", "status"]
_CAMPOS_PAINEL = ["formulario_num", "tag", "setor", "tipo_painel", "tensao_forca",
                  "tensao_comando", "num_fases", "descricao", "data_avaliacao",
                  "nivel_aderencia", "observacoes_gerais"]

_ANGULOS = ["frontal", "lateral_dir", "lateral_esq", "traseira"]


class BackupErro(Exception):
    """Falha ao ler ou gravar um pacote."""


def _somente(d: dict, campos: list) -> dict:
    return {c: d.get(c) for c in campos}


# ---------------------------------------------------------------------------
# Coleta de fotos
# ---------------------------------------------------------------------------
class _ColetorFotos:
    """Acumula as imagens que irao para dentro do pacote.

    Deduplica por hash do conteudo: a mesma foto usada em varios itens entra
    uma unica vez no ZIP.
    """

    def __init__(self):
        self._por_origem = {}   # caminho absoluto -> nome dentro do pacote
        self._por_hash = {}     # hash -> nome dentro do pacote
        self.ausentes = []      # caminhos que nao existem mais no disco

    def adicionar(self, caminho: str) -> str:
        """Registra a foto e devolve o nome dela dentro do pacote ("" se falhar)."""
        if not caminho:
            return ""
        if caminho in self._por_origem:
            return self._por_origem[caminho]
        if not os.path.exists(caminho):
            self.ausentes.append(caminho)
            return ""
        try:
            with open(caminho, "rb") as fh:
                conteudo = fh.read()
        except OSError:
            self.ausentes.append(caminho)
            return ""
        digest = hashlib.sha1(conteudo).hexdigest()[:16]
        if digest in self._por_hash:
            nome = self._por_hash[digest]
        else:
            nome = "fotos/%s%s" % (digest, os.path.splitext(caminho)[1].lower() or ".jpg")
            self._por_hash[digest] = nome
        self._por_origem[caminho] = nome
        return nome

    def gravar(self, zf: zipfile.ZipFile):
        gravados = set()
        for origem, nome in self._por_origem.items():
            if nome in gravados:
                continue
            gravados.add(nome)
            zf.write(origem, nome)

    @property
    def total(self) -> int:
        return len(set(self._por_origem.values()))


# ---------------------------------------------------------------------------
# Serializacao de um painel
# ---------------------------------------------------------------------------
def _painel_para_dict(painel: dict, fotos: _ColetorFotos, itens_por_id: dict) -> dict:
    """Converte um painel do banco no formato do pacote.

    As avaliacoes NAO guardam opcao_id: esse id e local do banco de origem e nao
    corresponderia a nada no destino. Guardamos o numero do item e a descricao da
    opcao escolhida, que sao reconciliados na importacao.
    """
    dados = _somente(painel, _CAMPOS_PAINEL)

    dados["fotos_identificacao"] = {}
    ident = db.buscar_fotos_identificacao(painel["id"]) or {}
    for ang in _ANGULOS:
        dados["fotos_identificacao"][ang] = fotos.adicionar(ident.get(ang, ""))

    avaliacoes = []
    for item_numero, aval in sorted(db.listar_avaliacoes(painel["id"]).items()):
        opc = itens_por_id.get(aval.get("opcao_id")) or {}
        avaliacoes.append({
            "item_numero": item_numero,
            "opcao_descricao": opc.get("descricao", ""),
            "peso": aval.get("peso"),
            "observacoes": aval.get("observacoes"),
            "acao_corretiva": aval.get("acao_corretiva"),
        })
    dados["avaliacoes"] = avaliacoes

    evidencias = []
    for f in db.listar_fotos(painel["id"]):
        nome = fotos.adicionar(f.get("caminho", ""))
        if nome:
            evidencias.append({
                "item_numero": f.get("item_numero"),
                "arquivo": nome,
                "legenda": f.get("legenda") or "",
            })
    dados["evidencias"] = evidencias
    return dados


def _mapa_opcoes() -> dict:
    """opcao_id -> {item_numero, descricao}, para traduzir avaliacoes na exportacao."""
    mapa = {}
    for item in db.listar_checklist_items():
        for opc in item["opcoes"]:
            mapa[opc["id"]] = {"item_numero": item["numero"], "descricao": opc["descricao"]}
    return mapa


def _gravar_pacote(destino: str, tipo: str, dados: dict, fotos: _ColetorFotos,
                   resumo: dict) -> dict:
    manifest = {
        "formato": FORMATO,
        "versao": VERSAO,
        "tipo": tipo,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "aplicativo": "GerLauNR10",
        "resumo": resumo,
    }
    destino = str(destino)
    os.makedirs(os.path.dirname(os.path.abspath(destino)) or ".", exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("dados.json", json.dumps(dados, ensure_ascii=False, indent=2))
        fotos.gravar(zf)
    resultado = dict(resumo)
    resultado["arquivo"] = destino
    resultado["fotos"] = fotos.total
    resultado["fotos_ausentes"] = list(fotos.ausentes)
    resultado["tamanho"] = os.path.getsize(destino)
    return resultado


# ---------------------------------------------------------------------------
# Exportacao
# ---------------------------------------------------------------------------
def exportar_cliente(cliente_id: int, destino: str) -> dict:
    """Grava um pacote com o cliente e tudo que pende dele."""
    cliente = db.buscar_cliente(cliente_id)
    if not cliente:
        raise BackupErro("Cliente %s nao encontrado." % cliente_id)

    fotos = _ColetorFotos()
    itens_por_id = _mapa_opcoes()

    dados = {
        "cliente": _somente(cliente, _CAMPOS_CLIENTE),
        "participantes": [_somente(p, _CAMPOS_PARTICIPANTE)
                          for p in db.listar_participantes(cliente_id)],
        "laudos": [],
    }
    dados["cliente"]["logo"] = fotos.adicionar(cliente.get("logo_path") or "")

    n_paineis = 0
    for laudo in db.listar_laudos(cliente_id):
        item = _somente(laudo, _CAMPOS_LAUDO)
        item["art"] = fotos.adicionar(laudo.get("art_pdf_path") or "")
        item["profissionais"] = [_somente(p, _CAMPOS_PROFISSIONAL)
                                 for p in db.profissionais_do_laudo(laudo["id"])]
        item["participantes"] = [p.get("nome") for p in db.participantes_do_laudo(laudo["id"])]
        item["paineis"] = [_painel_para_dict(p, fotos, itens_por_id)
                           for p in db.listar_paineis(laudo["id"])]
        n_paineis += len(item["paineis"])
        dados["laudos"].append(item)

    resumo = {
        "cliente": cliente.get("razao_social", ""),
        "laudos": len(dados["laudos"]),
        "paineis": n_paineis,
    }
    return _gravar_pacote(destino, "cliente", dados, fotos, resumo)


def exportar_painel(painel_id: int, destino: str) -> dict:
    """Grava um pacote com um unico painel, para anexar a um laudo no destino."""
    painel = db.buscar_painel(painel_id)
    if not painel:
        raise BackupErro("Painel %s nao encontrado." % painel_id)

    laudo = db.buscar_laudo(painel["laudo_id"]) or {}
    cliente = db.buscar_cliente(laudo.get("cliente_id")) if laudo.get("cliente_id") else {}

    fotos = _ColetorFotos()
    dados = {
        "painel": _painel_para_dict(painel, fotos, _mapa_opcoes()),
        # apenas informativo: ajuda o operador a confirmar o destino na importacao
        "origem": {
            "cliente": (cliente or {}).get("razao_social", ""),
            "laudo": laudo.get("numero") or laudo.get("titulo") or "",
        },
    }
    resumo = {
        "painel": painel.get("tag") or "(sem TAG)",
        "cliente": (cliente or {}).get("razao_social", ""),
        "avaliacoes": len(dados["painel"]["avaliacoes"]),
    }
    return _gravar_pacote(destino, "painel", dados, fotos, resumo)


# ---------------------------------------------------------------------------
# Checklist (para o aplicativo de campo)
# ---------------------------------------------------------------------------
def exportar_checklist(destino: str) -> dict:
    """Grava o checklist ativo em JSON, para carregar no aplicativo de campo.

    Leva so o que o tecnico precisa ver na tela para responder: o numero do
    item, a pergunta e as opcoes de resposta. Pesos, textos da norma e
    recomendacoes ficam de fora de proposito -- o aplicativo de campo apenas
    coleta, e todo o processamento acontece no PC, que resolve peso e textos
    padrao na importacao a partir do proprio checklist.

    Como as respostas trafegam pela descricao da opcao, o checklist do
    aparelho precisa ser o mesmo do PC: exporte de novo sempre que edita-lo.
    """
    itens = []
    for item in db.listar_checklist_items():
        itens.append({
            "numero": item["numero"],
            "questao": item["questao"],
            "opcoes": [o["descricao"] for o in item["opcoes"]],
        })

    dados = {
        "formato": FORMATO_CHECKLIST,
        "versao": VERSAO,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "itens": itens,
    }
    destino = str(destino)
    os.makedirs(os.path.dirname(os.path.abspath(destino)) or ".", exist_ok=True)
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=2)
    return {
        "arquivo": destino,
        "itens": len(itens),
        "opcoes": sum(len(i["opcoes"]) for i in itens),
        "tamanho": os.path.getsize(destino),
    }


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def ler_manifest(arquivo: str) -> dict:
    """Le o manifest de um pacote sem importar nada. Valida formato e versao."""
    try:
        with zipfile.ZipFile(arquivo) as zf:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, OSError) as e:
        raise BackupErro("Arquivo invalido ou nao e um pacote GerLauNR10.\n\n%s" % e)
    if manifest.get("formato") != FORMATO:
        raise BackupErro("Este arquivo nao e um pacote do GerLauNR10.")
    if manifest.get("versao", 0) > VERSAO:
        raise BackupErro(
            "O pacote foi gerado por uma versao mais nova do aplicativo "
            "(formato %s, suportado ate %s)." % (manifest.get("versao"), VERSAO))
    return manifest


# ---------------------------------------------------------------------------
# Importacao
# ---------------------------------------------------------------------------
def _extrair_foto(zf: zipfile.ZipFile, nome: str, pasta: Path) -> str:
    """Extrai uma imagem do pacote para a pasta de dados e devolve o caminho final."""
    if not nome:
        return ""
    try:
        info = zf.getinfo(nome)
    except KeyError:
        return ""
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / os.path.basename(nome)
    if not destino.exists():
        with zf.open(info) as origem, open(destino, "wb") as saida:
            shutil.copyfileobj(origem, saida)
    return str(destino)


def _mapa_descricoes() -> dict:
    """(item_numero, descricao) -> dados da opcao no checklist local.

    O checklist do PC e a autoridade sobre peso e textos padrao. Um pacote vindo
    do aplicativo de campo traz apenas a opcao escolhida; o peso e as
    recomendacoes sao resolvidos aqui, no momento da importacao.
    """
    mapa = {}
    for item in db.listar_checklist_items():
        for opc in item["opcoes"]:
            mapa[(item["numero"], opc["descricao"])] = {
                "id": opc["id"],
                "peso": opc["peso"],
                "observacao_padrao": opc.get("observacao_padrao") or "",
                "acao_corretiva_padrao": opc.get("acao_corretiva_padrao") or "",
            }
    return mapa


def _formularios_usados(laudo_id: int) -> set:
    return {p.get("formulario_num") for p in db.listar_paineis(laudo_id)
            if p.get("formulario_num") is not None}


def _proximo_formulario(usados: set) -> int:
    """Menor numero livre a partir de 1 (reaproveita buracos na numeracao)."""
    n = 1
    while n in usados:
        n += 1
    return n


def painel_existente_por_tag(laudo_id: int, tag: str):
    """Devolve o painel do laudo com a mesma TAG, ou None."""
    if not tag:
        return None
    alvo = tag.strip().casefold()
    for p in db.listar_paineis(laudo_id):
        if (p.get("tag") or "").strip().casefold() == alvo:
            return p
    return None


def _importar_painel_dict(pdados: dict, laudo_id: int, zf: zipfile.ZipFile,
                          opcoes: dict, relatorio: dict, usados: set = None,
                          modo: str = "novo") -> int:
    """Importa um painel.

    O numero do formulario vem do banco de origem e quase sempre ja esta ocupado
    no destino -- importar sem tratar gerava dois paineis com o mesmo "Nº Form"
    dentro do mesmo laudo. Com modo="novo" o painel recebe o proximo numero
    livre; com modo="substituir" o painel de mesma TAG e removido e o novo
    assume o numero que era dele.
    """
    if usados is None:
        usados = _formularios_usados(laudo_id)

    novo = _somente(pdados, _CAMPOS_PAINEL)
    novo["laudo_id"] = laudo_id
    tag = novo.get("tag") or ""
    original = novo.get("formulario_num")

    anterior = painel_existente_por_tag(laudo_id, tag) if modo == "substituir" else None
    if anterior is not None:
        # Assume a vaga do painel substituido, inclusive o numero do formulario
        novo["formulario_num"] = anterior.get("formulario_num") or original
        db.excluir_painel(anterior["id"])
        usados.discard(anterior.get("formulario_num"))
        relatorio["substituidos"].append(tag or "(sem TAG)")
    elif original is None or original in usados:
        novo["formulario_num"] = _proximo_formulario(usados)
        if original is not None:
            relatorio["renumerados"].append((tag or "(sem TAG)", original,
                                             novo["formulario_num"]))
    usados.add(novo["formulario_num"])

    painel_id = db.salvar_painel(novo)

    pasta = FOTOS_DIR / ("painel_%d" % painel_id)

    ident = pdados.get("fotos_identificacao") or {}
    caminhos = {ang: _extrair_foto(zf, ident.get(ang, ""), pasta) for ang in _ANGULOS}
    if any(caminhos.values()):
        db.salvar_fotos_identificacao(painel_id, caminhos["frontal"], caminhos["lateral_dir"],
                                      caminhos["lateral_esq"], caminhos["traseira"])

    for aval in pdados.get("avaliacoes", []):
        chave = (aval.get("item_numero"), aval.get("opcao_descricao") or "")
        opc = opcoes.get(chave)
        obs = (aval.get("observacoes") or "").strip()
        acao = (aval.get("acao_corretiva") or "").strip()

        if opc is None:
            if aval.get("opcao_descricao"):
                # O checklist local nao tem essa opcao (foi editada ou removida).
                # O peso e os textos do pacote sao preservados para nao perder a
                # avaliacao, mas a opcao fica sem vinculo.
                relatorio["opcoes_nao_encontradas"].append(
                    "Item %s: %s" % (aval.get("item_numero"), aval.get("opcao_descricao")))
            opcao_id, peso = None, aval.get("peso")
        else:
            # O checklist do PC e a autoridade: peso e recomendacoes saem dele,
            # nao do pacote. Assim o aplicativo de campo so precisa registrar a
            # opcao escolhida -- nao carrega pesos nem textos da norma.
            opcao_id, peso = opc["id"], opc["peso"]
            if not obs:
                obs = opc["observacao_padrao"]
            if not acao:
                acao = opc["acao_corretiva_padrao"]

        db.salvar_avaliacao(painel_id, aval.get("item_numero"), opcao_id,
                            peso, obs, acao)

    for ev in pdados.get("evidencias", []):
        caminho = _extrair_foto(zf, ev.get("arquivo", ""), pasta)
        if caminho:
            db.adicionar_foto(painel_id, ev.get("item_numero"), caminho, ev.get("legenda") or "")

    db.atualizar_nivel_aderencia(painel_id)
    relatorio["paineis"] += 1
    return painel_id


def _novo_relatorio() -> dict:
    return {"clientes": 0, "laudos": 0, "paineis": 0, "opcoes_nao_encontradas": [],
            "renumerados": [], "substituidos": [],
            "laudos_renomeados": [], "laudos_substituidos": []}


# ---------------------------------------------------------------------------
# Deteccao de conflitos (chamada pela interface antes de importar)
# ---------------------------------------------------------------------------
def conflito_painel(arquivo: str, laudo_id: int) -> dict:
    """Verifica se o painel do pacote colide com algum ja existente no laudo.

    Devolve {} quando nao ha colisao; caso contrario, o que colide e o numero
    que o painel receberia se for importado como novo.
    """
    manifest = ler_manifest(arquivo)
    if manifest.get("tipo") != "painel":
        raise BackupErro("Este pacote e do tipo '%s'." % manifest.get("tipo"))
    with zipfile.ZipFile(arquivo) as zf:
        pdados = (json.loads(zf.read("dados.json").decode("utf-8")).get("painel") or {})
    tag = pdados.get("tag") or ""
    anterior = painel_existente_por_tag(laudo_id, tag)
    usados = _formularios_usados(laudo_id)
    numero = pdados.get("formulario_num")
    if anterior is None and numero is not None and numero not in usados:
        return {}
    return {
        "tag": tag,
        "tag_existente": anterior is not None,
        "formulario_origem": numero,
        "formulario_existente": (anterior or {}).get("formulario_num"),
        "formulario_sugerido": _proximo_formulario(usados),
    }


def conflito_paineis(arquivo: str, laudo_id: int) -> list:
    """Paineis de um pacote "paineis" cuja TAG ja existe no laudo.

    Devolve [(tag, nº form do painel existente), ...]; lista vazia = sem colisao.
    O Nº Form nao entra na conta: o aplicativo de campo nao numera os paineis
    e o PC atribui os numeros livres na importacao.
    """
    manifest = ler_manifest(arquivo)
    if manifest.get("tipo") != "paineis":
        raise BackupErro("Este pacote e do tipo '%s'." % manifest.get("tipo"))
    with zipfile.ZipFile(arquivo) as zf:
        lista = json.loads(zf.read("dados.json").decode("utf-8")).get("paineis") or []
    repetidos = []
    for pdados in lista:
        anterior = painel_existente_por_tag(laudo_id, pdados.get("tag") or "")
        if anterior is not None:
            repetidos.append((pdados.get("tag"), anterior.get("formulario_num")))
    return repetidos


def conflito_cliente(arquivo: str, cliente_id_destino: int) -> list:
    """Numeros de laudo do pacote que ja existem no cliente de destino."""
    manifest = ler_manifest(arquivo)
    if manifest.get("tipo") != "cliente":
        raise BackupErro("Este pacote e do tipo '%s'." % manifest.get("tipo"))
    if not cliente_id_destino:
        return []
    existentes = {(l.get("numero") or "").strip().casefold(): l
                  for l in db.listar_laudos(cliente_id_destino)}
    with zipfile.ZipFile(arquivo) as zf:
        dados = json.loads(zf.read("dados.json").decode("utf-8"))
    return [l.get("numero") for l in dados.get("laudos", [])
            if (l.get("numero") or "").strip().casefold() in existentes]


def _numero_laudo_livre(cliente_id: int, numero: str) -> str:
    """Acrescenta um sufixo ao numero do laudo ate ele ficar unico no cliente."""
    usados = {(l.get("numero") or "").strip().casefold()
              for l in db.listar_laudos(cliente_id)}
    if (numero or "").strip().casefold() not in usados:
        return numero
    n = 2
    while ("%s (%d)" % (numero, n)).strip().casefold() in usados:
        n += 1
    return "%s (%d)" % (numero, n)


def importar_cliente(arquivo: str, cliente_id_destino: int = None,
                     modo: str = "novo") -> dict:
    """Importa um pacote de cliente.

    Com cliente_id_destino, os laudos entram nesse cliente ja cadastrado. Sem
    ele, um novo cliente e criado.

    modo="novo"        laudos de numero repetido recebem sufixo "(2)", "(3)"...
    modo="substituir"  o laudo de mesmo numero e removido antes, com todos os
                       seus paineis e avaliacoes, e o do pacote toma o lugar.
    """
    manifest = ler_manifest(arquivo)
    if manifest.get("tipo") != "cliente":
        raise BackupErro("Este pacote e do tipo '%s'. Use a importacao correspondente."
                         % manifest.get("tipo"))

    relatorio = _novo_relatorio()
    opcoes = _mapa_descricoes()

    with zipfile.ZipFile(arquivo) as zf:
        dados = json.loads(zf.read("dados.json").decode("utf-8"))
        cli = dados.get("cliente") or {}

        if cliente_id_destino:
            cliente_id = cliente_id_destino
        else:
            novo = _somente(cli, _CAMPOS_CLIENTE)
            cliente_id = db.salvar_cliente(novo)
            relatorio["clientes"] = 1
            logo = _extrair_foto(zf, cli.get("logo", ""), FOTOS_DIR / ("cliente_%d" % cliente_id))
            if logo:
                novo["id"] = cliente_id
                novo["logo_path"] = logo
                db.salvar_cliente(novo)

        # Participantes: casados por nome para nao duplicar em cliente existente
        ja_existem = {p["nome"] for p in db.listar_participantes(cliente_id)}
        for part in dados.get("participantes", []):
            if part.get("nome") in ja_existem:
                continue
            novo_part = dict(part)
            novo_part["cliente_id"] = cliente_id
            db.salvar_participante(novo_part)

        # Profissionais sao globais: reaproveitados por CREA (ou nome)
        locais = db.listar_profissionais()
        por_crea = {p.get("crea"): p["id"] for p in locais if p.get("crea")}
        por_nome = {p.get("nome"): p["id"] for p in locais}

        for laudo in dados.get("laudos", []):
            novo_laudo = _somente(laudo, _CAMPOS_LAUDO)
            novo_laudo["cliente_id"] = cliente_id

            # Laudo de mesmo numero ja no cliente: substitui ou desambigua
            numero = novo_laudo.get("numero") or ""
            existente = next(
                (l for l in db.listar_laudos(cliente_id)
                 if (l.get("numero") or "").strip().casefold() == numero.strip().casefold()
                 and numero.strip()), None)
            if existente is not None:
                if modo == "substituir":
                    db.excluir_laudo(existente["id"])
                    relatorio["laudos_substituidos"].append(numero)
                else:
                    novo_laudo["numero"] = _numero_laudo_livre(cliente_id, numero)
                    relatorio["laudos_renomeados"].append((numero, novo_laudo["numero"]))

            laudo_id = db.salvar_laudo(novo_laudo)
            relatorio["laudos"] += 1

            art = _extrair_foto(zf, laudo.get("art", ""), FOTOS_DIR / ("laudo_%d" % laudo_id))
            if art:
                novo_laudo["id"] = laudo_id
                novo_laudo["art_pdf_path"] = art
                db.salvar_laudo(novo_laudo)

            for prof in laudo.get("profissionais", []):
                pid = por_crea.get(prof.get("crea")) or por_nome.get(prof.get("nome"))
                if pid is None:
                    pid = db.salvar_profissional(dict(prof))
                    if prof.get("crea"):
                        por_crea[prof["crea"]] = pid
                    por_nome[prof.get("nome")] = pid
                db.vincular_profissional_laudo(laudo_id, pid)

            # Pacotes trazem, por laudo, o nome dos fornecedores indicados nele.
            # Pacotes antigos nao trazem: ai todos os do cliente sao vinculados,
            # como era antes.
            if "participantes" in laudo:
                por_nome_part = {p["nome"]: p["id"] for p in db.listar_participantes(cliente_id)}
                for nome in laudo.get("participantes") or []:
                    if nome in por_nome_part:
                        db.vincular_participante_laudo(laudo_id, por_nome_part[nome])
            else:
                db.sincronizar_participantes_laudo(laudo_id)

            # Um unico conjunto de numeros por laudo, para que os paineis do
            # pacote tambem nao colidam entre si.
            usados = _formularios_usados(laudo_id)
            for pdados in laudo.get("paineis", []):
                _importar_painel_dict(pdados, laudo_id, zf, opcoes, relatorio, usados)

    return relatorio


def importar_painel(arquivo: str, laudo_id: int, modo: str = "novo") -> dict:
    """Importa um pacote de painel para dentro de um laudo existente.

    modo="novo"        o painel entra com o proximo Nº Form livre do laudo
    modo="substituir"  o painel de mesma TAG e removido e o novo toma o lugar
    """
    manifest = ler_manifest(arquivo)
    if manifest.get("tipo") != "painel":
        raise BackupErro("Este pacote e do tipo '%s'. Use a importacao correspondente."
                         % manifest.get("tipo"))
    if not db.buscar_laudo(laudo_id):
        raise BackupErro("Laudo de destino nao encontrado.")

    relatorio = _novo_relatorio()
    with zipfile.ZipFile(arquivo) as zf:
        dados = json.loads(zf.read("dados.json").decode("utf-8"))
        _importar_painel_dict(dados.get("painel") or {}, laudo_id, zf,
                              _mapa_descricoes(), relatorio, modo=modo)
    return relatorio


def importar_paineis(arquivo: str, laudo_id: int, modo: str = "novo") -> dict:
    """Importa um pacote com varios paineis (gerado pelo aplicativo de campo)
    para dentro de um laudo existente.

    modo="novo"        cada painel entra com o proximo Nº Form livre do laudo
    modo="substituir"  os paineis de mesma TAG sao removidos e os novos tomam o lugar
    """
    manifest = ler_manifest(arquivo)
    if manifest.get("tipo") != "paineis":
        raise BackupErro("Este pacote e do tipo '%s'. Use a importacao correspondente."
                         % manifest.get("tipo"))
    if not db.buscar_laudo(laudo_id):
        raise BackupErro("Laudo de destino nao encontrado.")

    relatorio = _novo_relatorio()
    opcoes = _mapa_descricoes()
    with zipfile.ZipFile(arquivo) as zf:
        dados = json.loads(zf.read("dados.json").decode("utf-8"))
        # Um unico conjunto de numeros, para os paineis do pacote nao colidirem
        # entre si nem com os do laudo.
        usados = _formularios_usados(laudo_id)
        for pdados in dados.get("paineis") or []:
            _importar_painel_dict(pdados, laudo_id, zf, opcoes, relatorio, usados, modo)
    return relatorio
