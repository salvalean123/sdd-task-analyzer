# CONTEXT_RULES: Governança de Contexto para Agentes de IA

> Regras rígidas transpostas da seção 3 da especificação da Fase 1.
> São fornecidas ao assistente de IA **junto** com `specs/task_analyzer_spec.md`
> antes de qualquer pedido de geração de código. Código que viole qualquer regra é rejeitado.

## 1. Diretrizes arquiteturais (obrigatórias)

1. Python **3.11+** como versão mínima.
2. **Type hints** em todas as funções e métodos.
3. Princípio da responsabilidade única (SRP) e código limpo conforme **PEP 8**.
4. Docstrings no padrão **Google style** em módulos, classes e funções.
5. Funções pequenas, coesas e com um único propósito.
6. Tratamento de exceções específico e com mensagens claras. Nunca usar `except Exception` genérico sem justificativa.
7. Logs estruturados com o módulo padrão **`logging`**. Proibido usar `print` para depuração.
8. Nomes de variáveis e funções descritivos.

## 2. Proibições explícitas

1. Não usar bibliotecas externas: somente a biblioteca padrão, salvo `pytest` para testes.
2. Não alterar, remover ou adaptar os cenários de teste da especificação.
3. Não modificar a estrutura de pastas definida na especificação.
4. Não persistir dados em arquivos ou bancos: o módulo opera em memória.
5. Não alterar a assinatura (nome e parâmetros) das funções públicas sem autorização explícita.
6. Não gerar código sem testes automatizados correspondentes.
7. Não duplicar código (DRY).
8. Não assumir comportamentos não especificados. Em caso de dúvida, **sinalizar e pedir esclarecimento** em vez de inferir.

## 3. Regras de interação com a IA

1. Fornecer sempre o contexto completo (especificação + CONTEXT_RULES) antes de pedir código.
2. Validar se a IA entendeu o contrato e os cenários de aceite antes de aceitar o código.
3. Pedir explicações quando houver dúvida sobre a solução proposta.
4. Revisar criticamente todo o código gerado, linha a linha, antes de qualquer commit.
5. Rejeitar e pedir nova geração quando a resposta violar qualquer proibição ou o contrato.

## 4. Plano de homologação humana

Executado em todo Pull Request, nesta ordem:

1. Execução completa dos testes automatizados (`pytest`).
2. Revisão de conformidade com o contrato de negócio (spec) e com este arquivo.
3. Análise de qualidade: legibilidade, tratamento de erros, PEP 8, SRP, type hints e docstrings.
4. Testes manuais complementares em casos de borda não cobertos.
5. Só após aprovação em todos os itens o código é mesclado na `main`.

### Checklist do revisor

- [ ] `pytest` 100% passed
- [ ] Pipeline de CI (GitHub Actions) verde no PR: jobs `test` e `docker`
- [ ] Assinatura `analyze_tasks(tarefas: list[dict[str, Any]]) -> TaskAnalysis` igual à spec
- [ ] Saída com as chaves da seção 1.4 da spec, sem chaves inventadas
- [ ] Somente biblioteca padrão em `src/`
- [ ] Type hints e docstrings Google style em todas as funções
- [ ] `logging` em vez de `print`
- [ ] Nenhuma divisão por zero possível
- [ ] Estrutura de pastas inalterada

## 5. Versionamento

- Branch `main` estável; trabalho em `feature/*`, integrado **somente via Pull Request** revisado.
- Commits pequenos e descritivos, no padrão `tipo: descrição` (`feat:`, `test:`, `docs:`, `chore:`).
- Tag de release ao fim de cada fase (`v0.2.0` = Fase 2, `v0.3.0` = Fase 3).

## 6. Infraestrutura e DevOps (Fase 3)

1. Todo `push` e todo Pull Request para `main` ou `develop` disparam o pipeline `.github/workflows/ci.yml`.
2. **Nenhum merge na `main` com pipeline vermelho.** O green build é pré-requisito da homologação humana, não substituto dela.
3. A imagem Docker parte **somente** da imagem oficial `python:3.11-slim`. Proibido usar imagens de terceiros não verificadas.
4. O container roda com usuário sem privilégios (sem `root`) e não guarda segredos, tokens ou chaves.
5. Arquivos de infraestrutura (`Dockerfile`, `docker-compose.yml`, `ci.yml`) gerados por IA passam pelo mesmo checklist e revisão humana que o código.
6. Nenhuma dependência nova entra em `requirements.txt` sem atualização da spec e aprovação humana.
7. Mudanças na estrutura de pastas (§2.3) só com nova versão da spec e aprovação explícita do arquiteto (ver spec v1.2).
