# MVP Roadmap — FinBot

## Priorização (MoSCoW)

| Feature | Prioridade | Fase | Estimativa | Dependência |
|---|---|---|---|---|
| Webhook Telegram (receber foto/texto) | Must-have | MVP | 2d | — |
| Agente Extrator (Sonnet 4.6 com visão) | Must-have | MVP | 3d | Webhook |
| Agente Categorizador (Haiku 4.5) | Must-have | MVP | 2d | Extrator |
| Fluxo de confirmação via Telegram (inline keyboards) | Must-have | MVP | 2d | Categorizador |
| Persistência em PostgreSQL (Supabase) | Must-have | MVP | 2d | Confirmação |
| Comando `/relatorio` (semanal/mensal) | Should-have | MVP | 3d | Persistência |
| Relatório automático mensal (cron/scheduler) | Should-have | MVP | 1d | Relatório |
| Suporte a PDF de NF-e | Should-have | MVP | 2d | Extrator |
| Comando `/categorias` (listar/editar categorias) | Could-have | Pós-MVP | 2d | Persistência |
| Dashboard web com gráficos | Could-have | Pós-MVP | 5d | Persistência |
| Exportação CSV/Excel | Could-have | Pós-MVP | 1d | Persistência |
| Multi-usuário / auth | Won't-have | Futuro | — | — |
| Integração Google Sheets | Won't-have | Futuro | — | — |

## Estimativa Total

- **MVP (Must + Should):** ~17 dias úteis
- **Pós-MVP (Could):** ~8 dias úteis adicionais

## Categorias Padrão (v1)

Categorias pré-definidas para o Agente Categorizador:

1. **Alimentação** — supermercado, restaurante, delivery, padaria
2. **Transporte** — combustível, estacionamento, pedágio, transporte público, app de corrida
3. **Moradia** — aluguel, condomínio, energia, água, gás, internet
4. **Saúde** — farmácia, consulta médica, plano de saúde, exames
5. **Educação** — cursos, livros, assinaturas educacionais
6. **Lazer** — streaming, jogos, viagens, eventos
7. **Vestuário** — roupas, calçados, acessórios
8. **Serviços** — assinaturas digitais, manutenção, reparos
9. **Pets** — ração, veterinário, acessórios
10. **Outros** — fallback quando nenhuma categoria se aplica

> O usuário poderá futuramente criar/editar categorias via `/categorias` (Pós-MVP).

## Definição de "Pronto" (DoD)

Uma feature é considerada pronta quando:

- Código funcional e testado manualmente
- Tratamento de erros básico implementado
- Documentação mínima no código (docstrings)
- Commit no repositório com mensagem descritiva
