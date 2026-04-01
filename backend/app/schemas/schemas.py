"""
schemas.py — Schemas Pydantic v2 para validação e serialização.

Cada entidade possui três grupos de schemas:
  - Base    : campos comuns a criação e leitura
  - Create  : campos obrigatórios para criação (POST)
  - Update  : campos opcionais para atualização parcial (PATCH)
  - Read/Out: schema de resposta, com campos adicionais do banco (id, datas)

Convenções:
  - model_config = ConfigDict(from_attributes=True) permite converter
    objetos SQLAlchemy para Pydantic automaticamente.
  - Campos monetários usam Decimal para precisão.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Membro
# ═══════════════════════════════════════════════════════════════════════════════

class MembroBase(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF com ou sem formatação")
    nome: str = Field(..., min_length=3, max_length=200)


class MembroCreate(MembroBase):
    pass


class MembroUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=200)


class MembroOut(MembroBase):
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Comissão
# ═══════════════════════════════════════════════════════════════════════════════

class ComissaoBase(BaseModel):
    presidente_cpf: str = Field(..., description="CPF do presidente da comissão")
    documento_numero: str = Field(..., max_length=100, description="Número do ato de designação")
    documento_data: date = Field(..., description="Data do ato de designação")


class ComissaoCreate(ComissaoBase):
    fiscais_cpf: List[str] = Field(
        default_factory=list,
        description="Lista de CPFs dos fiscais da comissão",
    )


class ComissaoUpdate(BaseModel):
    presidente_cpf: Optional[str] = None
    documento_numero: Optional[str] = None
    documento_data: Optional[date] = None
    fiscais_cpf: Optional[List[str]] = None


class ComissaoOut(ComissaoBase):
    id: int
    documento_path: Optional[str] = None
    presidente: MembroOut
    fiscais: List[MembroOut] = []
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Empresa
# ═══════════════════════════════════════════════════════════════════════════════

class EmpresaBase(BaseModel):
    cnpj: str = Field(..., min_length=14, max_length=18, description="CNPJ com ou sem formatação")
    nome: str = Field(..., min_length=2, max_length=300)


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=300)


class EmpresaOut(EmpresaBase):
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Contrato
# ═══════════════════════════════════════════════════════════════════════════════

class ContratoBase(BaseModel):
    numero: str = Field(..., max_length=50, description="Número do contrato")
    empresa_cnpj: str = Field(..., description="CNPJ da empresa contratada")
    data_inicio: date
    data_termino: date
    comissao_id: int
    numero_processo: str = Field(..., max_length=100, description="Número do processo administrativo")

    @field_validator("data_termino")
    @classmethod
    def termino_apos_inicio(cls, v, info):
        if "data_inicio" in info.data and v <= info.data["data_inicio"]:
            raise ValueError("data_termino deve ser posterior a data_inicio")
        return v


class ContratoCreate(ContratoBase):
    pass


class ContratoUpdate(BaseModel):
    numero: Optional[str] = None
    empresa_cnpj: Optional[str] = None
    data_inicio: Optional[date] = None
    data_termino: Optional[date] = None
    comissao_id: Optional[int] = None
    numero_processo: Optional[str] = None


class ContratoOut(ContratoBase):
    id: int
    empresa: EmpresaOut
    comissao: ComissaoOut
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ContratoResumo(BaseModel):
    """Schema resumido para listagens e selects."""
    id: int
    numero: str
    empresa: EmpresaOut
    data_inicio: date
    data_termino: date

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Fatura
# ═══════════════════════════════════════════════════════════════════════════════

class FaturaBase(BaseModel):
    numero: str = Field(..., max_length=100)
    data: date
    contrato_id: int


class FaturaCreate(FaturaBase):
    pass


class FaturaUpdate(BaseModel):
    numero: Optional[str] = None
    data: Optional[date] = None
    contrato_id: Optional[int] = None


class FaturaOut(FaturaBase):
    id: int
    contrato: ContratoResumo
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Documento Contábil
# ═══════════════════════════════════════════════════════════════════════════════

class TipoDocBase(BaseModel):
    nome: str = Field(..., max_length=100, description="Ex: NE, OB, RP")


class TipoDocCreate(TipoDocBase):
    pass


class TipoDocUpdate(BaseModel):
    nome: Optional[str] = None


class TipoDocOut(TipoDocBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Documento Contábil
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentoContabilBase(BaseModel):
    numero: str = Field(..., max_length=100)
    tipo_documento_id: int
    contrato_id: int
    valor: Decimal = Field(..., ge=0, decimal_places=2)


class DocumentoContabilCreate(DocumentoContabilBase):
    pass


class DocumentoContabilUpdate(BaseModel):
    numero: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    contrato_id: Optional[int] = None
    valor: Optional[Decimal] = None


class DocumentoContabilOut(DocumentoContabilBase):
    id: int
    tipo_documento: TipoDocOut
    contrato: ContratoResumo
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class TipoImpressoraBase(BaseModel):
    tipo: str = Field(..., max_length=100, description="Ex: Laser Mono, Laser Color, Multifuncional")


class TipoImpressoraCreate(TipoImpressoraBase):
    pass


class TipoImpressoraUpdate(BaseModel):
    tipo: Optional[str] = None


class TipoImpressoraOut(TipoImpressoraBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Local da Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class LocalImpressoraBase(BaseModel):
    setor: str = Field(..., max_length=100, description="Sigla ou nome do setor")
    descricao: str = Field(..., max_length=300)


class LocalImpressoraCreate(LocalImpressoraBase):
    pass


class LocalImpressoraUpdate(BaseModel):
    setor: Optional[str] = None
    descricao: Optional[str] = None


class LocalImpressoraOut(LocalImpressoraBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class ImpressoraBase(BaseModel):
    num_serie: str = Field(..., max_length=100)
    nome: str = Field(..., max_length=200)
    tipo_id: int
    local_id: int
    ip: Optional[str] = Field(None, max_length=45, description="Endereço IP para consulta SNMP")
    ativa: bool = True


class ImpressoraCreate(ImpressoraBase):
    pass


class ImpressoraUpdate(BaseModel):
    nome: Optional[str] = None
    tipo_id: Optional[int] = None
    local_id: Optional[int] = None
    ip: Optional[str] = None
    ativa: Optional[bool] = None


class ImpressoraOut(ImpressoraBase):
    tipo: TipoImpressoraOut
    local: LocalImpressoraOut
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Impressão
# ═══════════════════════════════════════════════════════════════════════════════

class TipoImpressaoBase(BaseModel):
    descricao: str = Field(..., max_length=200, description="Ex: P&B A4, Colorida A4")
    franquia: int = Field(..., ge=0, description="Quantidade de páginas na franquia mensal")
    valor_franquia: Decimal = Field(..., ge=0, decimal_places=2, description="Valor mensal da franquia (R$)")
    valor_extra_franquia: Decimal = Field(..., ge=0, decimal_places=2, description="Valor por página excedente (R$)")


class TipoImpressaoCreate(TipoImpressaoBase):
    pass


class TipoImpressaoUpdate(BaseModel):
    descricao: Optional[str] = None
    franquia: Optional[int] = None
    valor_franquia: Optional[Decimal] = None
    valor_extra_franquia: Optional[Decimal] = None


class TipoImpressaoOut(TipoImpressaoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Leitura
# ═══════════════════════════════════════════════════════════════════════════════

class LeituraBase(BaseModel):
    impressora_num_serie: str
    tipo_impressao_id: int
    contador: int = Field(..., ge=0, description="Valor do totalizador (contador acumulado)")
    data: date
    mes_referencia: int = Field(..., ge=1, le=12)
    ano_referencia: int = Field(..., ge=2000, le=2100)
    manual: bool = False
    observacao: Optional[str] = None


class LeituraCreate(LeituraBase):
    pass


class LeituraSNMPRequest(BaseModel):
    """
    Schema para solicitar leitura automática via SNMP.
    O sistema tenta ler o contador e salva o resultado.
    """
    impressora_num_serie: str
    tipo_impressao_id: int
    mes_referencia: int = Field(..., ge=1, le=12)
    ano_referencia: int = Field(..., ge=2000, le=2100)


class LeituraUpdate(BaseModel):
    contador: Optional[int] = None
    data: Optional[date] = None
    mes_referencia: Optional[int] = None
    ano_referencia: Optional[int] = None
    observacao: Optional[str] = None


class LeituraOut(LeituraBase):
    id: int
    impressora: ImpressoraOut
    tipo_impressao: TipoImpressaoOut
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class SNMPResultado(BaseModel):
    """Resultado de uma tentativa de leitura SNMP."""
    sucesso: bool
    contador: Optional[int] = None
    oid_usado: Optional[str] = None
    erro: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas de Relatórios
# ═══════════════════════════════════════════════════════════════════════════════

class RelatorioMensalItem(BaseModel):
    """Item de consumo mensal por impressora e tipo de impressão."""
    impressora_num_serie: str
    impressora_nome: str
    setor: str
    tipo_impressao: str
    mes: int
    ano: int
    contador_inicial: int
    contador_final: int
    paginas_impressas: int
    franquia: int
    paginas_dentro_franquia: int
    paginas_excedente: int
    valor_franquia: Decimal
    valor_excedente: Decimal
    valor_total: Decimal


class RelatorioMensal(BaseModel):
    """Relatório mensal consolidado por contrato."""
    contrato_numero: str
    empresa_nome: str
    mes: int
    ano: int
    itens: List[RelatorioMensalItem]
    total_paginas: int
    total_valor: Decimal
    percentual_orcamento: Optional[float] = None
    percentual_tempo: Optional[float] = None


class RelatorioTotalItem(BaseModel):
    """Resumo total por tipo de impressão para o período do contrato."""
    tipo_impressao: str
    total_paginas: int
    total_valor: Decimal


class RelatorioTotal(BaseModel):
    """Relatório total consolidado para toda a vigência do contrato."""
    contrato_numero: str
    empresa_nome: str
    data_inicio: date
    data_termino: date
    numero_processo: str
    itens: List[RelatorioTotalItem]
    total_geral_paginas: int
    total_geral_valor: Decimal
    total_empenhado: Decimal
    percentual_orcamento_consumido: float
    percentual_tempo_decorrido: float
    dias_decorridos: int
    dias_totais: int
    meses_com_leitura: int
    impressoras_ativas: int


class EvolucaoMensalItem(BaseModel):
    """Ponto de dados para o gráfico de evolução mensal."""
    mes: int
    ano: int
    label: str  # Ex: "Jan/2024"
    total_paginas: int
    total_valor: Decimal


class RankingImpressora(BaseModel):
    """Ranking de impressoras por volume de impressão."""
    posicao: int
    num_serie: str
    nome: str
    setor: str
    total_paginas: int
    total_valor: Decimal
