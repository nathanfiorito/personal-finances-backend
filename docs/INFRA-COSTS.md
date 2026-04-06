# Estimativa de Custo Mensal — FinBot

## Cenário: Uso Pessoal (~100 despesas/mês)

| Serviço | Uso Estimado | Custo Free Tier | Custo Após Free Tier |
|---|---|---|---|
| **Render** (FastAPI) | 1 web service always-on | Grátis (750h/mês com spin-down) | $7/mês (Starter) |
| **Supabase** (PostgreSQL) | ~500 registros/mês, < 50MB | Grátis (500MB DB, 1GB storage) | $25/mês (Pro) |
| **OpenRouter** (LLM) | ~100 chamadas extração + categorização | — | ~$0.76/mês |
| **Cloudflare** (DNS/Tunnel) | DNS + tunnel | Grátis | Grátis |
| **Domínio** (opcional) | 1 domínio .com.br | — | ~R$ 40/ano (~R$ 3.3/mês) |
| **Total estimado** | | **~$0.76/mês (~R$ 4.50)** | **~$33/mês (~R$ 190)** |

## Detalhamento OpenRouter

| Agente | Modelo | Chamadas/mês | Input tokens | Output tokens | Custo |
|---|---|---|---|---|---|
| Extrator (imagem) | Sonnet 4.6 ($3/$15 por 1M) | 70 | 105K | 14K | $0.53 |
| Extrator (texto) | Haiku 4.5 ($1/$5 por 1M) | 30 | 15K | 6K | $0.045 |
| Categorizador | Haiku 4.5 ($1/$5 por 1M) | 100 | 30K | 10K | $0.08 |
| Relatórios | Sonnet 4.6 ($3/$15 por 1M) | 4 | 8K | 4K | $0.084 |
| **Subtotal tokens** | | **204** | **158K** | **34K** | **$0.72** |
| **Taxa OpenRouter (5.5%)** | | | | | **$0.04** |
| **Total OpenRouter** | | | | | **$0.76** |

## Notas

### Render Free Tier
- O free tier do Render coloca o serviço em spin-down após 15 minutos de inatividade
- Para um bot pessoal isso pode ser aceitável (cold start de ~30s na primeira mensagem após inatividade)
- Workaround: usar UptimeRobot ou cron externo para pingar o serviço a cada 5 minutos
- Se o cold start incomodar, upgrade para Starter ($7/mês) garante always-on

### Supabase Free Tier
- 500MB de banco é suficiente para anos de uso pessoal (~100 registros/mês × 1KB = ~1.2MB/ano)
- Projetos free pausam após 7 dias de inatividade — precisa de atividade regular (o bot mesmo gera isso)
- Limitado a 2 projetos free por conta

### Quando sairia do Free Tier
- **Render:** se precisar de always-on sem workaround → $7/mês
- **Supabase:** se ultrapassar 500MB de DB ou precisar de backups → $25/mês
- **OpenRouter:** escala linear — se registrar 500 despesas/mês, custo sobe para ~$3.80/mês
- **Cenário realista:** projeto permanece no free tier por 1-2 anos com uso pessoal normal
