# MVP Roadmap — Personal Finances

## Priorização (MoSCoW)

| Feature | Prioridade | Status | Dependência |
|---|---|---|---|
| Webhook Telegram (receber foto/texto) | Must-have | ✅ Concluído | — |
| Agente Extrator (Sonnet 4.6 com visão) | Must-have | ✅ Concluído | Webhook |
| Agente Categorizador (Haiku 4.5) | Must-have | ✅ Concluído | Extrator |
| Fluxo de confirmação via Telegram (inline keyboards) | Must-have | ✅ Concluído | Categorizador |
| Persistência em PostgreSQL (Supabase) | Must-have | ✅ Concluído | Confirmação |
| Comando `/relatorio` (semanal/mensal) | Should-have | ✅ Concluído | Persistência |
| Relatório automático mensal (cron/scheduler) | Should-have | ✅ Concluído | Relatório |
| Suporte a PDF de NF-e | Should-have | ✅ Concluído | Extrator |
| Comando `/categorias` (listar/adicionar categorias) | Could-have | ✅ Concluído | Persistência |
| Exportação CSV (`/exportar`) | Could-have | ✅ Concluído | Persistência |
| Verificação de duplicatas via LLM | Could-have | ✅ Concluído | Persistência |
| Dashboard web com gráficos | Could-have | 🔜 Em planejamento | Persistência |
| Multi-usuário / auth | Won't-have | — | — |
| Integração Google Sheets | Won't-have | — | — |

## Categorias Padrão (v1)

Categorias pré-definidas para o Agente Categorizador (customizáveis via `/categorias add`):

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

## Próximas Etapas

- **Dashboard web** — interface visual para visualização de despesas e gráficos (em planejamento)

## Definição de "Pronto" (DoD)

Uma feature é considerada pronta quando:

- Código funcional e testado manualmente
- Tratamento de erros básico implementado
- Testes automatizados cobrindo os fluxos principais
- Commit no repositório com mensagem descritiva
