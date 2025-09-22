### Fase 0 — Decisão de containers

* Um contêiner por serviço: streamlit-app, etl-worker (scraping/ingestão), evolution-api e n8n; facilita deploy independente, escala e confiabilidade em Cloud Run/Docker.\[1]\[2]
* EvolutionAPI e n8n têm guias oficiais de Docker com volumes e variáveis de ambiente; mantenha sessões e credenciais persistentes.\[3]\[4]
* 

### Fase 1 — Extração web e dados base (Semana 1)

* Objetivo: rodar Playwright, baixar CSV, normalizar em DataFrame e salvar local (parquet/CSV).\[5]
* Entregáveis:

  * Script Playwright funcionando com retry/backoff e logs.\[5]
  * Processamento com Pandas e metadados (timestamp, fonte).\[5]

* Dica: Use um Dockerfile específico para o etl-worker com browsers do Playwright instalados, isolado do Streamlit.\[2]
* 

### Fase 2 — Ingestão no BigQuery (Semana 2)

* Objetivo: enviar DataFrame para BigQuery com particionamento por data e clustering por fonte.\[2]
* Entregáveis:

  * Conector BigQuery (load\_table\_from\_dataframe) com WRITE\_APPEND e autodetect.\[2]
  * Tabelas raw particionadas por DATE(extraction\_timestamp).\[2]

* Boa prática: expor um endpoint HTTP no etl-worker para acionar ingestões via Cloud Scheduler/cron.\[2]
* 

### Fase 3 — Google Sheets e Oracle (Semana 3)

* Objetivo: adicionar ingestões de Sheets e Oracle ao mesmo pipeline, padronizando colunas e metadados.\[2]
* Entregáveis:

  * Extrator Sheets com credenciais de serviço; DataFrame normalizado.\[2]
  * Extrator Oracle com parametrização de queries e chunks; envio para BigQuery.\[2]

* Observação: mantenha tudo no etl-worker, cada fonte como “tarefas” independentes.\[1]
* 

### Fase 4 — Streamlit (Semana 4)

* Objetivo: dashboard simples lendo do BigQuery, com métricas e tabelas.\[2]
* Entregáveis:

  * App Streamlit em contêiner separado, apenas client BigQuery; sem Playwright para reduzir cold start.\[2]
  * Cache de consultas e health checks básicos.\[2]
  * 

### Fase 5 — EvolutionAPI (Semana 5)

* Objetivo: expor webhooks e comandos básicos para acionar extrações e enviar resumos.\[3]
* Entregáveis:

  * EvolutionAPI em contêiner dedicado com volumes (instances) e AUTHENTICATION\_API\_KEY.\[3]
  * Webhook handler (HTTP) em etl-worker ou microserviço pequeno para processar mensagens e chamar pipelines.\[2]
  * 

### Fase 6 — Orquestração e agendamentos (Semana 6)

* Objetivo: automação diária e semanal do ETL e notificações.\[2]
* Entregáveis:

  * Cloud Scheduler → HTTP do etl-worker no Cloud Run; ou cron no Docker Compose durante dev.\[2]
  * Notificações pós-execução via EvolutionAPI.\[3]

* Boas práticas Cloud Run: configurar concurrency, min/max instances e limitar exposição pública; usar Secret Manager para segredos.\[6]\[7]
* 

### Fase 7 — n8n + IA (Semana 7)

* Objetivo: criar automações low-code com IA que leem BigQuery e respondem no WhatsApp via EvolutionAPI.\[8]\[9]
* Entregáveis:

  * n8n em contêiner próprio com N8N\_ENCRYPTION\_KEY e volume persistente; instalar via Docker.\[4]
  * Fluxos:

    * Webhook (EvolutionAPI) → formata mensagem → nó OpenAI/Chat → consulta BigQuery (via HTTP Request para microserviço ou node/HTTP + serviço backend) → resposta no WhatsApp.\[9]\[10]
    * Templates: AI agent chat e “Building Your First WhatsApp Chatbot” podem acelerar.\[9]

* Observações:

  * Use o node OpenAI do n8n para prompts, ferramentas e controle de tokens.\[9]
  * Armazene chaves no gerenciador de credenciais do n8n.\[9]

Roadmap operacional (dev → prod)

* Desenvolvimento local: Docker Compose com 4 serviços (streamlit, etl, evolution-api, n8n) em uma rede e volumes dedicados para EvolutionAPI e n8n.\[4]\[3]
* Produção:

  * Cloud Run: streamlit e etl-worker como serviços distintos (autoscaling e HTTP triggers).\[2]
  * EvolutionAPI e n8n: Cloud Run se stateless/sem volumes; caso precise volumes persistentes simples, use VM com Docker Compose.\[4]\[3]
  * Endurecer Cloud Run: acesso público mínimo, limites de instâncias, rotulagem e gerenciamento de custos.\[11]\[6]

Estrutura mínima de repositório

* containers/etl (Dockerfile + src/pipeline) e containers/streamlit (Dockerfile + app).\[2]
* deploy/docker-compose.yml com serviços streamlit-app, etl-worker, evolution-api, n8n e volumes.\[4]\[3]
* CI/CD por serviço com build e deploy para Artifact/Cloud Run.\[2]

Critérios de pronto por fase

* F1: CSV local e logs; F2: dados no BigQuery (tabela raw particionada); F3: Sheets/Oracle no mesmo dataset; F4: dashboard visível; F5: WhatsApp envia “extrair” e recebe status; F6: scheduler diário no ar; F7: n8n responde perguntas no WhatsApp consultando BigQuery com suporte de IA.\[9]\[3]\[4]\[2]
