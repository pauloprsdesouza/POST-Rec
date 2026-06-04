# SDD — Spec-Driven Development

# POST-Rec Alpha Validation MVP

## 1. Nome do projeto

**POST-Rec — Paper-Oriented Scientific Topic Recommender**

Versão deste documento:

```text id="b02mtb"
POST-Rec Alpha Validation MVP
```

---

# 2. Visão geral

O **POST-Rec** é uma plataforma inteligente para recomendar, ranquear e documentar oportunidades de pesquisa científica a partir de tópicos informados pelo usuário.

O sistema recebe temas-semente como:

```text id="o96z1g"
Generative AI in recommender systems
LLM-based personalization
RAG for explainable recommendations
Agentic recommender systems
```

e retorna recomendações estruturadas contendo:

* título sugerido;
* gap científico;
* pergunta de pesquisa;
* hipótese;
* método proposto;
* artigos relacionados;
* datasets sugeridos;
* métricas de avaliação;
* plano experimental;
* riscos;
* score de relevância;
* score de originalidade;
* score de viabilidade;
* score final;
* nível de confiança;
* custo estimado da execução;
* status de revisão;
* exportação em Markdown.

Esta versão do SDD adiciona uma camada essencial:

```text id="pzgzyr"
Módulo de Validação com Voluntários
```

O objetivo é testar se o sistema responde de acordo com as expectativas de usuários reais, por meio de:

* captura de expectativa antes da geração;
* feedback explícito por recomendação;
* feedback implícito por comportamento de uso;
* avaliação final da sessão;
* métricas de alinhamento com expectativa;
* dashboard de validação;
* exportação de dados anonimizados para análise.

---

# 3. Objetivo geral

Desenvolver um MVP funcional, seguro, rastreável e validável do POST-Rec para testar com voluntários se as recomendações científicas geradas são úteis, claras, confiáveis, acionáveis e alinhadas às expectativas dos usuários.

---

# 4. Objetivos específicos

## 4.1 Objetivos de produto

O MVP deve permitir que voluntários:

* acessem o sistema;
* aceitem um termo de participação;
* informem seu perfil básico;
* cadastrem tópicos de interesse;
* declarem suas expectativas antes da geração;
* recebam recomendações científicas;
* avaliem cada recomendação;
* indiquem se usariam a recomendação em um artigo real;
* forneçam feedback qualitativo;
* concluam uma avaliação final da sessão.

---

## 4.2 Objetivos técnicos

O MVP deve conter:

* Streamlit como interface;
* FastAPI como backend;
* PostgreSQL + pgvector como banco relacional/vetorial;
* RabbitMQ como broker;
* Celery como motor assíncrono;
* Alembic para migrations;
* OpenAI para embeddings e geração estruturada;
* OpenAlex e arXiv como fontes acadêmicas iniciais;
* structlog para logs estruturados;
* OpenTelemetry para traces e métricas;
* Grafana Stack para observabilidade;
* health checks;
* readiness checks;
* backup PostgreSQL;
* controle de custo por run;
* validação rígida da saída da LLM;
* testes automatizados.

---

## 4.3 Objetivos de validação com voluntários

O MVP deve responder:

```text id="sx6ao4"
As recomendações são relevantes?
Os gaps são claros?
As hipóteses são testáveis?
O plano experimental é viável?
As evidências aumentam a confiança?
O resultado corresponde ao que o usuário esperava?
O usuário usaria alguma recomendação em um artigo real?
O usuário usaria o POST-Rec novamente?
```

---

# 5. Hipótese do MVP

A hipótese principal do MVP é:

```text id="anh7md"
Usuários pesquisadores, estudantes de pós-graduação ou profissionais técnicos conseguem obter,
a partir do POST-Rec, pelo menos uma recomendação científica considerada útil, clara e acionável
para iniciar um artigo, experimento ou investigação exploratória.
```

---

# 6. Critério principal de sucesso

O MVP será considerado promissor se, em uma onda exploratória com voluntários:

```text id="ok8kxc"
EAS médio >= 3.5
Approval Rate >= 40%
Would Use in Real Paper Rate >= 30%
Trust Score médio >= 3.5
Run Failure Rate < 15%
```

Onde **EAS** significa:

```text id="ug2062"
Expectation Alignment Score
```

---

# 7. Escopo do MVP

## 7.1 Dentro do escopo

O MVP deve conter:

* login simples;
* termo de participação;
* política curta de privacidade;
* formulário de perfil;
* captura de expectativa;
* criação de recommendation run;
* processamento assíncrono;
* busca acadêmica inicial;
* embeddings;
* ranking;
* geração estruturada via LLM;
* feedback explícito;
* feedback implícito;
* event tracking;
* dashboard de validação;
* exportação Markdown;
* exportação de dados anonimizados;
* logs estruturados;
* tracing;
* métricas;
* controle de custo;
* health checks;
* backup.

---

## 7.2 Fora do escopo inicial

Fora do MVP Alpha:

* frontend React;
* app mobile;
* multi-tenant completo;
* billing;
* marketplace;
* integração Notion;
* integração Zotero;
* integração Overleaf;
* geração automática de artigo completo;
* submissão automática para conferências;
* LangGraph;
* multi-agent workflow;
* treinamento automático do ranking;
* fine-tuning;
* experimento acadêmico formal sem protocolo ético.

---

# 8. Stack tecnológica

```text id="fkqb1d"
Streamlit
FastAPI
PostgreSQL
pgvector
RabbitMQ
Celery
OpenAI
OpenAlex
arXiv
SQLAlchemy
Alembic
Pydantic
structlog
OpenTelemetry
Grafana
Tempo
Loki
Prometheus
Docker
GitHub Actions
Pytest
Ruff
Mypy
Bandit
Trivy
```

---

# 9. Decisões arquiteturais

## 9.1 Streamlit como UI

O Streamlit será usado para acelerar a criação da interface de validação.

Responsabilidades do Streamlit:

* autenticação inicial;
* captura de expectativa;
* criação de runs;
* acompanhamento de progresso;
* visualização de recomendações;
* coleta de feedback;
* dashboard de validação;
* exportação Markdown;
* exportação de dados anonimizados.

Regra:

```text id="swi2ic"
Streamlit não deve conter lógica crítica de negócio.
```

---

## 9.2 FastAPI como backend

A FastAPI será a API principal do sistema.

Responsabilidades:

* validar payloads;
* criar runs;
* consultar status;
* expor recomendações;
* registrar feedback;
* registrar eventos;
* controlar autenticação/autorização;
* publicar tarefas no RabbitMQ via Celery;
* expor health/readiness checks;
* expor métricas.

---

## 9.3 RabbitMQ como broker

RabbitMQ será usado como broker de mensagens.

Responsabilidades:

* receber tarefas de recomendação;
* distribuir tarefas para workers;
* permitir filas especializadas;
* suportar retries;
* suportar dead-letter queue;
* desacoplar API e processamento pesado.

---

## 9.4 Celery como motor de workers

Celery será usado para executar tarefas assíncronas.

Responsabilidades:

* retrieval acadêmico;
* normalização;
* deduplicação;
* geração de embeddings;
* ranking;
* chamada à LLM;
* validação do schema;
* exportação Markdown;
* atualização de status;
* registro de eventos.

---

## 9.5 PostgreSQL + pgvector

PostgreSQL será a fonte da verdade do sistema.

pgvector será usado para:

* armazenar embeddings;
* buscar documentos similares;
* reaproveitar artigos já indexados;
* reduzir custo e latência.

---

## 9.6 structlog para logs estruturados

Logs devem ser estruturados em JSON e enviados para stdout.

Campos obrigatórios:

* timestamp;
* level;
* service;
* environment;
* run_id;
* session_id;
* user_id;
* job_id;
* trace_id;
* span_id;
* event;
* message.

---

## 9.7 OpenTelemetry para observabilidade

OpenTelemetry será usado para:

* instrumentar FastAPI;
* instrumentar Celery;
* instrumentar SQLAlchemy;
* instrumentar HTTP clients;
* criar spans manuais;
* enviar traces e métricas para o Collector/Alloy.

---

## 9.8 Grafana Stack

A stack de observabilidade será composta por:

* Grafana;
* Tempo;
* Loki;
* Prometheus;
* OpenTelemetry Collector ou Grafana Alloy.

---

# 10. Arquitetura de alto nível

```text id="q9prai"
┌──────────────────────────┐
│       Streamlit UI        │
│ Validation / Review App   │
└────────────┬─────────────┘
             │ HTTPS
             ▼
┌──────────────────────────┐
│        FastAPI API        │
│ Runs / Feedback / Events  │
└───────┬─────────┬────────┘
        │         │
        │         ▼
        │   ┌─────────────────┐
        │   │    RabbitMQ      │
        │   │ Broker / Queues  │
        │   └────────┬────────┘
        │            ▼
        │   ┌─────────────────┐
        │   │ Celery Workers   │
        │   │ Retrieval / LLM  │
        │   └────────┬────────┘
        │            │
        ▼            ▼
┌──────────────────────────┐
│ PostgreSQL + pgvector     │
│ Runs / Papers / Feedback  │
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ External APIs             │
│ OpenAlex / arXiv / OpenAI │
└──────────────────────────┘

Observability:
FastAPI + Workers + Streamlit
        │
        ▼
OpenTelemetry Collector / Grafana Alloy
        │
        ├── Tempo
        ├── Loki
        └── Prometheus
             │
             ▼
          Grafana
```

---

# 11. Fluxo do voluntário

## 11.1 Fluxo completo

```text id="sirf9c"
1. Voluntário acessa o sistema.
2. Faz login.
3. Aceita o termo de participação.
4. Informa perfil básico.
5. Informa tópicos científicos.
6. Declara o que espera receber.
7. Cria uma recommendation run.
8. Sistema retorna run_id.
9. Sistema processa em background.
10. Usuário acompanha progresso.
11. Usuário visualiza recomendações.
12. Usuário avalia cada recomendação.
13. Usuário escolhe a recomendação mais útil.
14. Usuário responde avaliação final.
15. Sistema calcula métricas de validação.
16. Admin acompanha resultados no dashboard.
```

---

## 11.2 Tela 1 — Consentimento

Campos:

```text id="m4zkbq"
Li e aceito participar do teste exploratório.
Entendo que o sistema é experimental.
Entendo que as recomendações devem ser revisadas por humanos.
Entendo que posso desistir a qualquer momento.
```

Registro:

```text id="g0ioov"
consent_accepted
```

---

## 11.3 Tela 2 — Perfil básico

Campos:

```text id="4kbhp6"
Área de atuação
Nível acadêmico/profissional
Experiência com pesquisa científica
Experiência com IA
Experiência com sistemas de recomendação
Objetivo ao usar o POST-Rec
```

Evitar coletar:

```text id="j1909s"
CPF
endereço
telefone
dados sensíveis
dados pessoais desnecessários
```

---

## 11.4 Tela 3 — Captura de expectativa

Antes de gerar a recomendação, o sistema deve perguntar:

```text id="bscqry"
O que você espera receber do POST-Rec?
```

Campos:

```text id="ng77do"
Tópicos de interesse
Área de pesquisa
Tipo de contribuição esperada
Nível de profundidade esperado
Preferência por datasets públicos
Preferência por validação offline
Evitar experimentos com usuários reais
Objetivo do uso
Tipo de publicação desejada
```

Exemplo:

```json id="yvtp2f"
{
  "research_area": "Recommender Systems and LLMs",
  "seed_topics": [
    "Generative AI in recommender systems",
    "RAG for explainable recommendations"
  ],
  "expected_output": "I want ideas that can become a real paper using public datasets.",
  "desired_depth": "medium",
  "preferred_validation": ["offline datasets", "benchmark", "simulation"],
  "avoid_real_user_experiments": true,
  "publication_goal": "conference_or_journal"
}
```

---

## 11.5 Tela 4 — Progresso da execução

A UI deve exibir:

* status;
* barra de progresso;
* etapa atual;
* tempo decorrido;
* mensagens de evento;
* custo estimado parcial;
* botão cancelar.

Estados:

```text id="ivqqx3"
queued
started
searching_papers
normalizing_documents
deduplicating_documents
generating_embeddings
ranking_candidates
generating_recommendations
validating_output
completed
failed
cancelled
```

---

## 11.6 Tela 5 — Recomendações

Cada recomendação deve exibir:

* título;
* técnica proposta;
* gap;
* pergunta de pesquisa;
* hipótese;
* método proposto;
* artigos de evidência;
* datasets;
* métricas;
* plano experimental;
* riscos;
* score final;
* nível de confiança.

---

## 11.7 Tela 6 — Feedback por recomendação

Para cada recomendação, coletar notas de 1 a 5:

```text id="xceg3f"
Relevância
Originalidade percebida
Clareza do gap
Hipótese testável
Viabilidade experimental
Confiança nas evidências
Utilidade geral
```

Botões:

```text id="x4va7o"
Aprovar
Rejeitar
Salvar para depois
Precisa melhorar
Não entendi
Já vi algo parecido
Usaria em um artigo real
```

Campo livre:

```text id="kec29v"
O que faltou para essa recomendação ser mais útil?
```

---

## 11.8 Tela 7 — Avaliação final da sessão

Perguntas:

```text id="pmcyua"
1. O resultado atendeu sua expectativa inicial?
2. Você usaria alguma recomendação como base para um artigo real?
3. Qual recomendação foi mais útil?
4. O que mais prejudicou sua experiência?
5. O que mais ajudou sua experiência?
6. Você usaria o POST-Rec novamente?
7. Você recomendaria o POST-Rec para outro pesquisador?
8. Comentário livre.
```

---

# 12. Feedback explícito

Feedback explícito é toda avaliação informada diretamente pelo usuário.

## 12.1 Dados coletados

```text id="gkvlws"
rating de relevância
rating de originalidade
rating de clareza
rating de viabilidade
rating de confiança
rating de utilidade
decisão: approve/reject/save/needs_revision
comentário textual
would_use_in_real_paper
```

---

## 12.2 Uso do feedback explícito

Na versão Alpha, o feedback será usado para:

* análise offline;
* ajustes no prompt;
* ajustes nos pesos de ranking;
* melhoria da interface;
* identificação de recomendações ruins;
* cálculo do Expectation Alignment Score;
* cálculo de Approval Rate;
* cálculo de Would Use Rate.

Não haverá aprendizado automático no MVP Alpha.

---

# 13. Feedback implícito

Feedback implícito é inferido pelo comportamento do usuário.

## 13.1 Eventos comportamentais

```text id="g5v9vu"
tempo na recomendação
recomendação expandida
evidência clicada
paper aberto
scroll até o fim
exportação Markdown
rerun solicitado
cancelamento
abandono da sessão
edição manual
ordenação manual
```

---

## 13.2 Cuidados

Feedback implícito não deve ser usado isoladamente.

Exemplo:

```text id="cc4wr1"
Tempo alto na tela pode indicar interesse, mas também pode indicar confusão.
```

Por isso, o sistema deve combinar:

```text id="zpgzjq"
feedback explícito + feedback implícito
```

---

# 14. Métrica principal: Expectation Alignment Score

## 14.1 Definição

O **Expectation Alignment Score**, ou **EAS**, mede o quanto a recomendação entregue ficou alinhada com a expectativa inicial do usuário.

---

## 14.2 Fórmula MVP

```text id="alrrrb"
EAS =
  0.25 * usefulness_score +
  0.20 * relevance_score +
  0.20 * clarity_score +
  0.15 * feasibility_score +
  0.10 * trust_score +
  0.10 * would_use_score
```

Onde:

```text id="ed9b7t"
would_use_score = 5 se o usuário usaria em um artigo real
would_use_score = 3 se talvez usaria
would_use_score = 1 se não usaria
```

---

## 14.3 Interpretação

```text id="e1oyr0"
EAS >= 4.2: muito alinhada
3.5 <= EAS < 4.2: promissora
2.8 <= EAS < 3.5: precisa melhorar
EAS < 2.8: desalinhada
```

---

# 15. Métricas do MVP

## 15.1 Métricas principais

```text id="qbwsk0"
Expectation Alignment Score
Recommendation Approval Rate
Would Use in Real Paper Rate
Average Usefulness Score
Average Trust Score
Average Feasibility Score
Run Completion Rate
Run Failure Rate
Average Time to Result
Cost per Run
Cost per Approved Recommendation
```

---

## 15.2 Métricas de comportamento

```text id="akf2pt"
tempo médio por recomendação
taxa de expansão de evidências
taxa de clique em papers
taxa de exportação Markdown
taxa de rerun
taxa de abandono
número médio de recomendações avaliadas
número médio de comentários qualitativos
```

---

## 15.3 Métricas técnicas

```text id="mty4ln"
latência da API
tempo médio de worker
tempo por etapa
falhas por etapa
retries por etapa
tamanho da fila RabbitMQ
dead-letter count
tokens por run
custo por modelo
erros de schema LLM
erros de APIs externas
```

---

# 16. Critérios de sucesso por onda

## 16.1 Onda 1 — 3 a 5 voluntários

Objetivo:

```text id="zejq21"
Encontrar problemas graves de fluxo, UX, estabilidade e clareza.
```

Sucesso se:

```text id="miui5j"
80% das runs completarem sem erro
pelo menos 1 recomendação útil por sessão
nenhum bug bloqueante
tempo do Quick Mode aceitável
feedback qualitativo suficiente
```

---

## 16.2 Onda 2 — 8 a 12 voluntários

Objetivo:

```text id="vlw4rs"
Validar utilidade percebida e aderência à expectativa.
```

Sucesso se:

```text id="a3pkzs"
EAS médio >= 3.5
Approval Rate >= 40%
Would Use in Real Paper Rate >= 30%
Trust Score médio >= 3.5
Feasibility Score médio >= 3.5
Run Failure Rate < 15%
```

---

## 16.3 Onda 3 — 15 a 30 voluntários

Objetivo:

```text id="tfux3j"
Avaliar consistência do valor entregue.
```

Sucesso se:

```text id="r69a20"
EAS médio >= 4.0
Approval Rate >= 50%
Would Use in Real Paper Rate >= 40%
Export Markdown Rate >= 25%
Rerun por insatisfação < 30%
```

---

# 17. Modelo de dados

## 17.1 volunteer_session

```sql id="ewr3o2"
CREATE TABLE volunteer_session (
    id UUID PRIMARY KEY,
    user_id TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'started',
    user_agent TEXT,
    ip_hash TEXT,
    metadata JSONB
);
```

---

## 17.2 participant_consent

```sql id="ue9tdk"
CREATE TABLE participant_consent (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id UUID NOT NULL REFERENCES volunteer_session(id),
    consent_version TEXT NOT NULL,
    accepted BOOLEAN NOT NULL,
    accepted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);
```

---

## 17.3 participant_profile

```sql id="cf2jal"
CREATE TABLE participant_profile (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id UUID NOT NULL REFERENCES volunteer_session(id),
    research_area TEXT,
    academic_level TEXT,
    professional_role TEXT,
    experience_with_ai TEXT,
    experience_with_recommender_systems TEXT,
    experience_with_scientific_writing TEXT,
    goal_with_postrec TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.4 user_expectation

```sql id="rgo1f3"
CREATE TABLE user_expectation (
    id UUID PRIMARY KEY,
    user_id TEXT,
    session_id UUID NOT NULL REFERENCES volunteer_session(id),
    research_area TEXT,
    seed_topics JSONB NOT NULL,
    expected_output TEXT,
    desired_depth TEXT,
    preferred_validation JSONB,
    avoid_real_user_experiments BOOLEAN DEFAULT TRUE,
    publication_goal TEXT,
    expects_original_ideas BOOLEAN,
    expects_datasets BOOLEAN,
    expects_experimental_plan BOOLEAN,
    expects_references BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.5 recommendation_run

```sql id="me0nkd"
CREATE TABLE recommendation_run (
    id UUID PRIMARY KEY,
    request_id TEXT UNIQUE,
    user_id TEXT,
    session_id UUID REFERENCES volunteer_session(id),
    expectation_id UUID REFERENCES user_expectation(id),
    input JSONB NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INT NOT NULL DEFAULT 0,
    current_step TEXT,
    error_message TEXT,
    max_papers INT NOT NULL,
    max_recommendations INT NOT NULL,
    trace_id TEXT,
    estimated_cost_usd NUMERIC DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);
```

---

## 17.6 recommendation_run_event

```sql id="e9f2hu"
CREATE TABLE recommendation_run_event (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES recommendation_run(id),
    session_id UUID REFERENCES volunteer_session(id),
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    payload JSONB,
    trace_id TEXT,
    span_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.7 source_document

```sql id="zucpdb"
CREATE TABLE source_document (
    id UUID PRIMARY KEY,
    external_id TEXT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    authors JSONB,
    year INT,
    venue TEXT,
    doi TEXT,
    url TEXT,
    citation_count INT DEFAULT 0,
    keywords JSONB,
    metadata JSONB,
    content_hash TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.8 document_embedding

```sql id="pgc6yc"
CREATE TABLE document_embedding (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES source_document(id),
    embedding VECTOR(1536),
    embedding_model TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.9 recommendation_candidate

```sql id="c1cr6p"
CREATE TABLE recommendation_candidate (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES recommendation_run(id),
    title TEXT NOT NULL,
    technique_name TEXT,
    research_gap TEXT,
    research_question TEXT,
    hypothesis TEXT,
    proposed_method TEXT,
    related_work_summary TEXT,
    evidence_papers JSONB,
    datasets JSONB,
    evaluation_metrics JSONB,
    experimental_plan TEXT,
    risks JSONB,
    expected_contribution TEXT,
    confidence_level TEXT,
    scores JSONB,
    final_score NUMERIC,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.10 recommendation_feedback

```sql id="dnkl1m"
CREATE TABLE recommendation_feedback (
    id UUID PRIMARY KEY,
    user_id TEXT,
    session_id UUID NOT NULL REFERENCES volunteer_session(id),
    run_id UUID NOT NULL REFERENCES recommendation_run(id),
    recommendation_id UUID NOT NULL REFERENCES recommendation_candidate(id),
    relevance_score INT CHECK (relevance_score BETWEEN 1 AND 5),
    originality_score INT CHECK (originality_score BETWEEN 1 AND 5),
    clarity_score INT CHECK (clarity_score BETWEEN 1 AND 5),
    feasibility_score INT CHECK (feasibility_score BETWEEN 1 AND 5),
    trust_score INT CHECK (trust_score BETWEEN 1 AND 5),
    usefulness_score INT CHECK (usefulness_score BETWEEN 1 AND 5),
    would_use_in_real_paper TEXT,
    decision TEXT,
    comment TEXT,
    expectation_alignment_score NUMERIC,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.11 user_interaction_event

```sql id="gaknrw"
CREATE TABLE user_interaction_event (
    id UUID PRIMARY KEY,
    user_id TEXT,
    session_id UUID NOT NULL REFERENCES volunteer_session(id),
    run_id UUID REFERENCES recommendation_run(id),
    recommendation_id UUID REFERENCES recommendation_candidate(id),
    event_type TEXT NOT NULL,
    event_value TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.12 session_final_survey

```sql id="bz94mm"
CREATE TABLE session_final_survey (
    id UUID PRIMARY KEY,
    user_id TEXT,
    session_id UUID NOT NULL REFERENCES volunteer_session(id),
    run_id UUID REFERENCES recommendation_run(id),
    expectation_met_score INT CHECK (expectation_met_score BETWEEN 1 AND 5),
    would_use_again BOOLEAN,
    would_recommend BOOLEAN,
    would_use_any_recommendation_in_real_paper TEXT,
    most_useful_recommendation_id UUID,
    what_helped_most TEXT,
    what_hurt_most TEXT,
    free_comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.13 llm_usage

```sql id="whg9c4"
CREATE TABLE llm_usage (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES recommendation_run(id),
    recommendation_id UUID REFERENCES recommendation_candidate(id),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    operation TEXT NOT NULL,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    estimated_cost_usd NUMERIC DEFAULT 0,
    request_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.14 exported_artifact

```sql id="bbxrfb"
CREATE TABLE exported_artifact (
    id UUID PRIMARY KEY,
    recommendation_id UUID NOT NULL REFERENCES recommendation_candidate(id),
    artifact_type TEXT NOT NULL,
    file_path TEXT,
    content TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 17.15 audit_log

```sql id="ba4230"
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    actor_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

# 18. Índices

```sql id="z6e2lc"
CREATE INDEX idx_volunteer_session_user_id
ON volunteer_session(user_id);

CREATE INDEX idx_recommendation_run_session_id
ON recommendation_run(session_id);

CREATE INDEX idx_recommendation_run_status
ON recommendation_run(status);

CREATE INDEX idx_recommendation_run_created_at
ON recommendation_run(created_at);

CREATE INDEX idx_recommendation_feedback_recommendation_id
ON recommendation_feedback(recommendation_id);

CREATE INDEX idx_recommendation_feedback_session_id
ON recommendation_feedback(session_id);

CREATE INDEX idx_user_interaction_event_session_id
ON user_interaction_event(session_id);

CREATE INDEX idx_user_interaction_event_event_type
ON user_interaction_event(event_type);

CREATE INDEX idx_source_document_doi
ON source_document(doi);

CREATE INDEX idx_source_document_content_hash
ON source_document(content_hash);

CREATE INDEX idx_llm_usage_run_id
ON llm_usage(run_id);

CREATE INDEX idx_audit_log_actor_id
ON audit_log(actor_id);
```

Índice vetorial:

```sql id="zr5juo"
CREATE INDEX idx_document_embedding_vector
ON document_embedding
USING hnsw (embedding vector_cosine_ops);
```

---

# 19. API FastAPI

## 19.1 Endpoints principais

```http id="zjboea"
POST /api/v1/sessions
POST /api/v1/consents
POST /api/v1/profiles
POST /api/v1/expectations

POST /api/v1/recommendation-runs
GET  /api/v1/recommendation-runs
GET  /api/v1/recommendation-runs/{run_id}
GET  /api/v1/recommendation-runs/{run_id}/events
GET  /api/v1/recommendation-runs/{run_id}/recommendations
POST /api/v1/recommendation-runs/{run_id}/cancel

POST /api/v1/recommendations/{recommendation_id}/feedback
POST /api/v1/recommendations/{recommendation_id}/export

POST /api/v1/interaction-events
POST /api/v1/session-final-surveys

GET /api/v1/validation/dashboard
GET /api/v1/validation/export

GET /api/v1/health
GET /api/v1/ready
GET /api/v1/metrics
```

---

## 19.2 Criar sessão

```http id="nqzmhf"
POST /api/v1/sessions
```

Response:

```json id="irwsr8"
{
  "session_id": "uuid",
  "status": "started"
}
```

---

## 19.3 Registrar expectativa

```http id="b6e1nk"
POST /api/v1/expectations
```

Request:

```json id="cwv2ef"
{
  "session_id": "uuid",
  "research_area": "Recommender Systems and LLMs",
  "seed_topics": [
    "Generative AI in recommender systems",
    "RAG for explainable recommendations"
  ],
  "expected_output": "I want ideas that can become a real paper using public datasets.",
  "desired_depth": "medium",
  "preferred_validation": ["offline datasets", "benchmark", "simulation"],
  "avoid_real_user_experiments": true,
  "publication_goal": "conference_or_journal",
  "expects_original_ideas": true,
  "expects_datasets": true,
  "expects_experimental_plan": true,
  "expects_references": true
}
```

---

## 19.4 Criar run

```http id="z0bsht"
POST /api/v1/recommendation-runs
```

Request:

```json id="vl2rza"
{
  "session_id": "uuid",
  "expectation_id": "uuid",
  "request_id": "client-generated-uuid",
  "topics": [
    "Generative AI in recommender systems",
    "RAG for explainable recommendations"
  ],
  "mode": "quick",
  "max_papers": 50,
  "max_recommendations": 5,
  "constraints": {
    "avoid_real_user_experiments": true,
    "prefer_public_datasets": true,
    "prefer_reproducibility": true
  }
}
```

Response:

```json id="sg6x5c"
{
  "run_id": "uuid",
  "status": "queued",
  "progress": 0,
  "message": "Recommendation run created successfully."
}
```

---

## 19.5 Registrar evento de interação

```http id="nomktq"
POST /api/v1/interaction-events
```

Request:

```json id="r3xvhs"
{
  "session_id": "uuid",
  "run_id": "uuid",
  "recommendation_id": "uuid",
  "event_type": "recommendation_expanded",
  "event_value": "true",
  "metadata": {
    "section": "evidence_papers"
  }
}
```

---

## 19.6 Registrar feedback

```http id="h2gwj8"
POST /api/v1/recommendations/{recommendation_id}/feedback
```

Request:

```json id="ss2fju"
{
  "session_id": "uuid",
  "run_id": "uuid",
  "relevance_score": 5,
  "originality_score": 4,
  "clarity_score": 4,
  "feasibility_score": 5,
  "trust_score": 4,
  "usefulness_score": 5,
  "would_use_in_real_paper": "yes",
  "decision": "approved",
  "comment": "The topic is actionable and can be validated with public datasets."
}
```

---

# 20. RabbitMQ e Celery

## 20.1 Filas

```text id="el79xz"
postrec.recommendation.default
postrec.recommendation.retrieval
postrec.recommendation.embedding
postrec.recommendation.ranking
postrec.recommendation.llm
postrec.recommendation.export
postrec.validation.metrics
postrec.dead_letter
```

---

## 20.2 Roteamento

| Task                       | Queue                            |
| -------------------------- | -------------------------------- |
| process_recommendation_run | postrec.recommendation.default   |
| retrieve_papers            | postrec.recommendation.retrieval |
| generate_embeddings        | postrec.recommendation.embedding |
| rank_candidates            | postrec.recommendation.ranking   |
| generate_recommendations   | postrec.recommendation.llm       |
| export_markdown            | postrec.recommendation.export    |
| compute_validation_metrics | postrec.validation.metrics       |
| unrecoverable failures     | postrec.dead_letter              |

---

## 20.3 Configuração Celery

```python id="jrbzq5"
from celery import Celery

celery_app = Celery(
    "postrec",
    broker="pyamqp://postrec:postrec@rabbitmq:5672//",
    backend="rpc://",
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_time_limit=900,
    task_soft_time_limit=840,
    broker_connection_retry_on_startup=True,
    task_default_queue="postrec.recommendation.default",
    task_routes={
        "postrec.tasks.retrieve_papers": {"queue": "postrec.recommendation.retrieval"},
        "postrec.tasks.generate_embeddings": {"queue": "postrec.recommendation.embedding"},
        "postrec.tasks.rank_candidates": {"queue": "postrec.recommendation.ranking"},
        "postrec.tasks.generate_recommendations": {"queue": "postrec.recommendation.llm"},
        "postrec.tasks.export_markdown": {"queue": "postrec.recommendation.export"},
        "postrec.tasks.compute_validation_metrics": {"queue": "postrec.validation.metrics"},
    },
)
```

---

# 21. Pipeline do worker

```text id="b4tdmr"
process_recommendation_run(run_id)
    update_status(started)

    update_status(searching_papers)
    retrieve_papers(run_id)

    update_status(normalizing_documents)
    normalize_documents(run_id)

    update_status(deduplicating_documents)
    deduplicate_documents(run_id)

    update_status(generating_embeddings)
    generate_embeddings(run_id)

    update_status(ranking_candidates)
    rank_candidates(run_id)

    update_status(generating_recommendations)
    generate_recommendations(run_id)

    update_status(validating_output)
    validate_llm_output(run_id)

    save_recommendations(run_id)

    update_status(completed)
```

---

# 22. Política de retry

```text id="bpp726"
max_retries: 3
retry_backoff: true
retry_jitter: true
retry_intervals: 30s, 120s, 300s
```

Falhas com retry:

* timeout;
* rate limit;
* erro temporário em API externa;
* erro temporário da LLM;
* falha de rede.

Falhas sem retry:

* payload inválido;
* schema inválido após tentativas;
* autenticação inválida;
* custo excedido;
* run cancelada.

---

# 23. Validação rígida da LLM

## 23.1 Regra

A LLM deve retornar apenas JSON válido aderente ao schema.

Não aceitar texto livre como resultado final.

---

## 23.2 Regras anti-alucinação

A LLM não pode:

* inventar DOI;
* inventar autores;
* inventar papers;
* inventar venues;
* inventar datasets como se fossem usados nos artigos;
* garantir originalidade absoluta;
* garantir publicação;
* usar evidência não recuperada.

---

## 23.3 Schema lógico da recomendação

```json id="bmwh0r"
{
  "recommendations": [
    {
      "title": "string",
      "technique_name": "string",
      "research_gap": "string",
      "research_question": "string",
      "hypothesis": "string",
      "proposed_method": "string",
      "related_work_summary": "string",
      "evidence_papers": [
        {
          "title": "string",
          "year": 2026,
          "doi": "string",
          "url": "string",
          "why_relevant": "string"
        }
      ],
      "datasets": ["string"],
      "evaluation_metrics": ["string"],
      "experimental_plan": "string",
      "risks": ["string"],
      "expected_contribution": "string",
      "confidence_level": "low | medium | high",
      "scores": {
        "relevance": 0,
        "novelty": 0,
        "evidence": 0,
        "feasibility": 0,
        "trend": 0,
        "publication_potential": 0,
        "strategic_fit": 0,
        "final_score": 0
      }
    }
  ]
}
```

---

## 23.4 Política de falha

Se a saída for inválida:

```text id="kplf12"
1. tentar repair local;
2. tentar uma nova chamada com prompt de correção;
3. se falhar, marcar run como failed_schema_validation;
4. salvar erro;
5. não exibir recomendação inválida.
```

---

# 24. Ranking

## 24.1 Fórmula inicial

```text id="btde8r"
final_score =
    0.22 * relevance_score +
    0.18 * novelty_score +
    0.15 * evidence_score +
    0.15 * feasibility_score +
    0.10 * trend_score +
    0.10 * publication_potential_score +
    0.10 * strategic_fit_score
```

---

## 24.2 Critérios

| Critério                    | Descrição                                        |
| --------------------------- | ------------------------------------------------ |
| relevance_score             | Aderência aos tópicos-semente                    |
| novelty_score               | Diferenciação em relação à literatura recuperada |
| evidence_score              | Quantidade/qualidade das evidências              |
| feasibility_score           | Viabilidade experimental                         |
| trend_score                 | Recência e crescimento do tema                   |
| publication_potential_score | Potencial para workshop, conferência ou journal  |
| strategic_fit_score         | Aderência ao posicionamento do usuário           |

---

# 25. Logs estruturados

## 25.1 Biblioteca

Usar:

```text id="zgomr1"
structlog
```

---

## 25.2 Campos obrigatórios

```json id="z1k8b1"
{
  "timestamp": "2026-06-03T10:00:00Z",
  "level": "info",
  "service": "postrec-api",
  "environment": "production",
  "event": "recommendation_run_created",
  "message": "Recommendation run created",
  "run_id": "uuid",
  "session_id": "uuid",
  "job_id": "celery-task-id",
  "user_id": "string",
  "trace_id": "string",
  "span_id": "string",
  "request_id": "string"
}
```

---

## 25.3 Regras

Nunca logar:

* API keys;
* tokens;
* secrets;
* credenciais;
* prompts completos sensíveis;
* payloads grandes sem truncamento.

Sempre logar:

* transição de status;
* início/fim de etapa;
* erro externo;
* retry;
* custo estimado;
* duração da etapa;
* quantidade de papers;
* quantidade de recomendações;
* falha de schema;
* evento de feedback.

---

# 26. OpenTelemetry

## 26.1 Instrumentar

* FastAPI;
* Celery;
* SQLAlchemy;
* HTTPX/Requests;
* chamadas acadêmicas;
* chamadas OpenAI;
* pipeline de ranking;
* pipeline de validação.

---

## 26.2 Atributos obrigatórios em spans

```text id="szsg4j"
postrec.run_id
postrec.session_id
postrec.stage
postrec.mode
postrec.max_papers
postrec.max_recommendations
postrec.paper_count
postrec.recommendation_count
postrec.llm_model
postrec.embedding_model
postrec.estimated_cost_usd
```

---

## 26.3 Spans manuais recomendados

```text id="rbezdy"
postrec.retrieve_papers
postrec.normalize_documents
postrec.deduplicate_documents
postrec.generate_embeddings
postrec.rank_candidates
postrec.generate_recommendations
postrec.validate_llm_output
postrec.save_feedback
postrec.compute_validation_metrics
```

---

# 27. Grafana Stack

## 27.1 Dashboards obrigatórios

### Product Validation Dashboard

* EAS médio;
* Approval Rate;
* Would Use Rate;
* Trust Score médio;
* Usefulness Score médio;
* Feasibility Score médio;
* comentários qualitativos;
* motivos de rejeição;
* recomendações mais aprovadas;
* recomendações mais rejeitadas.

### Technical Dashboard

* latência API;
* erro 4xx/5xx;
* runs concluídas;
* runs falhas;
* tempo por etapa;
* fila RabbitMQ;
* Celery retries;
* DLQ count.

### LLM Cost Dashboard

* tokens por run;
* custo por run;
* custo por modelo;
* custo por recomendação;
* custo diário;
* custo mensal;
* runs bloqueadas por limite.

---

# 28. Segurança e privacidade

## 28.1 Requisitos mínimos

* autenticação;
* autorização básica;
* secrets fora do código;
* HTTPS;
* CORS restrito;
* rate limiting;
* validação de payload;
* sanitização de logs;
* audit logs;
* proteção contra injection;
* limite de tamanho de payload;
* timeout em chamadas externas;
* backup;
* exportação anonimizada.

---

## 28.2 Dados pessoais mínimos

Coletar apenas:

```text id="xpz2kh"
identificador do voluntário
e-mail, se necessário
área de atuação
nível acadêmico/profissional
expectativas
tópicos informados
feedbacks
eventos de interação
```

Evitar:

```text id="v0bbrn"
CPF
telefone
endereço
dados sensíveis
dados de saúde
dados políticos
dados religiosos
instituição obrigatória
```

---

## 28.3 Anonimização para análise

A exportação de dados para análise deve remover ou mascarar:

* e-mail;
* user_id direto;
* IP;
* qualquer identificador pessoal;
* comentários com dados pessoais, quando possível.

---

# 29. Consentimento e ética

## 29.1 Termo de participação

O termo deve explicar:

* objetivo do teste;
* o que o voluntário fará;
* quais dados serão coletados;
* como os dados serão usados;
* riscos;
* benefícios esperados;
* direito de desistir;
* contato do responsável;
* prazo de retenção dos dados.

---

## 29.2 Uso como teste exploratório

Se o MVP for usado apenas como validação interna de produto, com consentimento e sem publicação dos dados como pesquisa científica formal, o processo pode ser conduzido como teste exploratório controlado.

---

## 29.3 Uso como pesquisa científica

Se os dados dos voluntários forem usados em artigo, dissertação, tese ou publicação científica, deve-se avaliar submissão ética ao sistema adequado antes da coleta formal.

---

# 30. Controle de custo por run

## 30.1 Registrar

Para cada run:

* provider;
* modelo;
* operação;
* input tokens;
* output tokens;
* total tokens;
* custo estimado;
* embeddings gerados;
* papers processados;
* tempo total;
* custo por recomendação.

---

## 30.2 Limites

```text id="b5rlr8"
max_papers_quick=50
max_papers_deep=200
max_recommendations_quick=5
max_recommendations_deep=10
max_daily_runs_per_user=20
max_cost_per_run_usd=2.00
```

---

## 30.3 Política

Se o custo estimado ultrapassar o limite:

```text id="ja5c8x"
parar execução
marcar status cost_limit_exceeded
salvar evento
notificar usuário
não continuar chamando LLM
```

---

# 31. Backup PostgreSQL

## 31.1 Estratégia

Backups automáticos diários.

Retenção:

```text id="tnpynb"
diário: 7 dias
semanal: 4 semanas
mensal: 6 meses
```

---

## 31.2 Restore

Regra:

```text id="squaeq"
Backup só é válido se o restore já foi testado.
```

---

# 32. Health checks

## 32.1 Health

```http id="kacevb"
GET /api/v1/health
```

Verifica se o serviço está vivo.

---

## 32.2 Readiness

```http id="bvobz5"
GET /api/v1/ready
```

Verifica:

* PostgreSQL;
* RabbitMQ;
* migrations;
* OpenTelemetry Collector;
* configuração mínima;
* secrets obrigatórios.

---

# 33. Testes

## 33.1 Unitários

Cobrir:

* cálculo EAS;
* normalização de documentos;
* deduplicação;
* ranking;
* validação de schema;
* cálculo de custo;
* exportação Markdown;
* criação de eventos;
* persistência de feedback.

---

## 33.2 Integração

Cobrir:

* FastAPI + PostgreSQL;
* FastAPI + RabbitMQ;
* Celery + RabbitMQ;
* worker + banco;
* Streamlit + API;
* migrations;
* health/readiness;
* OpenTelemetry configurado.

---

## 33.3 End-to-end

Fluxo:

```text id="jn9t5h"
voluntário cria sessão
aceita termo
preenche expectativa
cria run
worker processa
recomendações aparecem
usuário avalia
métricas são calculadas
dashboard mostra resultados
```

---

## 33.4 Cobertura mínima

```text id="bpce4q"
MVP Alpha: mínimo 80%
Antes de teste ampliado: mínimo 90%
```

---

# 34. CI/CD

Pipeline:

```text id="g15dhn"
lint
format-check
type-check
unit-tests
integration-tests
coverage
security-scan
dependency-scan
docker-build
migration-check
push-image
deploy-staging
smoke-test
manual-approval
deploy-production
```

Ferramentas:

```text id="h394jf"
ruff
mypy
pytest
pytest-cov
bandit
pip-audit
trivy
alembic
docker buildx
```

---

# 35. Docker Compose local

```yaml id="ti2oc1"
services:
  api:
    build: .
    command: uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
    env_file: .env
    depends_on:
      - postgres
      - rabbitmq
      - otel-collector

  ui:
    build: .
    command: streamlit run apps/ui/streamlit_app.py --server.port 8501
    env_file: .env
    depends_on:
      - api

  worker:
    build: .
    command: celery -A apps.api.workers.celery_app worker --loglevel=INFO
    env_file: .env
    depends_on:
      - postgres
      - rabbitmq
      - otel-collector

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: postrec
      POSTGRES_USER: postrec
      POSTGRES_PASSWORD: postrec

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: postrec
      RABBITMQ_DEFAULT_PASS: postrec
    ports:
      - "15672:15672"
      - "5672:5672"

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest

  prometheus:
    image: prom/prometheus

  tempo:
    image: grafana/tempo

  loki:
    image: grafana/loki

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

# 36. Variáveis de ambiente

```env id="niate5"
APP_ENV=development
APP_NAME=post-rec

DATABASE_URL=postgresql+psycopg://postrec:postrec@postgres:5432/postrec

RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=postrec
RABBITMQ_PASSWORD=postrec
CELERY_BROKER_URL=pyamqp://postrec:postrec@rabbitmq:5672//
CELERY_RESULT_BACKEND=rpc://

OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_GENERATION_MODEL=gpt-4.1-mini

OPENALEX_EMAIL=

MAX_PAPERS_DEFAULT=50
MAX_RECOMMENDATIONS_DEFAULT=5
RUN_TIMEOUT_SECONDS=900
MAX_COST_PER_RUN_USD=2.00

LOG_LEVEL=INFO
LOG_FORMAT=json

OTEL_SERVICE_NAME=postrec-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

AUTH_ENABLED=true
API_INTERNAL_KEY=
JWT_SECRET=
```

---

# 37. Estrutura do repositório

```text id="ldg236"
post-rec/
  README.md
  docker-compose.yml
  .env.example
  pyproject.toml

  apps/
    api/
      main.py
      settings.py
      dependencies.py

      routers/
        sessions.py
        consents.py
        profiles.py
        expectations.py
        recommendation_runs.py
        recommendations.py
        feedback.py
        interaction_events.py
        validation_dashboard.py
        health.py
        metrics.py

      schemas/
        sessions.py
        expectations.py
        recommendation_runs.py
        recommendations.py
        feedback.py
        surveys.py
        llm_outputs.py

      services/
        session_service.py
        consent_service.py
        expectation_service.py
        run_service.py
        retrieval_service.py
        embedding_service.py
        ranking_service.py
        llm_service.py
        feedback_service.py
        validation_metrics_service.py
        export_service.py
        cost_service.py

      repositories/
        session_repository.py
        run_repository.py
        document_repository.py
        recommendation_repository.py
        feedback_repository.py
        event_repository.py
        usage_repository.py

      workers/
        celery_app.py
        tasks.py
        queues.py

      observability/
        logging.py
        tracing.py
        metrics.py

    ui/
      streamlit_app.py
      pages/
        01_Consent.py
        02_Profile.py
        03_New_Recommendation.py
        04_Run_Details.py
        05_Review.py
        06_Final_Survey.py
        07_Validation_Dashboard.py
        08_Admin.py
      components/
        consent_form.py
        expectation_form.py
        run_status.py
        recommendation_card.py
        feedback_form.py
        event_timeline.py
        validation_charts.py
      clients/
        api_client.py
      auth/
        authentication.py

  packages/
    postrec_core/
      domain/
        models.py
        enums.py
      scoring/
        relevance.py
        novelty.py
        feasibility.py
        trend.py
        final_score.py
        expectation_alignment.py
      prompts/
        recommendation_prompt.py
      schemas/
        recommendation_output_schema.json

  migrations/
    versions/

  tests/
    unit/
    integration/
    e2e/

  observability/
    otel-collector.yaml
    prometheus.yml
    grafana/
      dashboards/
      provisioning/

  docs/
    sdd.md
    architecture.md
    validation_protocol.md
    api.md
    deployment.md
    security.md
    observability.md
    roadmap.md

  scripts/
    seed_topics.py
    backup_postgres.sh
    restore_postgres.sh
    export_anonymized_validation_data.py
```

---

# 38. Roadmap MVP Ready

## Fase 0 — Fundação

Entregas:

* repositório;
* estrutura modular;
* Docker Compose;
* FastAPI;
* Streamlit;
* PostgreSQL;
* RabbitMQ;
* Celery;
* health check;
* readiness check;
* `.env.example`.

Critério:

```text id="n6zfo5"
docker compose up inicia API, UI, banco, RabbitMQ e worker.
```

---

## Fase 1 — Banco e migrations

Entregas:

* SQLAlchemy models;
* Alembic;
* tabelas principais;
* tabelas de validação;
* pgvector;
* índices;
* migration tests.

Critério:

```text id="mtf7xk"
Banco sobe limpo e migrations criam todo o schema.
```

---

## Fase 2 — Fluxo de voluntário

Entregas:

* sessão;
* consentimento;
* perfil;
* expectativa;
* final survey.

Critério:

```text id="zlkhm6"
Voluntário consegue iniciar e finalizar uma sessão completa.
```

---

## Fase 3 — Runs assíncronas

Entregas:

* criação de run;
* publicação no RabbitMQ;
* Celery worker;
* status;
* eventos;
* cancelamento;
* retries.

Critério:

```text id="zb1yt5"
Run criada pela API é processada por Celery via RabbitMQ.
```

---

## Fase 4 — Retrieval acadêmico

Entregas:

* OpenAlex;
* arXiv;
* normalização;
* deduplicação;
* persistência.

Critério:

```text id="fj59lu"
Sistema recupera e salva pelo menos 30 papers por tópico.
```

---

## Fase 5 — Embeddings e ranking

Entregas:

* embeddings;
* pgvector;
* relevance score;
* novelty score;
* feasibility score;
* final score.

Critério:

```text id="n92tw3"
Sistema retorna candidatos ranqueados com score.
```

---

## Fase 6 — LLM Structured Output

Entregas:

* prompt;
* JSON Schema;
* validação;
* retry de schema;
* persistência das recomendações.

Critério:

```text id="nx0czy"
Sistema gera 3 a 5 recomendações válidas em JSON.
```

---

## Fase 7 — Feedback e eventos

Entregas:

* feedback explícito;
* eventos implícitos;
* EAS;
* final survey;
* interaction tracking.

Critério:

```text id="n91qts"
Usuário avalia recomendações e sistema calcula métricas.
```

---

## Fase 8 — Dashboard de validação

Entregas:

* EAS médio;
* Approval Rate;
* Would Use Rate;
* Trust Score;
* Feasibility Score;
* comentários;
* motivos de rejeição.

Critério:

```text id="px1wfw"
Admin consegue visualizar se o MVP está entregando valor.
```

---

## Fase 9 — Observabilidade

Entregas:

* structlog;
* OpenTelemetry;
* Grafana;
* Tempo;
* Loki;
* Prometheus;
* dashboards.

Critério:

```text id="z7wsnq"
Uma sessão pode ser rastreada da UI até o worker.
```

---

## Fase 10 — Segurança e privacidade

Entregas:

* autenticação;
* secrets fora do código;
* consentimento;
* anonimização;
* rate limit;
* audit log;
* CORS;
* HTTPS no deploy.

Critério:

```text id="yceai5"
Sistema está apto para teste controlado com voluntários.
```

---

## Fase 11 — Testes e CI/CD

Entregas:

* unit tests;
* integration tests;
* e2e básico;
* lint;
* type-check;
* security scan;
* Docker build;
* staging deploy.

Critério:

```text id="exkmzz"
Pipeline bloqueia merge se qualidade mínima falhar.
```

---

## Fase 12 — Onda 1 com voluntários

Entregas:

* 3 a 5 voluntários;
* coleta de feedback;
* dashboard;
* análise qualitativa;
* backlog de melhorias.

Critério:

```text id="fi8lxm"
Identificar bugs bloqueantes e validar se há pelo menos uma recomendação útil por sessão.
```

---

# 39. Definition of Done

Uma feature só está pronta quando:

* spec atualizada;
* migration criada, se aplicável;
* teste unitário criado;
* teste de integração criado, quando aplicável;
* logs estruturados adicionados;
* spans adicionados em operações relevantes;
* erro tratado;
* validação Pydantic implementada;
* documentação atualizada;
* payload de exemplo criado;
* CI passando;
* sem secrets no código;
* comportamento validado no Streamlit.

---

# 40. Definition of Ready para teste com voluntários

Antes de convidar voluntários, o sistema deve ter:

```text id="u5appd"
login funcionando
termo de participação
captura de expectativa
Quick Mode funcionando
run assíncrona funcionando
OpenAlex ou arXiv funcionando
3 a 5 recomendações por run
feedback explícito funcionando
event tracking funcionando
final survey funcionando
dashboard de validação funcionando
controle de custo funcionando
logs estruturados
health checks
backup PostgreSQL
exportação anonimizada
tratamento de erro sem quebrar a UI
```

---

# 41. Decisão final

A versão MVP Ready do POST-Rec deve ser construída como:

```text id="vtdbp0"
Streamlit UI
FastAPI API
PostgreSQL + pgvector
RabbitMQ
Celery Workers
OpenAI Structured Outputs
Alembic
structlog
OpenTelemetry
Grafana + Tempo + Loki + Prometheus
Validation Layer
Feedback Explicit + Implicit
Expectation Alignment Score
```

O objetivo do Alpha não é provar cientificamente a superioridade do sistema.

O objetivo é validar:

```text id="a53gyp"
O POST-Rec entrega recomendações que voluntários consideram úteis,
claras, confiáveis e alinhadas às expectativas iniciais?
```

Se a resposta for positiva nas ondas exploratórias, o projeto estará pronto para evoluir para:

* Deep Mode;
* estudo formal;
* integração com mais fontes acadêmicas;
* otimização do ranking;
* geração de plano experimental mais avançado;
* publicação científica sobre o próprio POST-Rec.
