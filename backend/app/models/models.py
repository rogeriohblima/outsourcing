"""
models.py — Modelos ORM do sistema (SQLAlchemy 2.0).

Cada classe representa uma tabela no banco de dados.
Relacionamentos são definidos com Mapped[] e relationship(),
seguindo a sintaxe moderna do SQLAlchemy 2.0.

Entidades do sistema:
  - Membro          : Integrante da comissão fiscal
  - Comissao        : Comissão com presidente e fiscais
  - Empresa         : Empresa contratada
  - Contrato        : Contrato de fornecimento de impressoras
  - Fatura          : Fatura vinculada ao contrato
  - TipoDoc         : Tipo de documento contábil
  - DocumentoContabil: Documento contábil (NE, OB, etc.)
  - TipoImpressora  : Categorização de impressoras (laser, jato, etc.)
  - LocalImpressora : Setor/local onde a impressora está instalada
  - Impressora      : Impressora física monitorada
  - TipoImpressao   : Tipo de impressão (P&B, colorida, etc.) com franquia
  - Leitura         : Leitura de contador (automática via SNMP ou manual)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Column,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ═══════════════════════════════════════════════════════════════════════════════
# Tabela de associação: Comissão ↔ Fiscais (N:N)
# ═══════════════════════════════════════════════════════════════════════════════

comissao_fiscais = Table(
    "comissao_fiscais",
    Base.metadata,
    Column(
        "comissao_id",
        Integer,
        ForeignKey("comissoes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "membro_cpf",
        String(14),
        ForeignKey("membros.cpf", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# Membro
# ═══════════════════════════════════════════════════════════════════════════════

class Membro(Base):
    """
    Integrante da comissão fiscal (presidente ou fiscal).

    O CPF é a chave primária natural do membro.
    Formato esperado: '000.000.000-00' (com pontuação) ou '00000000000' (só dígitos).
    """

    __tablename__ = "membros"

    cpf: Mapped[str] = mapped_column(String(14), primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relacionamentos reversos
    presidencias: Mapped[List["Comissao"]] = relationship(
        "Comissao", back_populates="presidente", foreign_keys="Comissao.presidente_cpf"
    )
    fiscalizacoes: Mapped[List["Comissao"]] = relationship(
        "Comissao", secondary=comissao_fiscais, back_populates="fiscais"
    )

    def __repr__(self) -> str:
        return f"<Membro cpf={self.cpf} nome={self.nome}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Comissão Fiscal
# ═══════════════════════════════════════════════════════════════════════════════

class Comissao(Base):
    """
    Comissão fiscal responsável pela fiscalização do contrato.

    Composta por um presidente (Membro) e zero ou mais fiscais (Membro).
    O documento oficial (portaria, BI, etc.) pode ser armazenado
    como arquivo no servidor (campo documento_path).
    """

    __tablename__ = "comissoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    presidente_cpf: Mapped[str] = mapped_column(
        String(14), ForeignKey("membros.cpf"), nullable=False
    )
    documento_numero: Mapped[str] = mapped_column(String(100), nullable=False)
    documento_data: Mapped[date] = mapped_column(Date, nullable=False)
    # Caminho do arquivo no servidor (PDF do ato de designação)
    documento_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relacionamentos
    presidente: Mapped["Membro"] = relationship(
        "Membro", back_populates="presidencias", foreign_keys=[presidente_cpf]
    )
    fiscais: Mapped[List["Membro"]] = relationship(
        "Membro", secondary=comissao_fiscais, back_populates="fiscalizacoes"
    )
    contratos: Mapped[List["Contrato"]] = relationship(
        "Contrato", back_populates="comissao"
    )

    def __repr__(self) -> str:
        return f"<Comissao id={self.id} doc={self.documento_numero}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Empresa
# ═══════════════════════════════════════════════════════════════════════════════

class Empresa(Base):
    """
    Empresa contratada para fornecimento de impressoras/serviços.

    O CNPJ é a chave primária natural da empresa.
    Formato esperado: '00.000.000/0000-00'.
    """

    __tablename__ = "empresas"

    cnpj: Mapped[str] = mapped_column(String(18), primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    contratos: Mapped[List["Contrato"]] = relationship(
        "Contrato", back_populates="empresa"
    )

    def __repr__(self) -> str:
        return f"<Empresa cnpj={self.cnpj} nome={self.nome}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Contrato
# ═══════════════════════════════════════════════════════════════════════════════

class Contrato(Base):
    """
    Contrato de fornecimento de impressoras firmado com a empresa.

    Vincula uma empresa, uma comissão fiscal e possui
    datas de vigência e número de processo administrativo.
    """

    __tablename__ = "contratos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    empresa_cnpj: Mapped[str] = mapped_column(
        String(18), ForeignKey("empresas.cnpj"), nullable=False
    )
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_termino: Mapped[date] = mapped_column(Date, nullable=False)
    comissao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comissoes.id"), nullable=False
    )
    numero_processo: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_estimado: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relacionamentos
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="contratos")
    comissao: Mapped["Comissao"] = relationship("Comissao", back_populates="contratos")
    faturas: Mapped[List["Fatura"]] = relationship(
        "Fatura", back_populates="contrato", cascade="all, delete-orphan"
    )
    documentos_contabeis: Mapped[List["DocumentoContabil"]] = relationship(
        "DocumentoContabil", back_populates="contrato", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Contrato numero={self.numero}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Fatura
# ═══════════════════════════════════════════════════════════════════════════════

class Fatura(Base):
    """
    Fatura emitida pela empresa contratada, vinculada a um contrato.
    """

    __tablename__ = "faturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    contrato_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contratos.id"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    contrato: Mapped["Contrato"] = relationship("Contrato", back_populates="faturas")

    def __repr__(self) -> str:
        return f"<Fatura numero={self.numero}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Documento Contábil
# ═══════════════════════════════════════════════════════════════════════════════

class TipoDoc(Base):
    """
    Tipo de documento contábil (NE — Nota de Empenho, OB — Ordem Bancária, etc.).
    """

    __tablename__ = "tipos_doc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    documentos: Mapped[List["DocumentoContabil"]] = relationship(
        "DocumentoContabil", back_populates="tipo_documento"
    )

    def __repr__(self) -> str:
        return f"<TipoDoc id={self.id} nome={self.nome}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Documento Contábil
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentoContabil(Base):
    """
    Documento contábil (NE, OB, etc.) vinculado a um contrato.

    Permite rastrear os empenhos e pagamentos realizados ao longo
    da vigência do contrato.
    """

    __tablename__ = "documentos_contabeis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tipo_documento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_doc.id"), nullable=False
    )
    contrato_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contratos.id"), nullable=False
    )
    # Usando Numeric(14,2) para precisão monetária
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    tipo_documento: Mapped["TipoDoc"] = relationship(
        "TipoDoc", back_populates="documentos"
    )
    contrato: Mapped["Contrato"] = relationship(
        "Contrato", back_populates="documentos_contabeis"
    )

    def __repr__(self) -> str:
        return f"<DocumentoContabil numero={self.numero} valor={self.valor}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class TipoImpressora(Base):
    """
    Categoria/tipo de impressora (laser mono, laser cor, multifuncional, etc.).
    """

    __tablename__ = "tipos_impressora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    impressoras: Mapped[List["Impressora"]] = relationship(
        "Impressora", back_populates="tipo"
    )

    def __repr__(self) -> str:
        return f"<TipoImpressora id={self.id} tipo={self.tipo}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Local da Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class LocalImpressora(Base):
    """
    Localização física da impressora dentro da organização.

    Setor: identificador da seção/divisão (ex: 'SETIC').
    Descricao: descrição detalhada do local (ex: 'Sala 12, 2º andar').
    """

    __tablename__ = "locais_impressora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    setor: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)

    impressoras: Mapped[List["Impressora"]] = relationship(
        "Impressora", back_populates="local"
    )

    def __repr__(self) -> str:
        return f"<LocalImpressora setor={self.setor}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class Impressora(Base):
    """
    Impressora física monitorada pelo sistema.

    O número de série é a chave primária natural.
    O campo 'ip' é usado para consultas SNMP automáticas.
    O campo 'ativa' indica se a impressora está em operação.
    """

    __tablename__ = "impressoras"

    num_serie: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_impressora.id"), nullable=False
    )
    local_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("locais_impressora.id"), nullable=False
    )
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv4 ou IPv6
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    tipo: Mapped["TipoImpressora"] = relationship(
        "TipoImpressora", back_populates="impressoras"
    )
    local: Mapped["LocalImpressora"] = relationship(
        "LocalImpressora", back_populates="impressoras"
    )
    leituras: Mapped[List["Leitura"]] = relationship(
        "Leitura", back_populates="impressora", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Impressora num_serie={self.num_serie} nome={self.nome}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Impressão
# ═══════════════════════════════════════════════════════════════════════════════

class TipoImpressao(Base):
    """
    Tipo de impressão definido no contrato, com valores de franquia.

    Exemplos: 'Preto e Branco A4', 'Colorida A4', 'A3 Colorida'.

    franquia          : Quantidade de páginas incluídas no custo fixo mensal
    valor_franquia    : Valor mensal cobrado pela franquia (custo fixo)
    valor_extra_franquia: Valor cobrado por página que exceder a franquia
    """

    __tablename__ = "tipos_impressao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    franquia: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valor_franquia: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    valor_extra_franquia: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )

    leituras: Mapped[List["Leitura"]] = relationship(
        "Leitura", back_populates="tipo_impressao"
    )

    def __repr__(self) -> str:
        return f"<TipoImpressao id={self.id} desc={self.descricao}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Leitura de Contador
# ═══════════════════════════════════════════════════════════════════════════════

class Leitura(Base):
    """
    Registro de leitura do contador de páginas de uma impressora.

    Pode ser obtida de forma automática via SNMP ou inserida manualmente
    pelo fiscal do contrato (campo 'manual' indica a origem).

    O campo 'contador' representa o valor acumulado do totalizador da
    impressora (contador absoluto, não incremental).

    mes_referencia e ano_referencia identificam o período de cobrança.
    """

    __tablename__ = "leituras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    impressora_num_serie: Mapped[str] = mapped_column(
        String(100), ForeignKey("impressoras.num_serie"), nullable=False, index=True
    )
    tipo_impressao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_impressao.id"), nullable=False
    )
    contador: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    mes_referencia: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–12
    ano_referencia: Mapped[int] = mapped_column(Integer, nullable=False)
    # True = lançamento manual pelo fiscal; False = leitura automática SNMP
    manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Observação opcional para lançamentos manuais
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    impressora: Mapped["Impressora"] = relationship(
        "Impressora", back_populates="leituras"
    )
    tipo_impressao: Mapped["TipoImpressao"] = relationship(
        "TipoImpressao", back_populates="leituras"
    )

    def __repr__(self) -> str:
        return (
            f"<Leitura id={self.id} impressora={self.impressora_num_serie} "
            f"contador={self.contador} ref={self.mes_referencia}/{self.ano_referencia}>"
        )