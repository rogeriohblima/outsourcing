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
    franquias: Mapped[List["FranquiaContrato"]] = relationship(
        "FranquiaContrato", back_populates="contrato", cascade="all, delete-orphan"
    )
    tabelas_preco: Mapped[List["TabelaPreco"]] = relationship(
        "TabelaPreco", back_populates="contrato", cascade="all, delete-orphan"
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
    mes_referencia: Mapped[int] = mapped_column(Integer, nullable=False)
    ano_referencia: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    contrato_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contratos.id"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    contrato: Mapped["Contrato"] = relationship("Contrato", back_populates="faturas")

    def __repr__(self) -> str:
        return f"<Fatura numero={self.numero} ref={self.mes_referencia}/{self.ano_referencia}>"


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
# Modelo de Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class ModeloImpressora(Base):
    """
    Modelo comercial de impressora (ex: HP LaserJet Pro M404n).

    Armazena informações do modelo que podem ser reutilizadas em múltiplas
    impressoras físicas do mesmo modelo.

    fabricante : Fabricante da impressora (ex: HP, Xerox, Ricoh, Canon)
    modelo     : Nome comercial do modelo (ex: LaserJet Pro M404n)
    descricao  : Informações adicionais (velocidade, resolução, etc.)
    """

    __tablename__ = "modelos_impressora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fabricante: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    impressoras: Mapped[List["Impressora"]] = relationship(
        "Impressora", back_populates="modelo"
    )

    def __repr__(self) -> str:
        return f"<ModeloImpressora {self.fabricante} {self.modelo}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Impressora
# ═══════════════════════════════════════════════════════════════════════════════

class Impressora(Base):
    """
    Impressora física monitorada pelo sistema.

    O número de série é a chave primária natural.
    O modelo é selecionado via FK para ModeloImpressora.
    O campo 'ip' é usado para consultas SNMP automáticas.
    O campo 'ativa' indica se a impressora está em operação.
    """

    __tablename__ = "impressoras"

    num_serie: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    tipo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_impressora.id"), nullable=False
    )
    local_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("locais_impressora.id"), nullable=False
    )
    modelo_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("modelos_impressora.id"), nullable=True
    )
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv4 ou IPv6
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    modelo: Mapped[Optional["ModeloImpressora"]] = relationship(
        "ModeloImpressora", back_populates="impressoras"
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
        return f"<Impressora num_serie={self.num_serie}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Tipo de Impressão
# ═══════════════════════════════════════════════════════════════════════════════

class TipoImpressao(Base):
    """
    Categoria de impressão (ex: Preto e Branco A4, Colorido A4).

    Os valores financeiros e franquias ficam em FranquiaContrato e
    TabelaPreco, vinculados ao contrato específico. Isso permite que
    o mesmo tipo de impressão tenha valores diferentes por contrato
    e suporte reajustes com histórico imutável.
    """

    __tablename__ = "tipos_impressao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    leituras: Mapped[List["Leitura"]] = relationship(
        "Leitura", back_populates="tipo_impressao"
    )
    franquias: Mapped[List["FranquiaContrato"]] = relationship(
        "FranquiaContrato", back_populates="tipo_impressao"
    )
    tabelas_preco: Mapped[List["TabelaPreco"]] = relationship(
        "TabelaPreco", back_populates="tipo_impressao"
    )

    def __repr__(self) -> str:
        return f"<TipoImpressao id={self.id} desc={self.descricao}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Franquia do Contrato
# ═══════════════════════════════════════════════════════════════════════════════

class FranquiaContrato(Base):
    """
    Define a franquia de páginas e o custo fixo mensal para um tipo de
    impressão dentro de um contrato específico.

    A franquia é a quantidade TOTAL de páginas contratadas para toda a
    vigência do contrato (não por mês). A OM paga o valor_mensal_franquia
    todos os meses, independente de ter usado ou não as páginas.

    Exemplo:
        contrato 4 anos, P&B A4:
          paginas_franquia      = 500.000 (total no contrato)
          valor_mensal_franquia = R$ 2.000,00 (pago todo mês)

    Os valores por página ficam em TabelaPreco (suporta reajustes).
    """

    __tablename__ = "franquias_contrato"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contrato_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False
    )
    tipo_impressao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_impressao.id"), nullable=False
    )
    # Total de páginas contratadas para toda a vigência
    paginas_franquia: Mapped[int] = mapped_column(Integer, nullable=False)
    # Custo fixo mensal pago independente do uso
    valor_mensal_franquia: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )

    contrato: Mapped["Contrato"] = relationship(
        "Contrato", back_populates="franquias"
    )
    tipo_impressao: Mapped["TipoImpressao"] = relationship(
        "TipoImpressao", back_populates="franquias"
    )

    def __repr__(self) -> str:
        return (
            f"<FranquiaContrato contrato={self.contrato_id} "
            f"tipo={self.tipo_impressao_id} franquia={self.paginas_franquia}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Tabela de Preços (com histórico de reajustes)
# ═══════════════════════════════════════════════════════════════════════════════

class TabelaPreco(Base):
    """
    Valores unitários por página para um tipo de impressão em um contrato.

    Suporta reajustes: quando os preços são reajustados, um novo registro
    é inserido com vigente_de = data do reajuste e o registro anterior
    recebe vigente_ate = data_reajuste - 1 dia.

    Regra de negócio:
      - Apenas um registro com vigente_ate = NULL por (contrato, tipo_impressao)
        — esse é o preço vigente atual.
      - Registros com vigente_ate preenchido são históricos e NUNCA devem
        ser alterados (imutabilidade).
      - O cálculo de um período usa o preço vigente na data_leitura.

    Campos:
      valor_dentro_franquia : preço/página para páginas dentro da franquia total
      valor_fora_franquia   : preço/página para páginas além da franquia total
      vigente_de            : data a partir da qual este preço é válido
      vigente_ate           : data até quando este preço é válido (NULL = atual)
    """

    __tablename__ = "tabelas_preco"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contrato_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False
    )
    tipo_impressao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_impressao.id"), nullable=False
    )
    valor_dentro_franquia: Mapped[Decimal] = mapped_column(
        Numeric(14, 6), nullable=False,
        comment="Preço por página dentro da franquia total do contrato"
    )
    valor_fora_franquia: Mapped[Decimal] = mapped_column(
        Numeric(14, 6), nullable=False,
        comment="Preço por página acima da franquia total do contrato"
    )
    vigente_de: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_ate: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="NULL = preço vigente atual. Nunca alterar registros históricos."
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    contrato: Mapped["Contrato"] = relationship(
        "Contrato", back_populates="tabelas_preco"
    )
    tipo_impressao: Mapped["TipoImpressao"] = relationship(
        "TipoImpressao", back_populates="tabelas_preco"
    )

    def __repr__(self) -> str:
        ate = self.vigente_ate or "atual"
        return (
            f"<TabelaPreco contrato={self.contrato_id} "
            f"tipo={self.tipo_impressao_id} "
            f"dentro={self.valor_dentro_franquia} "
            f"fora={self.valor_fora_franquia} "
            f"de={self.vigente_de} até={ate}>"
        )


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
    contrato_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contratos.id"), nullable=False, index=True,
    )
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

    contrato: Mapped["Contrato"] = relationship("Contrato")
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
