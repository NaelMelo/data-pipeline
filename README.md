# 📁 Ideia de Estrutura inicial do projeto
data-pipeline/
├── data/
│   └── raw/                      # CSVs baixados (temporários)
├── src/
│   ├── connectors/
│   │   └── bq.py                 # upload_df e helpers do BigQuery 
│   ├── extractors/
│   │   └── web_scraper.py        # download_csv com Playwright
│   ├── pipeline/
│   │   └── run_once.py           # orquestra download → clean → upload
│   ├── utils.py                  # funções utilitárias (paths, limpeza, logs)
│   └── __init__.py               # torna src um pacote
├── .env.local
├── requirements.txt              # dependências mínimas
└── README.md                     # instruções de uso
