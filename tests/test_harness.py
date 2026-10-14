"""Test Harness do TaskAnalyzer.

Cada teste traduz um cenário de aceite de ``specs/task_analyzer_spec.md``.
Execução, na raiz do repositório: ``pytest -v``.
"""

import copy
import inspect
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

# A estrutura de pastas da spec não prevê pacote nem arquivo de configuração,
# então o diretório src/ é adicionado ao caminho de importação aqui.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import task_analyzer  # noqa: E402
from task_analyzer import TaskValidationError, analyze_tasks  # noqa: E402

ZERADO: dict[str, Any] = {
    "total_tarefas": 0,
    "total_concluidas": 0,
    "tempo_medio_conclusao_horas": 0.0,
    "taxa_atraso_percentual": 0.0,
}


@pytest.fixture
def tarefas_cenario_1() -> list[dict[str, Any]]:
    """Dado: 4 concluídas (1 atrasada), 1 pendente e 1 cancelada."""
    return [
        {   # alta, 4h, no prazo
            "id_tarefa": 1, "titulo": "Configurar repositório", "status": "concluida",
            "prioridade": "alta", "data_criacao": "2026-01-01T08:00:00",
            "data_conclusao": "2026-01-01T12:00:00", "prazo": "2026-01-01T18:00:00",
        },
        {   # alta, 8h contadas a partir de data_inicio, ATRASADA
            "id_tarefa": 2, "titulo": "Escrever especificação", "status": "concluida",
            "prioridade": "alta", "data_criacao": "2026-01-02T08:00:00",
            "data_inicio": "2026-01-02T10:00:00", "data_conclusao": "2026-01-02T18:00:00",
            "prazo": "2026-01-02T12:00:00",
        },
        {   # media, 24h, no prazo
            "id_tarefa": 3, "titulo": "Gerar código via IA", "status": "concluida",
            "prioridade": "media", "data_criacao": "2026-01-03T09:00:00",
            "data_conclusao": "2026-01-04T09:00:00", "prazo": "2026-01-05T09:00:00",
        },
        {   # baixa, 2h, no prazo
            "id_tarefa": 4, "titulo": "Atualizar README", "status": "concluida",
            "prioridade": "baixa", "data_criacao": "2026-01-04T10:00:00",
            "data_conclusao": "2026-01-04T12:00:00", "prazo": "2026-01-04T18:00:00",
        },
        {
            "id_tarefa": 5, "titulo": "Configurar CI", "status": "pendente",
            "prioridade": "media", "data_criacao": "2026-01-05T08:00:00",
            "prazo": "2026-01-10T08:00:00",
        },
        {
            "id_tarefa": 6, "titulo": "Migrar banco", "status": "cancelada",
            "prioridade": "baixa", "data_criacao": "2026-01-06T08:00:00",
            "prazo": "2026-01-10T08:00:00",
        },
    ]


def _tarefa(**campos: Any) -> dict[str, Any]:
    """Cria uma tarefa concluída válida (2h, no prazo), sobrescrevendo os campos informados."""
    base: dict[str, Any] = {
        "id_tarefa": 1, "titulo": "Tarefa de teste", "status": "concluida",
        "prioridade": "alta", "data_criacao": "2026-01-01T08:00:00",
        "data_conclusao": "2026-01-01T10:00:00", "prazo": "2026-01-02T08:00:00",
    }
    base.update(campos)
    return base


# ---------------------------------------------------------------------------
# Cenário 1: Sucesso
# ---------------------------------------------------------------------------

def test_cenario1_totais(tarefas_cenario_1: list[dict[str, Any]]) -> None:
    resultado = analyze_tasks(tarefas_cenario_1)
    assert resultado["total_tarefas"] == 6
    assert resultado["total_concluidas"] == 4
    assert resultado["total_pendentes"] == 1
    assert resultado["total_canceladas"] == 1
    assert resultado["sem_dados"] is False


def test_cenario1_tempo_medio_geral(tarefas_cenario_1: list[dict[str, Any]]) -> None:
    # (4 + 8 + 24 + 2) / 4 = 9.5
    assert analyze_tasks(tarefas_cenario_1)["tempo_medio_conclusao_horas"] == pytest.approx(9.5)


def test_cenario1_taxa_atraso_geral(tarefas_cenario_1: list[dict[str, Any]]) -> None:
    # 1 atrasada de 4 concluídas
    assert analyze_tasks(tarefas_cenario_1)["taxa_atraso_percentual"] == pytest.approx(25.0)


def test_cenario1_indicadores_por_prioridade(tarefas_cenario_1: list[dict[str, Any]]) -> None:
    por_prioridade = analyze_tasks(tarefas_cenario_1)["indicadores_por_prioridade"]
    assert por_prioridade == {
        "alta": {
            "total_tarefas": 2, "total_concluidas": 2,
            "tempo_medio_conclusao_horas": pytest.approx(6.0),
            "taxa_atraso_percentual": pytest.approx(50.0),
        },
        "media": {
            "total_tarefas": 2, "total_concluidas": 1,
            "tempo_medio_conclusao_horas": pytest.approx(24.0),
            "taxa_atraso_percentual": 0.0,
        },
        "baixa": {
            "total_tarefas": 2, "total_concluidas": 1,
            "tempo_medio_conclusao_horas": pytest.approx(2.0),
            "taxa_atraso_percentual": 0.0,
        },
    }


def test_cenario1_saida_tem_exatamente_as_chaves_da_spec(
    tarefas_cenario_1: list[dict[str, Any]],
) -> None:
    assert set(analyze_tasks(tarefas_cenario_1)) == {
        "total_tarefas", "total_concluidas", "total_pendentes", "total_canceladas",
        "tempo_medio_conclusao_horas", "taxa_atraso_percentual", "sem_dados",
        "indicadores_por_prioridade",
    }


def test_cenario1_usa_data_inicio_quando_informada() -> None:
    tarefa = _tarefa(data_inicio="2026-01-01T09:00:00")  # conclusão às 10:00
    assert analyze_tasks([tarefa])["tempo_medio_conclusao_horas"] == pytest.approx(1.0)


def test_cenario1_aceita_datetime_e_converte_fusos_para_utc() -> None:
    tarefas = [
        _tarefa(id_tarefa=1, data_criacao=datetime(2026, 1, 1, 8),
                data_conclusao=datetime(2026, 1, 1, 11)),  # 3h
        # 11:00Z até 10:00-03:00 (= 13:00Z): 2h
        _tarefa(id_tarefa=2, data_criacao="2026-01-01T11:00:00Z",
                data_conclusao="2026-01-01T10:00:00-03:00"),
    ]
    assert analyze_tasks(tarefas)["tempo_medio_conclusao_horas"] == pytest.approx(2.5)


def test_cenario1_arredonda_para_duas_casas() -> None:
    tarefas = [
        _tarefa(id_tarefa=1, data_conclusao="2026-01-01T09:00:00"),  # 1h
        _tarefa(id_tarefa=2, data_conclusao="2026-01-01T09:00:00"),  # 1h
        _tarefa(id_tarefa=3, data_conclusao="2026-01-01T10:00:00"),  # 2h
    ]
    assert analyze_tasks(tarefas)["tempo_medio_conclusao_horas"] == 1.33


def test_cenario1_nao_altera_a_entrada(tarefas_cenario_1: list[dict[str, Any]]) -> None:
    original = copy.deepcopy(tarefas_cenario_1)
    analyze_tasks(tarefas_cenario_1)
    assert tarefas_cenario_1 == original


# ---------------------------------------------------------------------------
# Cenário 2: Exceção / Erro
# ---------------------------------------------------------------------------

def test_cenario2_data_conclusao_anterior_a_criacao_dispara_erro() -> None:
    tarefa = _tarefa(id_tarefa=99, data_criacao="2026-01-10T08:00:00",
                     data_conclusao="2026-01-09T08:00:00", prazo="2026-01-11T08:00:00")
    with pytest.raises(TaskValidationError, match="anterior a data_criacao") as erro:
        analyze_tasks([tarefa])
    assert erro.value.id_tarefa == 99
    assert "99" in str(erro.value)


def test_cenario2_data_conclusao_anterior_a_inicio_dispara_erro() -> None:
    tarefa = _tarefa(data_inicio="2026-01-01T12:00:00", data_conclusao="2026-01-01T10:00:00")
    with pytest.raises(TaskValidationError, match="anterior a data_inicio"):
        analyze_tasks([tarefa])


def test_cenario2_erro_e_subclasse_de_value_error() -> None:
    assert issubclass(TaskValidationError, ValueError)


def test_cenario2_erro_e_registrado_no_log(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger=task_analyzer.__name__):
        with pytest.raises(TaskValidationError):
            analyze_tasks([_tarefa(prioridade="urgente")])
    assert "prioridade inválida" in caplog.text


@pytest.mark.parametrize(
    ("entrada", "trecho_mensagem"),
    [
        pytest.param("não é lista", "lista de tarefas", id="entrada-nao-lista"),
        pytest.param(["texto"], "não é um dicionário", id="item-nao-dict"),
        pytest.param([_tarefa(prazo=None)], "obrigatório ausente: 'prazo'", id="campo-ausente"),
        pytest.param([_tarefa(id_tarefa="1")], "inteiro positivo", id="id-texto"),
        pytest.param([_tarefa(id_tarefa=True)], "inteiro positivo", id="id-booleano"),
        pytest.param([_tarefa(id_tarefa=0)], "inteiro positivo", id="id-zero"),
        pytest.param([_tarefa(id_tarefa=-5)], "inteiro positivo", id="id-negativo"),
        pytest.param([_tarefa(id_tarefa=7), _tarefa(id_tarefa=7)], "duplicado", id="id-duplicado"),
        pytest.param([_tarefa(titulo="   ")], "titulo não pode ser vazio", id="titulo-vazio"),
        pytest.param([_tarefa(prioridade="urgente")], "prioridade inválida", id="prioridade-fora-enum"),
        pytest.param([_tarefa(status="feita")], "status inválido", id="status-fora-enum"),
        pytest.param([_tarefa(data_criacao="01/01/2026")], "data inválida", id="data-malformada"),
        pytest.param([_tarefa(prazo=20260101)], "ISO 8601", id="data-tipo-errado"),
        pytest.param([_tarefa(data_conclusao=None)], "sem data_conclusao", id="concluida-sem-data"),
    ],
)
def test_cenario2_entradas_invalidas_disparam_task_validation_error(
    entrada: Any, trecho_mensagem: str
) -> None:
    with pytest.raises(TaskValidationError, match=trecho_mensagem):
        analyze_tasks(entrada)


# ---------------------------------------------------------------------------
# Casos de borda
# ---------------------------------------------------------------------------

def test_borda_lista_vazia_retorna_metricas_zeradas_sem_excecao() -> None:
    assert analyze_tasks([]) == {
        "total_tarefas": 0,
        "total_concluidas": 0,
        "total_pendentes": 0,
        "total_canceladas": 0,
        "tempo_medio_conclusao_horas": 0.0,
        "taxa_atraso_percentual": 0.0,
        "sem_dados": True,
        "indicadores_por_prioridade": {"baixa": ZERADO, "media": ZERADO, "alta": ZERADO},
    }


def test_borda_apenas_pendentes_retorna_medias_zeradas() -> None:
    tarefas = [
        _tarefa(id_tarefa=1, status="pendente", data_conclusao=None),
        _tarefa(id_tarefa=2, status="pendente", data_conclusao=None, prioridade="baixa"),
    ]
    resultado = analyze_tasks(tarefas)
    assert resultado["total_tarefas"] == 2
    assert resultado["total_pendentes"] == 2
    assert resultado["total_concluidas"] == 0
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0
    assert resultado["sem_dados"] is True


def test_borda_pendente_e_cancelada_nao_entram_em_media_nem_atraso() -> None:
    tarefas = [
        _tarefa(id_tarefa=1),  # concluída: 2h, no prazo
        # pendente e cancelada com prazo já vencido: não contam como atraso
        _tarefa(id_tarefa=2, status="pendente", data_conclusao=None, prazo="2026-01-01T09:00:00"),
        _tarefa(id_tarefa=3, status="cancelada", data_conclusao=None, prazo="2026-01-01T09:00:00"),
    ]
    resultado = analyze_tasks(tarefas)
    assert resultado["total_tarefas"] == 3
    assert resultado["tempo_medio_conclusao_horas"] == pytest.approx(2.0)
    assert resultado["taxa_atraso_percentual"] == 0.0


def test_borda_prioridade_sem_concluidas_retorna_zero_sem_divisao_por_zero() -> None:
    por_prioridade = analyze_tasks([_tarefa(prioridade="alta")])["indicadores_por_prioridade"]
    assert por_prioridade["media"] == ZERADO
    assert por_prioridade["baixa"] == ZERADO


def test_borda_conclusao_exatamente_no_prazo_nao_e_atraso() -> None:
    tarefa = _tarefa(data_conclusao="2026-01-01T10:00:00", prazo="2026-01-01T10:00:00")
    assert analyze_tasks([tarefa])["taxa_atraso_percentual"] == 0.0


def test_borda_conclusao_imediata_tem_zero_horas() -> None:
    tarefa = _tarefa(data_conclusao="2026-01-01T08:00:00")
    assert analyze_tasks([tarefa])["tempo_medio_conclusao_horas"] == 0.0


# ---------------------------------------------------------------------------
# Aderência às CONTEXT_RULES
# ---------------------------------------------------------------------------

def _funcoes_do_modulo() -> list[Any]:
    """Lista as funções e métodos definidos em src/task_analyzer.py."""
    funcoes = [
        objeto for _, objeto in inspect.getmembers(task_analyzer, inspect.isfunction)
        if objeto.__module__ == task_analyzer.__name__
    ]
    funcoes.append(TaskValidationError.__init__)
    return funcoes


def test_context_rules_type_hints_em_todas_as_funcoes() -> None:
    for funcao in _funcoes_do_modulo():
        assinatura = inspect.signature(funcao)
        for nome, parametro in assinatura.parameters.items():
            if nome == "self":
                continue
            assert parametro.annotation is not inspect.Parameter.empty, (
                f"{funcao.__qualname__}: parâmetro '{nome}' sem type hint"
            )
        assert assinatura.return_annotation is not inspect.Signature.empty, (
            f"{funcao.__qualname__}: retorno sem type hint"
        )


def test_context_rules_docstrings_em_todas_as_funcoes() -> None:
    for funcao in _funcoes_do_modulo():
        assert inspect.getdoc(funcao), f"{funcao.__qualname__} sem docstring"


def test_context_rules_sem_print_no_codigo_fonte() -> None:
    codigo = Path(inspect.getfile(task_analyzer)).read_text(encoding="utf-8")
    assert "print(" not in codigo
