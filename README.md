# sdd-task-analyzer

[![CI](https://github.com/salvalean123/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/salvalean123/sdd-task-analyzer/actions/workflows/ci.yml)

Módulo **TaskAnalyzer** desenvolvido com *Spec-Driven Development* (SDD).
O código em `src/task_analyzer.py` foi gerado por assistente de IA a partir do contrato
[`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md), sob as regras de
[`CONTEXT_RULES.md`](CONTEXT_RULES.md), e homologado por revisão humana via Pull Request.

> Bootcamp III, Fase 3: DevOps, Testes Automatizados, Containerização e Governança Ética de IA.
> (Fase 2: Implementação com IA, Test Harness e Versionamento no GitHub.)
> Autor: Mateus Salvato.

## Status do build

| Item | Status |
|------|--------|
| Test Harness (`pytest`) | ✅ 36 passed (100%) |
| CI (GitHub Actions) | ✅ jobs `test` e `docker` a cada push/PR em `main` e `develop` |
| Docker | `python:3.11-slim`, `docker compose run --rm tests` |
| Python | 3.11+ |
| Dependências de runtime | nenhuma (somente biblioteca padrão) |

## Estrutura

```
sdd-task-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Motor CI/CD (GitHub Actions)
├── Dockerfile                        # Empacotamento (python:3.11-slim)
├── docker-compose.yml                # Orquestração dos testes
├── CONTEXT_RULES.md                  # Base de governança (Fase 1)
├── specs/
│   ├── system_design_document.pdf    # Especificação SDD (v1.2) em PDF
│   ├── requirements.yaml             # Requisitos executáveis e rastreabilidade
│   └── task_analyzer_spec.md         # Fonte editável da especificação
├── tests/
│   └── test_harness.py               # Suíte de testes (Fase 2)
├── src/
│   └── task_analyzer.py              # Código gerado por IA e homologado
├── requirements.txt                  # pytest
└── README.md
```

## Como executar

### Com Docker (recomendado)

Um único comando, sem instalar Python na máquina:

```bash
docker compose run --rm tests
```

Ou, sem o Compose:

```bash
docker build -t sdd-task-analyzer .
docker run --rm sdd-task-analyzer
```

### Localmente

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

## Integração Contínua

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em todo `push` e
Pull Request para `main` e `develop`:

1. **`test`**: `ubuntu-latest` + Python 3.11, `pip install -r requirements.txt`,
   `pytest tests/test_harness.py -v`.
2. **`docker`**: build da imagem e execução da suíte dentro do container.

Nenhum PR é mesclado na `main` sem os dois jobs verdes (CONTEXT_RULES §6).

## Fluxo Git

- `main`: ramo estável; recebe código **apenas via Pull Request**.
- `feature/sdd-specification`: spec e CONTEXT_RULES.
- `feature/task-analyzer-impl`: código gerado via IA.
- `feature/test-harness`: suíte pytest.
- `feature/devops-ci-docker`: CI, Docker e governança (Fase 3).
- Tags `v0.2.0` (Fase 2) e `v0.3.0` (Fase 3).
