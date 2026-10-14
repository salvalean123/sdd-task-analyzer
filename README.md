# sdd-task-analyzer

Módulo **TaskAnalyzer** desenvolvido com *Spec-Driven Development* (SDD).
O código em `src/task_analyzer.py` foi gerado por assistente de IA a partir do contrato
[`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md), sob as regras de
[`CONTEXT_RULES.md`](CONTEXT_RULES.md), e homologado por revisão humana via Pull Request.

> Bootcamp III, Fase 2: Implementação com IA, Test Harness e Versionamento no GitHub.
> Autor: Mateus Salvato.

## Status do build

| Item | Status |
|------|--------|
| Test Harness (`pytest`) | ✅ 36 passed (100%) |
| Python | 3.11+ |
| Dependências de runtime | nenhuma (somente biblioteca padrão) |

## Estrutura

```
sdd-task-analyzer/
├── README.md                  # Visão geral, execução e status
├── CONTEXT_RULES.md           # Regras de contexto para a IA
├── specs/
│   └── task_analyzer_spec.md  # Especificação SDD (Fase 1, v1.1)
├── tests/
│   └── test_harness.py        # Testes automatizados (pytest)
├── src/
│   └── task_analyzer.py       # Código gerado por IA e homologado
├── .gitignore                 # __pycache__, .pytest_cache, venv
└── requirements.txt           # pytest
```

## Como executar

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
pytest -v
```

## Uso

```python
import sys
sys.path.insert(0, "src")
from task_analyzer import analyze_tasks, TaskValidationError

tarefas = [
    {"id_tarefa": 1, "titulo": "Escrever spec", "status": "concluida", "prioridade": "alta",
     "data_criacao": "2026-01-01T08:00:00", "data_conclusao": "2026-01-01T12:00:00",
     "prazo": "2026-01-01T10:00:00"},
    {"id_tarefa": 2, "titulo": "Configurar CI", "status": "pendente", "prioridade": "baixa",
     "data_criacao": "2026-01-02T08:00:00", "prazo": "2026-01-05T08:00:00"},
]

resultado = analyze_tasks(tarefas)
# resultado["total_tarefas"] == 2
# resultado["tempo_medio_conclusao_horas"] == 4.0
# resultado["taxa_atraso_percentual"] == 100.0
# resultado["indicadores_por_prioridade"]["alta"]["total_concluidas"] == 1
```

Entradas inválidas, como `data_conclusao` anterior a `data_criacao`, disparam
`TaskValidationError` com o `id_tarefa` na mensagem.

## Cobertura do Test Harness

| Cenário da spec | O que é testado |
|-----------------|-----------------|
| Cenário 1: Sucesso | totais, tempo médio e taxa de atraso (geral e por prioridade), uso de `data_inicio`, fusos UTC, arredondamento, imutabilidade da entrada |
| Cenário 2: Exceção | `data_conclusao < data_criacao`, `data_conclusao < data_inicio`, registro em log e 14 entradas inválidas parametrizadas |
| Casos de borda | lista vazia, só pendentes, pendente/cancelada fora da média, prioridade sem concluídas, prazo exato, conclusão imediata |
| CONTEXT_RULES | type hints, docstrings e ausência de `print` |

## Fluxo Git

- `main`: ramo estável; recebe código **apenas via Pull Request**.
- `feature/sdd-specification`: spec e CONTEXT_RULES.
- `feature/task-analyzer-impl`: código gerado via IA.
- `feature/test-harness`: suíte pytest.
- Tag `v0.2.0` marca a entrega da Fase 2.
