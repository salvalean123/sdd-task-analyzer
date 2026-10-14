"""TaskAnalyzer: métricas de produtividade a partir de uma lista de tarefas.

Implementa o contrato de ``specs/task_analyzer_spec.md`` (v1.1). O código foi
gerado com assistente de IA sob as regras de ``CONTEXT_RULES.md`` e homologado
por revisão humana.

Exemplo:
    >>> analyze_tasks([])["sem_dados"]
    True
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Final, TypedDict

logger = logging.getLogger(__name__)

STATUS_CONCLUIDA: Final[str] = "concluida"
STATUS_PENDENTE: Final[str] = "pendente"
STATUS_CANCELADA: Final[str] = "cancelada"
STATUS_VALIDOS: Final[tuple[str, ...]] = (STATUS_CONCLUIDA, STATUS_PENDENTE, STATUS_CANCELADA)
PRIORIDADES_VALIDAS: Final[tuple[str, ...]] = ("baixa", "media", "alta")
CAMPOS_OBRIGATORIOS: Final[tuple[str, ...]] = (
    "id_tarefa", "titulo", "data_criacao", "prazo", "prioridade", "status",
)
SEGUNDOS_POR_HORA: Final[float] = 3600.0
CASAS_DECIMAIS: Final[int] = 2


class TaskValidationError(ValueError):
    """Erro disparado quando uma tarefa de entrada viola o contrato da spec.

    Attributes:
        id_tarefa: Identificador da tarefa inválida, ou ``None`` quando o erro
            não se refere a uma tarefa específica.
    """

    def __init__(self, mensagem: str, id_tarefa: Any = None) -> None:
        """Monta a mensagem de erro identificando a tarefa.

        Args:
            mensagem: Descrição clara da violação.
            id_tarefa: Identificador da tarefa inválida, se houver.
        """
        self.id_tarefa: Any = id_tarefa
        prefixo = f"[tarefa {id_tarefa!r}] " if id_tarefa is not None else ""
        super().__init__(f"{prefixo}{mensagem}")


class IndicadoresPrioridade(TypedDict):
    """Métricas de um grupo de tarefas (uma prioridade)."""

    total_tarefas: int
    total_concluidas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float


class TaskAnalysis(TypedDict):
    """Resultado de ``analyze_tasks`` (seção 1.4 da spec)."""

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    total_canceladas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    sem_dados: bool
    indicadores_por_prioridade: dict[str, IndicadoresPrioridade]


@dataclass(frozen=True)
class _TarefaValidada:
    """Tarefa já validada, reduzida ao necessário para o cálculo.

    Attributes:
        prioridade: Prioridade da tarefa.
        status: Status da tarefa.
        horas_conclusao: Tempo de conclusão em horas (só para concluídas).
        atrasada: ``True`` se concluída depois do prazo.
    """

    prioridade: str
    status: str
    horas_conclusao: float | None
    atrasada: bool


def _falha(mensagem: str, id_tarefa: Any = None) -> TaskValidationError:
    """Registra a violação no log e devolve a exceção a ser lançada.

    Args:
        mensagem: Descrição da violação.
        id_tarefa: Identificador da tarefa inválida, se houver.

    Returns:
        Exceção ``TaskValidationError`` pronta para ``raise``.
    """
    logger.warning("Tarefa inválida: %s (id_tarefa=%r)", mensagem, id_tarefa)
    return TaskValidationError(mensagem, id_tarefa)


def _converter_data(valor: Any, campo: str, id_tarefa: Any) -> datetime:
    """Converte ``datetime`` ou texto ISO 8601 para ``datetime`` UTC sem fuso.

    Args:
        valor: Valor recebido no campo de data.
        campo: Nome do campo (para a mensagem de erro).
        id_tarefa: Identificador da tarefa (para a mensagem de erro).

    Returns:
        Data em UTC, sem ``tzinfo``. Datas sem fuso são tratadas como UTC.

    Raises:
        TaskValidationError: Se o valor não for uma data válida.
    """
    if isinstance(valor, datetime):
        data = valor
    elif isinstance(valor, str):
        try:
            data = datetime.fromisoformat(valor)
        except ValueError as erro:
            raise _falha(f"campo '{campo}' com data inválida: {valor!r}", id_tarefa) from erro
    else:
        raise _falha(f"campo '{campo}' deve ser datetime ou texto ISO 8601", id_tarefa)
    if data.tzinfo is not None:
        data = data.astimezone(timezone.utc).replace(tzinfo=None)
    return data


def _converter_data_opcional(valor: Any, campo: str, id_tarefa: Any) -> datetime | None:
    """Converte uma data opcional, preservando ``None``.

    Args:
        valor: Valor recebido no campo de data, ou ``None``.
        campo: Nome do campo.
        id_tarefa: Identificador da tarefa.

    Returns:
        Data convertida, ou ``None`` se o campo não foi informado.
    """
    if valor is None:
        return None
    return _converter_data(valor, campo, id_tarefa)


def _validar_campos_obrigatorios(tarefa: dict[str, Any]) -> None:
    """Garante que todos os campos obrigatórios estão presentes.

    Args:
        tarefa: Tarefa recebida.

    Raises:
        TaskValidationError: Se algum campo obrigatório estiver ausente ou ``None``.
    """
    for campo in CAMPOS_OBRIGATORIOS:
        if tarefa.get(campo) is None:
            raise _falha(f"campo obrigatório ausente: '{campo}'", tarefa.get("id_tarefa"))


def _validar_identificacao(tarefa: dict[str, Any], ids_vistos: set[int]) -> None:
    """Valida ``id_tarefa`` (inteiro positivo e único) e ``titulo`` (não vazio).

    Args:
        tarefa: Tarefa recebida.
        ids_vistos: Identificadores já processados; é atualizado com o atual.

    Raises:
        TaskValidationError: Se o id ou o título forem inválidos.
    """
    id_tarefa = tarefa["id_tarefa"]
    if isinstance(id_tarefa, bool) or not isinstance(id_tarefa, int) or id_tarefa <= 0:
        raise _falha("id_tarefa deve ser um inteiro positivo", id_tarefa)
    if id_tarefa in ids_vistos:
        raise _falha("id_tarefa duplicado", id_tarefa)
    ids_vistos.add(id_tarefa)

    titulo = tarefa["titulo"]
    if not isinstance(titulo, str) or not titulo.strip():
        raise _falha("titulo não pode ser vazio", id_tarefa)


def _validar_enums(tarefa: dict[str, Any]) -> None:
    """Valida ``prioridade`` e ``status`` contra os valores permitidos.

    Args:
        tarefa: Tarefa recebida.

    Raises:
        TaskValidationError: Se algum valor estiver fora do enum.
    """
    id_tarefa = tarefa["id_tarefa"]
    if tarefa["prioridade"] not in PRIORIDADES_VALIDAS:
        raise _falha(
            f"prioridade inválida: {tarefa['prioridade']!r} (use 'baixa', 'media' ou 'alta')",
            id_tarefa,
        )
    if tarefa["status"] not in STATUS_VALIDOS:
        raise _falha(
            f"status inválido: {tarefa['status']!r} "
            "(use 'concluida', 'pendente' ou 'cancelada')",
            id_tarefa,
        )


def _calcular_conclusao(tarefa: dict[str, Any]) -> tuple[float | None, bool]:
    """Valida as datas e calcula o tempo de conclusão e o atraso (RN01–RN03).

    Args:
        tarefa: Tarefa com campos obrigatórios já validados.

    Returns:
        Tupla ``(horas_conclusao, atrasada)``. Para tarefas não concluídas,
        retorna ``(None, False)``.

    Raises:
        TaskValidationError: Se alguma data for inválida ou inconsistente.
    """
    id_tarefa = tarefa["id_tarefa"]
    data_criacao = _converter_data(tarefa["data_criacao"], "data_criacao", id_tarefa)
    prazo = _converter_data(tarefa["prazo"], "prazo", id_tarefa)
    data_inicio = _converter_data_opcional(tarefa.get("data_inicio"), "data_inicio", id_tarefa)
    data_conclusao = _converter_data_opcional(
        tarefa.get("data_conclusao"), "data_conclusao", id_tarefa
    )

    if tarefa["status"] != STATUS_CONCLUIDA:
        return None, False

    if data_conclusao is None:
        raise _falha("tarefa concluida sem data_conclusao", id_tarefa)
    if data_conclusao < data_criacao:
        raise _falha(
            f"data_conclusao ({data_conclusao.isoformat()}) anterior a "
            f"data_criacao ({data_criacao.isoformat()})",
            id_tarefa,
        )
    inicio_efetivo = data_inicio if data_inicio is not None else data_criacao
    if data_conclusao < inicio_efetivo:
        raise _falha(
            f"data_conclusao ({data_conclusao.isoformat()}) anterior a "
            f"data_inicio ({inicio_efetivo.isoformat()})",
            id_tarefa,
        )

    horas = (data_conclusao - inicio_efetivo).total_seconds() / SEGUNDOS_POR_HORA
    return horas, data_conclusao > prazo


def _validar_tarefa(tarefa: Any, posicao: int, ids_vistos: set[int]) -> _TarefaValidada:
    """Aplica todas as validações da seção 1.6 da spec a uma tarefa.

    Args:
        tarefa: Item recebido na lista de entrada.
        posicao: Posição do item na lista (para a mensagem de erro).
        ids_vistos: Identificadores já processados.

    Returns:
        Tarefa validada, pronta para o cálculo das métricas.

    Raises:
        TaskValidationError: Se a tarefa violar o contrato.
    """
    if not isinstance(tarefa, dict):
        raise _falha(f"item na posição {posicao} não é um dicionário")
    _validar_campos_obrigatorios(tarefa)
    _validar_identificacao(tarefa, ids_vistos)
    _validar_enums(tarefa)
    horas_conclusao, atrasada = _calcular_conclusao(tarefa)
    return _TarefaValidada(
        prioridade=tarefa["prioridade"],
        status=tarefa["status"],
        horas_conclusao=horas_conclusao,
        atrasada=atrasada,
    )


def _media(valores: list[float]) -> float:
    """Calcula a média sem risco de divisão por zero (RN05).

    Args:
        valores: Valores a serem somados.

    Returns:
        Média arredondada em 2 casas, ou ``0.0`` para lista vazia.
    """
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), CASAS_DECIMAIS)


def _percentual(parte: int, total: int) -> float:
    """Calcula um percentual sem risco de divisão por zero (RN05).

    Args:
        parte: Quantidade de interesse.
        total: Quantidade de referência.

    Returns:
        Percentual arredondado em 2 casas, ou ``0.0`` quando ``total`` é zero.
    """
    if total == 0:
        return 0.0
    return round(parte / total * 100, CASAS_DECIMAIS)


def _calcular_indicadores(tarefas: list[_TarefaValidada]) -> IndicadoresPrioridade:
    """Calcula as métricas de um grupo de tarefas validadas.

    Args:
        tarefas: Tarefas do grupo (todas, ou de uma prioridade).

    Returns:
        Totais, tempo médio de conclusão e taxa de atraso do grupo.
    """
    horas = [t.horas_conclusao for t in tarefas if t.horas_conclusao is not None]
    atrasadas = sum(1 for t in tarefas if t.atrasada)
    return IndicadoresPrioridade(
        total_tarefas=len(tarefas),
        total_concluidas=len(horas),
        tempo_medio_conclusao_horas=_media(horas),
        taxa_atraso_percentual=_percentual(atrasadas, len(horas)),
    )


def _contar_status(tarefas: list[_TarefaValidada], status: str) -> int:
    """Conta as tarefas com um determinado status.

    Args:
        tarefas: Tarefas validadas.
        status: Status a contar.

    Returns:
        Quantidade de tarefas com o status informado.
    """
    return sum(1 for t in tarefas if t.status == status)


def analyze_tasks(tarefas: list[dict[str, Any]]) -> TaskAnalysis:
    """Calcula as métricas de produtividade definidas na especificação SDD.

    Args:
        tarefas: Lista de tarefas (campos na seção 1.3 da spec). A lista não é alterada.

    Returns:
        Métricas gerais e por prioridade (seção 1.4 da spec).

    Raises:
        TaskValidationError: Se qualquer tarefa violar o contrato (seção 1.6 da spec).
    """
    if not isinstance(tarefas, list):
        raise _falha("a entrada deve ser uma lista de tarefas")

    ids_vistos: set[int] = set()
    validadas = [
        _validar_tarefa(tarefa, posicao, ids_vistos) for posicao, tarefa in enumerate(tarefas)
    ]

    geral = _calcular_indicadores(validadas)
    por_prioridade = {
        prioridade: _calcular_indicadores([t for t in validadas if t.prioridade == prioridade])
        for prioridade in PRIORIDADES_VALIDAS
    }
    sem_dados = geral["total_concluidas"] == 0
    if sem_dados:
        logger.info("Nenhuma tarefa concluída: métricas de tempo e atraso zeradas")
    logger.info(
        "Análise concluída: %d tarefas, %d concluídas",
        geral["total_tarefas"], geral["total_concluidas"],
    )

    return TaskAnalysis(
        total_tarefas=geral["total_tarefas"],
        total_concluidas=geral["total_concluidas"],
        total_pendentes=_contar_status(validadas, STATUS_PENDENTE),
        total_canceladas=_contar_status(validadas, STATUS_CANCELADA),
        tempo_medio_conclusao_horas=geral["tempo_medio_conclusao_horas"],
        taxa_atraso_percentual=geral["taxa_atraso_percentual"],
        sem_dados=sem_dados,
        indicadores_por_prioridade=por_prioridade,
    )
