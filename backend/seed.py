"""
seed.py — Popula o banco de dados com dados fake para testes.

Execução:
    cd backend
    python seed.py

O script é idempotente: verifica se os dados já existem antes de inserir,
portanto pode ser executado múltiplas vezes sem duplicar registros.

Dados criados:
  - 5 Membros (presidente + 4 fiscais)
  - 1 Comissão Fiscal
  - 1 Empresa contratada
  - 4 Tipos de Documento (NE, OB, RP, NS)
  - 1 Contrato (01/12/2025 a 30/11/2029 — 4 anos)
  - 2 Documentos Contábeis (NE de empenho)
  - 3 Tipos de Impressora
  - 4 Tipos de Impressão (com franquias e valores)
  - 6 Locais de Impressora (setores da OM)
  - 5 Modelos de Impressora
  - 10 Impressoras (distribuídas pelos setores)
  - Leituras mensais de Dez/2025 até o mês atual
"""

import asyncio
import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Garante que o diretório backend está no PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Carrega variáveis de ambiente do .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.config import get_settings
from app.database import Base
from app.models.models import (
    Comissao,
    Contrato,
    DocumentoContabil,
    Empresa,
    FranquiaContrato,
    Impressora,
    Leitura,
    LocalImpressora,
    Membro,
    ModeloImpressora,
    TabelaPreco,
    TipoDoc,
    TipoImpressao,
    TipoImpressora,
)

settings = get_settings()

# ── Cores para output ─────────────────────────────────────────────────────────
G = "\033[92m"  # verde
Y = "\033[93m"  # amarelo
R = "\033[91m"  # vermelho
B = "\033[94m"  # azul
E = "\033[0m"   # reset

def ok(msg):   print(f"  {G}[OK]{E}  {msg}")
def skip(msg): print(f"  {Y}[--]{E}  {msg} (já existe)")
def info(msg): print(f"  {B}[..]{E}  {msg}")


# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if settings.is_sqlite else {},
)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_or_none(db: AsyncSession, model, **kwargs):
    """Retorna o primeiro registro que bate com os filtros, ou None."""
    stmt = select(model).filter_by(**kwargs)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ─────────────────────────────────────────────────────────────────────────────
# DADOS SEED
# ─────────────────────────────────────────────────────────────────────────────

MEMBROS = [
    {"cpf": "111.111.111-11", "nome": "Cel Av Ricardo Fonseca"},
    {"cpf": "222.222.222-22", "nome": "Ten Cel Av Marcos Pereira"},
    {"cpf": "333.333.333-33", "nome": "Maj Av Fernanda Costa"},
    {"cpf": "444.444.444-44", "nome": "Cap Av Juliana Mendes"},
    {"cpf": "555.555.555-55", "nome": "1T Av Bruno Almeida"},
]

EMPRESA = {
    "cnpj": "12.345.678-0001-90",
    "nome": "TechPrint Soluções em Impressão LTDA",
}

TIPOS_DOC = ["NE", "OB", "RP", "NS"]

TIPOS_IMPRESSORA = [
    "Laser Monocromático A4",
    "Laser Colorido A4",
    "Multifuncional Laser A4",
]

LOCAIS = [
    {"setor": "COMAR",   "descricao": "Comando Aéreo Regional — Sala da Diretoria"},
    {"setor": "SETIC",   "descricao": "Seção de Tecnologia da Informação e Comunicações"},
    {"setor": "SEFIN",   "descricao": "Seção de Finanças — 2º andar"},
    {"setor": "SELOG",   "descricao": "Seção de Logística — Térreo"},
    {"setor": "SEPES",   "descricao": "Seção de Pessoal — 1º andar"},
    {"setor": "SECOP",   "descricao": "Secretaria e Protocolo — Recepção"},
]

MODELOS = [
    {"fabricante": "HP",     "modelo": "LaserJet Pro M404n",       "descricao": "Laser mono A4, 38 ppm"},
    {"fabricante": "HP",     "modelo": "LaserJet Pro MFP M428fdw", "descricao": "Multifuncional mono A4, 38 ppm"},
    {"fabricante": "Xerox",  "modelo": "VersaLink B405",            "descricao": "Multifuncional mono A4, 47 ppm"},
    {"fabricante": "Ricoh",  "modelo": "IM 430F",                   "descricao": "Multifuncional mono A4, 43 ppm"},
    {"fabricante": "Canon",  "modelo": "imageCLASS MF445dw",        "descricao": "Multifuncional mono A4, 40 ppm"},
]

# 10 impressoras: num_serie, modelo_idx, tipo_idx, local_idx, ip
IMPRESSORAS = [
    {"num_serie": "HP-M404-001",  "modelo": 0, "tipo": 0, "local": 1, "ip": "10.1.0.11"},
    {"num_serie": "HP-M404-002",  "modelo": 0, "tipo": 0, "local": 2, "ip": "10.1.0.12"},
    {"num_serie": "HP-MFP-003",   "modelo": 1, "tipo": 2, "local": 0, "ip": "10.1.0.13"},
    {"num_serie": "HP-MFP-004",   "modelo": 1, "tipo": 2, "local": 3, "ip": "10.1.0.14"},
    {"num_serie": "XRX-B405-005", "modelo": 2, "tipo": 2, "local": 1, "ip": "10.1.0.15"},
    {"num_serie": "XRX-B405-006", "modelo": 2, "tipo": 2, "local": 4, "ip": "10.1.0.16"},
    {"num_serie": "RCH-IM430-007","modelo": 3, "tipo": 2, "local": 2, "ip": "10.1.0.17"},
    {"num_serie": "RCH-IM430-008","modelo": 3, "tipo": 2, "local": 5, "ip": "10.1.0.18"},
    {"num_serie": "CNX-MF445-009","modelo": 4, "tipo": 2, "local": 3, "ip": "10.1.0.19"},
    {"num_serie": "CNX-MF445-010","modelo": 4, "tipo": 2, "local": 4, "ip": "10.1.0.20"},
]

# Tipos de impressão com franquias e valores
# Tipos de impressão (apenas descrição — valores ficam em FranquiaContrato + TabelaPreco)
TIPOS_IMPRESSAO = [
    {"descricao": "Preto e Branco A4"},
    {"descricao": "Colorido A4"},
]

# Configuração de franquia por contrato (total de páginas para os 4 anos)
# paginas_franquia = total contratado no período inteiro
FRANQUIAS_CONTRATO = [
    {
        "tipo_idx":            0,       # Preto e Branco A4
        "paginas_franquia":    500_000, # 500.000 pág. nos 4 anos
        "valor_mensal_franquia": Decimal("2_000.00"),  # pago todo mês
    },
    {
        "tipo_idx":            1,       # Colorido A4
        "paginas_franquia":    50_000,  # 50.000 pág. nos 4 anos
        "valor_mensal_franquia": Decimal("1_200.00"),  # pago todo mês
    },
]

# Tabelas de preço iniciais
TABELAS_PRECO_INICIAIS = [
    {
        "tipo_idx":             0,               # P&B A4
        "valor_dentro_franquia": Decimal("0.040"), # R$ 0,04/pág dentro da franquia
        "valor_fora_franquia":   Decimal("0.080"), # R$ 0,08/pág fora da franquia
        "vigente_de":           date(2025, 12, 1),
    },
    {
        "tipo_idx":             1,               # Colorido A4
        "valor_dentro_franquia": Decimal("0.150"), # R$ 0,15/pág dentro
        "valor_fora_franquia":   Decimal("0.300"), # R$ 0,30/pág fora
        "vigente_de":           date(2025, 12, 1),
    },
]

# Contrato
CONTRATO = {
    "numero":          "CONTRATO-001/2025",
    "data_inicio":     date(2025, 12, 1),
    "data_termino":    date(2029, 11, 30),
    "numero_processo": "NUP-00001-007/2025-FAB",
    "valor_estimado":  Decimal("480000.00"),
}

# Documentos contábeis (empenhos)
DOCS_CONTABEIS = [
    {"numero": "2025NE000123", "tipo": "NE", "valor": Decimal("120000.00")},
    {"numero": "2026NE000045", "tipo": "NE", "valor": Decimal("120000.00")},
]


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE SEED
# ─────────────────────────────────────────────────────────────────────────────

async def seed_membros(db: AsyncSession) -> list[Membro]:
    print(f"\n{B}Membros:{E}")
    membros = []
    for m in MEMBROS:
        existing = await get_or_none(db, Membro, cpf=m["cpf"])
        if existing:
            skip(m["nome"])
            membros.append(existing)
        else:
            obj = Membro(**m)
            db.add(obj)
            await db.flush()
            ok(m["nome"])
            membros.append(obj)
    return membros


async def seed_comissao(db: AsyncSession, membros: list[Membro]) -> Comissao:
    print(f"\n{B}Comissão Fiscal:{E}")
    existing = await get_or_none(db, Comissao, documento_numero="BI 012/2025")
    if existing:
        skip("BI 012/2025 — Comissão de Fiscalização do Contrato")
        return existing

    comissao = Comissao(
        presidente_cpf=membros[0].cpf,
        documento_numero="BI 012/2025",
        documento_data=date(2025, 11, 15),
    )
    comissao.fiscais = membros[1:]
    db.add(comissao)
    await db.flush()
    ok(f"BI 012/2025 — presidente: {membros[0].nome}, fiscais: {len(membros)-1}")
    return comissao


async def seed_empresa(db: AsyncSession) -> Empresa:
    print(f"\n{B}Empresa:{E}")
    existing = await get_or_none(db, Empresa, cnpj=EMPRESA["cnpj"])
    if existing:
        skip(EMPRESA["nome"])
        return existing
    obj = Empresa(**EMPRESA)
    db.add(obj)
    await db.flush()
    ok(EMPRESA["nome"])
    return obj


async def seed_tipos_doc(db: AsyncSession) -> dict[str, TipoDoc]:
    print(f"\n{B}Tipos de Documento:{E}")
    tipos = {}
    for nome in TIPOS_DOC:
        existing = await get_or_none(db, TipoDoc, nome=nome)
        if existing:
            skip(nome)
            tipos[nome] = existing
        else:
            obj = TipoDoc(nome=nome)
            db.add(obj)
            await db.flush()
            ok(nome)
            tipos[nome] = obj
    return tipos


async def seed_tipos_impressora(db: AsyncSession) -> list[TipoImpressora]:
    print(f"\n{B}Tipos de Impressora:{E}")
    tipos = []
    for tipo in TIPOS_IMPRESSORA:
        existing = await get_or_none(db, TipoImpressora, tipo=tipo)
        if existing:
            skip(tipo)
            tipos.append(existing)
        else:
            obj = TipoImpressora(tipo=tipo)
            db.add(obj)
            await db.flush()
            ok(tipo)
            tipos.append(obj)
    return tipos


async def seed_tipos_impressao(db: AsyncSession) -> list[TipoImpressao]:
    print(f"\n{B}Tipos de Impressão:{E}")
    tipos = []
    for t in TIPOS_IMPRESSAO:
        existing = await get_or_none(db, TipoImpressao, descricao=t["descricao"])
        if existing:
            skip(t["descricao"])
            tipos.append(existing)
        else:
            obj = TipoImpressao(**t)
            db.add(obj)
            await db.flush()
            ok(t['descricao'])
            tipos.append(obj)
    return tipos


async def seed_locais(db: AsyncSession) -> list[LocalImpressora]:
    print(f"\n{B}Locais de Impressora:{E}")
    locais = []
    for l in LOCAIS:
        existing = await get_or_none(db, LocalImpressora, setor=l["setor"])
        if existing:
            skip(l["setor"])
            locais.append(existing)
        else:
            obj = LocalImpressora(**l)
            db.add(obj)
            await db.flush()
            ok(f"{l['setor']} — {l['descricao']}")
            locais.append(obj)
    return locais


async def seed_modelos(db: AsyncSession) -> list[ModeloImpressora]:
    print(f"\n{B}Modelos de Impressora:{E}")
    modelos = []
    for m in MODELOS:
        existing = await get_or_none(db, ModeloImpressora,
                                     fabricante=m["fabricante"], modelo=m["modelo"])
        if existing:
            skip(f"{m['fabricante']} {m['modelo']}")
            modelos.append(existing)
        else:
            obj = ModeloImpressora(**m)
            db.add(obj)
            await db.flush()
            ok(f"{m['fabricante']} {m['modelo']}")
            modelos.append(obj)
    return modelos


async def seed_impressoras(
    db: AsyncSession,
    tipos_imp: list[TipoImpressora],
    locais: list[LocalImpressora],
    modelos: list[ModeloImpressora],
) -> list[Impressora]:
    print(f"\n{B}Impressoras:{E}")
    impressoras = []
    for i in IMPRESSORAS:
        existing = await get_or_none(db, Impressora, num_serie=i["num_serie"])
        if existing:
            modelo_nome = f"{modelos[i['modelo']].fabricante} {modelos[i['modelo']].modelo}"
            skip(f"{i['num_serie']} — {modelo_nome}")
            impressoras.append(existing)
        else:
            obj = Impressora(
                num_serie=i["num_serie"],
                tipo_id=tipos_imp[i["tipo"]].id,
                local_id=locais[i["local"]].id,
                modelo_id=modelos[i["modelo"]].id,
                ip=i["ip"],
                ativa=True,
            )
            db.add(obj)
            await db.flush()
            modelo_nome = f"{modelos[i['modelo']].fabricante} {modelos[i['modelo']].modelo}"
            ok(f"{i['num_serie']} — {modelo_nome} @ {locais[i['local']].setor} ({i['ip']})")
            impressoras.append(obj)
    return impressoras




async def seed_franquias_contrato(
    db: AsyncSession,
    contrato: Contrato,
    tipos_impressao: list[TipoImpressao],
) -> None:
    print(f"\n{B}Franquias do Contrato:{E}")
    for fc in FRANQUIAS_CONTRATO:
        tipo = tipos_impressao[fc["tipo_idx"]]
        existing = await db.execute(
            select(FranquiaContrato).filter_by(
                contrato_id=contrato.id,
                tipo_impressao_id=tipo.id,
            )
        )
        if existing.scalar_one_or_none():
            skip(f"{tipo.descricao}: {fc['paginas_franquia']:,} pág. / R$ {fc['valor_mensal_franquia']}/mês")
            continue
        obj = FranquiaContrato(
            contrato_id=contrato.id,
            tipo_impressao_id=tipo.id,
            paginas_franquia=fc["paginas_franquia"],
            valor_mensal_franquia=fc["valor_mensal_franquia"],
        )
        db.add(obj)
        await db.flush()
        ok(f"{tipo.descricao}: {fc['paginas_franquia']:,} pág. totais / R$ {fc['valor_mensal_franquia']}/mês")


async def seed_tabelas_preco(
    db: AsyncSession,
    contrato: Contrato,
    tipos_impressao: list[TipoImpressao],
) -> None:
    print(f"\n{B}Tabelas de Preço:{E}")
    for tp in TABELAS_PRECO_INICIAIS:
        tipo = tipos_impressao[tp["tipo_idx"]]
        existing = await db.execute(
            select(TabelaPreco).filter_by(
                contrato_id=contrato.id,
                tipo_impressao_id=tipo.id,
            )
        )
        if existing.scalar_one_or_none():
            skip(f"{tipo.descricao}: R$ {tp['valor_dentro_franquia']}/pág (dentro) | R$ {tp['valor_fora_franquia']}/pág (fora)")
            continue
        obj = TabelaPreco(
            contrato_id=contrato.id,
            tipo_impressao_id=tipo.id,
            valor_dentro_franquia=tp["valor_dentro_franquia"],
            valor_fora_franquia=tp["valor_fora_franquia"],
            vigente_de=tp["vigente_de"],
            vigente_ate=None,
        )
        db.add(obj)
        await db.flush()
        ok(f"{tipo.descricao}: R$ {tp['valor_dentro_franquia']}/pág (dentro) | R$ {tp['valor_fora_franquia']}/pág (fora)")

async def seed_contrato(
    db: AsyncSession,
    empresa: Empresa,
    comissao: Comissao,
) -> Contrato:
    print(f"\n{B}Contrato:{E}")
    existing = await get_or_none(db, Contrato, numero=CONTRATO["numero"])
    if existing:
        skip(f"{CONTRATO['numero']} ({CONTRATO['data_inicio']} → {CONTRATO['data_termino']})")
        return existing

    obj = Contrato(
        numero=CONTRATO["numero"],
        empresa_cnpj=empresa.cnpj,
        data_inicio=CONTRATO["data_inicio"],
        data_termino=CONTRATO["data_termino"],
        comissao_id=comissao.id,
        numero_processo=CONTRATO["numero_processo"],
        valor_estimado=CONTRATO["valor_estimado"],
    )
    db.add(obj)
    await db.flush()
    ok(
        f"{CONTRATO['numero']} | "
        f"{CONTRATO['data_inicio']} → {CONTRATO['data_termino']} | "
        f"R$ {CONTRATO['valor_estimado']:,.2f}"
    )
    return obj


async def seed_documentos_contabeis(
    db: AsyncSession,
    contrato: Contrato,
    tipos_doc: dict[str, TipoDoc],
) -> None:
    print(f"\n{B}Documentos Contábeis:{E}")
    for d in DOCS_CONTABEIS:
        existing = await get_or_none(db, DocumentoContabil, numero=d["numero"])
        if existing:
            skip(f"{d['numero']} — R$ {d['valor']:,.2f}")
            continue
        obj = DocumentoContabil(
            numero=d["numero"],
            tipo_documento_id=tipos_doc[d["tipo"]].id,
            contrato_id=contrato.id,
            valor=d["valor"],
        )
        db.add(obj)
        await db.flush()
        ok(f"{d['numero']} ({d['tipo']}) — R$ {d['valor']:,.2f}")


async def seed_leituras(
    db: AsyncSession,
    contrato: Contrato,
    impressoras: list[Impressora],
    tipos_impressao: list[TipoImpressao],
) -> None:
    print(f"\n{B}Leituras de Contadores:{E}")

    hoje = date.today()

    # Gera lista de (mes, ano) de dez/2025 até o mês atual
    meses = []
    ano, mes = 2025, 12
    while (ano, mes) <= (hoje.year, hoje.month):
        meses.append((mes, ano))
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

    info(f"Gerando leituras de Dez/2025 até {hoje.strftime('%b/%Y')} "
         f"({len(meses)} meses × 10 impressoras)")

    # Contadores iniciais por impressora (valores realistas e variados)
    contadores_iniciais = {
        "HP-M404-001":   12_500,
        "HP-M404-002":    8_300,
        "HP-MFP-003":    45_200,
        "HP-MFP-004":    31_700,
        "XRX-B405-005":  22_100,
        "XRX-B405-006":  18_900,
        "RCH-IM430-007": 67_800,
        "RCH-IM430-008": 53_200,
        "CNX-MF445-009": 29_600,
        "CNX-MF445-010": 41_300,
    }

    # Incremento médio mensal por impressora (páginas/mês — varia por setor)
    incrementos = {
        "HP-M404-001":    850,   # SETIC — uso moderado
        "HP-M404-002":    620,   # SEFIN — uso baixo
        "HP-MFP-003":   1_200,  # COMAR — uso alto (diretoria)
        "HP-MFP-004":    980,   # SELOG — uso moderado-alto
        "XRX-B405-005": 1_450,  # SETIC — multifuncional muito usado
        "XRX-B405-006":  730,   # SEPES — uso moderado
        "RCH-IM430-007": 1_100, # SEFIN — uso alto
        "RCH-IM430-008":  890,  # SECOP — uso moderado
        "CNX-MF445-009":  650,  # SELOG — uso baixo
        "CNX-MF445-010":  820,  # SEPES — uso moderado
    }

    # Tipo de impressão por impressora (0=P&B, 1=Colorido)
    tipo_por_impressora = {
        "HP-M404-001":   0,
        "HP-M404-002":   0,
        "HP-MFP-003":    0,
        "HP-MFP-004":    0,
        "XRX-B405-005":  0,
        "XRX-B405-006":  0,
        "RCH-IM430-007": 0,
        "RCH-IM430-008": 0,
        "CNX-MF445-009": 0,
        "CNX-MF445-010": 0,
    }

    import random
    random.seed(42)  # Seed fixo para resultados reproduzíveis

    total_inseridas = 0
    total_existentes = 0

    for imp in impressoras:
        contador = contadores_iniciais.get(imp.num_serie, 10_000)
        inc_base = incrementos.get(imp.num_serie, 800)
        tipo_idx = tipo_por_impressora.get(imp.num_serie, 0)
        tipo = tipos_impressao[tipo_idx]

        for mes, ano in meses:
            # Verifica se já existe leitura para esta impressora/mês/ano
            existing = await db.execute(
                select(Leitura).filter_by(
                    contrato_id=contrato.id,
                    impressora_num_serie=imp.num_serie,
                    mes_referencia=mes,
                    ano_referencia=ano,
                    tipo_impressao_id=tipo.id,
                )
            )
            if existing.scalar_one_or_none():
                total_existentes += 1
                continue

            # Variação aleatória ±20% do incremento base
            variacao = random.uniform(0.80, 1.20)
            contador += int(inc_base * variacao)

            # Último dia do mês de referência
            if mes == 12:
                ultimo_dia = date(ano, 12, 31)
            else:
                ultimo_dia = date(ano, mes + 1, 1) - timedelta(days=1)

            # Se o mês é o atual, usa hoje como data
            data_leitura = min(ultimo_dia, hoje)

            leitura = Leitura(
                contrato_id=contrato.id,
                impressora_num_serie=imp.num_serie,
                tipo_impressao_id=tipo.id,
                contador=contador,
                data=data_leitura,
                mes_referencia=mes,
                ano_referencia=ano,
                manual=False,
                observacao="Leitura de seed — dado de teste",
            )
            db.add(leitura)
            total_inseridas += 1

        # Flush por impressora para não acumular muitos objetos em memória
        await db.flush()

    if total_existentes:
        skip(f"{total_existentes} leituras já existiam")
    ok(f"{total_inseridas} leituras inseridas ({len(meses)} meses × 10 impressoras)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    print(f"\n{'='*60}")
    print(f"  SCI — Script de Population do Banco de Dados (Seed)")
    print(f"  Banco: {settings.DATABASE_URL[:60]}...")
    print(f"{'='*60}")

    # Cria tabelas se necessário (SQLite)
    if settings.is_sqlite:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        info("Tabelas verificadas/criadas (SQLite)")

    async with SessionLocal() as db:
        try:
            # Executa seed na ordem correta (respeitando FKs)
            membros         = await seed_membros(db)
            comissao        = await seed_comissao(db, membros)
            empresa         = await seed_empresa(db)
            tipos_doc       = await seed_tipos_doc(db)
            tipos_impressora= await seed_tipos_impressora(db)
            tipos_impressao = await seed_tipos_impressao(db)
            locais          = await seed_locais(db)
            modelos         = await seed_modelos(db)
            impressoras     = await seed_impressoras(db, tipos_impressora, locais, modelos)
            contrato        = await seed_contrato(db, empresa, comissao)
            await seed_documentos_contabeis(db, contrato, tipos_doc)
            await seed_franquias_contrato(db, contrato, tipos_impressao)
            await seed_tabelas_preco(db, contrato, tipos_impressao)
            await seed_leituras(db, contrato, impressoras, tipos_impressao)

            await db.commit()

            print(f"\n{'='*60}")
            print(f"  {G}Seed concluído com sucesso!{E}")
            print(f"{'='*60}")
            print(f"\n  Acesse o sistema e faça login com:")
            print(f"    Usuário: {Y}user{E}  |  Senha: {Y}user{E}")
            print(f"\n  Contrato criado: {Y}{CONTRATO['numero']}{E}")
            print(f"  Vigência: {CONTRATO['data_inicio']} → {CONTRATO['data_termino']}")
            print(f"  Valor estimado: R$ {CONTRATO['valor_estimado']:,.2f}")
            print(f"\n  Impressoras: {Y}10{E} cadastradas com leituras mensais")
            print(f"  Relatório disponível em: Relatórios → Selecione o contrato\n")

        except Exception as e:
            await db.rollback()
            print(f"\n  {R}[ERRO]{E} {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
