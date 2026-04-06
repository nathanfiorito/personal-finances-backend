# Arquitetura — FinBot

## Visão Geral

FinBot é um bot pessoal no Telegram para controle de despesas. Recebe comprovantes de pagamento (foto, PDF ou texto), extrai e categoriza os dados automaticamente usando agentes de IA, e persiste as informações para geração de relatórios financeiros. A arquitetura é um monólito modular em Python/FastAPI, com LLM via OpenRouter e persistência em Supabase (PostgreSQL).

## Componentes Principais

| Componente | Responsabilidade | Tecnologia |
|---|---|---|
| Telegram Webhook | Gateway de entrada — recebe mensagens, fotos e comandos | python-telegram-bot + FastAPI |
| Router | Identifica tipo de entrada (imagem, PDF, texto, comando) e direciona | Python (lógica interna) |
| Agente Extrator | Extrai dados estruturados de comprovantes e textos | Claude Sonnet 4.6 (visão) / Haiku 4.5 (texto) via OpenRouter |
| Agente Categorizador | Classifica a despesa em uma categoria pré-definida | Claude Haiku 4.5 via OpenRouter |
| Confirmador | Apresenta dados extraídos ao usuário e aguarda confirmação | Telegram Inline Keyboards |
| Persistência | Armazena despesas confirmadas | Supabase (PostgreSQL) |
| Relatórios | Gera resumos financeiros por período | Claude Sonnet 4.6 + queries SQL |
| Scheduler | Dispara relatórios automáticos mensais | APScheduler |

## Decisões Arquiteturais

### ADR-001 — Monólito Modular ao invés de Microserviços

- **Status:** Aceita
- **Contexto:** Projeto pessoal, single-user, equipe solo, sem necessidade de escala independente de componentes.
- **Decisão:** Monólito modular com separação clara em módulos Python (agents/, services/, models/).
- **Consequências:** Deploy simples, debugging direto, sem overhead de comunicação inter-serviços. Migração para microserviços possível no futuro se necessário.

### ADR-002 — OpenRouter como Gateway de LLM

- **Status:** Aceita
- **Contexto:** Necessidade de acessar múltiplos modelos Claude (Sonnet para visão, Haiku para categorização) com billing unificado.
- **Decisão:** Usar OpenRouter ao invés de API direta da Anthropic.
- **Consequências:** API compatível com OpenAI SDK, troca de modelo com um parâmetro, billing centralizado. Trade-off: 5.5% de fee na compra de créditos, dependência de intermediário.

### ADR-003 — Webhook direto com Cloudflare Tunnel

- **Status:** Aceita
- **Contexto:** Webhook é mais eficiente que polling para produção, mas requer HTTPS público.
- **Decisão:** Usar Cloudflare Tunnel em dev e Cloudflare (DNS + proxy) em produção para expor o FastAPI.
- **Consequências:** Zero cold start de polling, proteção DDoS gratuita via Cloudflare. Requer configuração inicial do tunnel.

### ADR-004 — Confirmação Obrigatória antes de Persistir

- **Status:** Aceita
- **Contexto:** LLMs podem extrair dados incorretamente, especialmente de comprovantes com layout não padronizado.
- **Decisão:** Sempre apresentar dados extraídos + categoria ao usuário via inline keyboard e persistir somente após confirmação explícita.
- **Consequências:** Zero falsos positivos no banco, UX com um passo extra (aceitável para uso pessoal), necessidade de estado temporário entre extração e confirmação.

### ADR-005 — Supabase como Persistência

- **Status:** Aceita
- **Contexto:** Necessidade de PostgreSQL gerenciado com free tier generoso para uso pessoal.
- **Decisão:** Usar Supabase (free tier: 500MB DB, API REST inclusa).
- **Consequências:** Zero administração de banco, SDK Python disponível, possibilidade de usar API REST direto se necessário. Trade-off: projetos free pausam após 7 dias de inatividade (mitigado pelo uso diário do bot).

### ADR-006 — Dois Modelos LLM (Sonnet + Haiku)

- **Status:** Aceita
- **Contexto:** Extração de imagens requer modelo com visão de alta qualidade; categorização é uma tarefa simples que não justifica modelo caro.
- **Decisão:** Sonnet 4.6 para extração de imagens e geração de relatórios; Haiku 4.5 para categorização e extração de texto simples.
- **Consequências:** Custo otimizado (~$0.76/mês para 100 despesas), latência menor na categorização. Trade-off: duas chamadas de API por despesa com imagem.

## Infraestrutura

```
┌─────────────────────────────────────────────────────┐
│                    Cloudflare                        │
│              (DNS + Proxy + DDoS)                    │
│                                                     │
│   Dev: Cloudflare Tunnel ──► localhost:8000          │
│   Prod: DNS ──► Render (finbot.onrender.com)        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
                       ▼
              ┌────────────────┐
              │  Render (Free) │
              │  FastAPI App   │
              └───────┬────────┘
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
      OpenRouter   Supabase   Telegram API
      (LLM API)   (PostgreSQL) (Bot API)
```

## Fluxos Principais

### Fluxo 1 — Registro de Despesa (Imagem)

1. Usuário envia foto de comprovante no Telegram
2. Webhook recebe a mensagem, baixa a imagem via Telegram API
3. Router identifica como imagem → encaminha ao Agente Extrator
4. Agente Extrator envia imagem ao Sonnet 4.6 via OpenRouter, recebe JSON com dados extraídos
5. Agente Categorizador recebe o JSON → classifica via Haiku 4.5
6. Bot apresenta dados + categoria ao usuário com inline keyboard: [✅ Confirmar] [✏️ Editar] [❌ Cancelar]
7. Usuário confirma → despesa é salva no Supabase
8. Bot responde: "Despesa de R$ 45,90 em Alimentação registrada!"

### Fluxo 2 — Registro de Despesa (Texto)

1. Usuário envia mensagem: "gastei 120 no posto shell"
2. Webhook recebe texto → Router identifica como texto livre
3. Agente Extrator (Haiku 4.5) parseia o texto → JSON estruturado
4. Agente Categorizador classifica → "Transporte"
5. Fluxo de confirmação (mesmo do Fluxo 1, passos 6-8)

### Fluxo 3 — Relatório sob Demanda

1. Usuário envia `/relatorio mensal`
2. Bot consulta despesas do mês corrente no Supabase
3. Agrega dados por categoria (SQL)
4. Envia ao Sonnet 4.6 para gerar resumo em linguagem natural
5. Bot responde com breakdown por categoria + insight do LLM

### Fluxo 4 — Relatório Automático

1. APScheduler dispara no dia 1 de cada mês às 08:00
2. Mesmo fluxo do Relatório sob Demanda, referente ao mês anterior
3. Bot envia mensagem proativamente ao usuário

## Schema do Banco de Dados

```sql
-- Tabela principal de despesas
CREATE TABLE expenses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    valor DECIMAL(10,2) NOT NULL,
    data DATE NOT NULL,
    estabelecimento VARCHAR(255),
    descricao TEXT,
    categoria VARCHAR(100) NOT NULL,
    cnpj VARCHAR(18),
    localizacao VARCHAR(255),
    tipo_entrada VARCHAR(20) NOT NULL, -- 'imagem', 'texto', 'pdf'
    confianca DECIMAL(3,2), -- score de confiança da extração (0.00-1.00)
    dados_raw JSONB, -- JSON completo retornado pelo extrator
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para queries de relatório
CREATE INDEX idx_expenses_data ON expenses(data);
CREATE INDEX idx_expenses_categoria ON expenses(categoria);
CREATE INDEX idx_expenses_data_categoria ON expenses(data, categoria);

-- Tabela de categorias (para customização futura)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descricao TEXT,
    keywords TEXT[], -- palavras-chave para matching
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Considerações de Segurança

- Webhook protegido por `secret_token` do Telegram
- Acesso restrito por `chat_id` (single-user)
- API keys em variáveis de ambiente (nunca no código)
- Dados financeiros não logados em texto plano
- Cloudflare proxy oculta IP real do servidor
- Ver `SECURITY-CHECKLIST.md` para checklist completo

## Escalabilidade e Custos

- **Free Tier:** ~R$ 4.50/mês (apenas OpenRouter)
- **Após Free Tier:** ~R$ 190/mês (Render $7 + Supabase $25 + OpenRouter + domínio)
- **Projeção:** free tier sustenta uso pessoal por 1-2 anos sem problemas
- **Gargalo provável:** Render spin-down (cold start de ~30s) — resolvido com ping periódico ou upgrade para $7/mês
