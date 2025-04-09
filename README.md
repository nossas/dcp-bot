
# Defesa Climática Popular

**Defesa Climática Popular** é um chatbot de WhatsApp desenvolvido com [Rasa](https://rasa.com/).

## 📦 Estrutura do Projeto

```
.
├── actions/                  # Ações customizadas do Rasa (Python)
│   ├── actions.py            # Classes de ações personalizadas
│   ├── db_utils.py           # Utilitários para comunicação com banco de dados
│   └── __init__.py
├── config.yml                # Configuração de pipelines e políticas do Rasa
├── credentials.yml           # Credenciais do banco de dados e do custom connector
├── domain.yml                # Definição de intents, entidades, slots e respostas
├── data/                     # Dados de treinamento
│   ├── nlu.yml               # Exemplo de frases de intenção
│   ├── rules.yml             # Regras de conversa
│   └── stories.yml           # Histórias de conversação
├── docker/                   # Infraestrutura de container
│   ├── Dockerfile            # Imagem do chatbot
│   ├── entrypoint.sh         # Script de entrada com verificação do banco
│   └── .config/rasa/global.yml  # Configurações globais do Rasa
├── docker-compose.yml        # Configuração principal do ambiente Docker
├── docker-compose-local.yml  # Variação local do docker-compose
├── endpoints.yml             # configuração do banco de dados para o tracker e configuração do action server
├── migrations.py             # Script de migração/inicialização do banco
├── requirements.txt          # Dependências do Python
├── whatsapp_connector.py     # Conector customizado para WhatsApp
├── media/                    # Mídias usadas nas interações do bot
└── README.md                 # Arquivo atual
```

## ⚙️ Configuração

### 🔑 Variáveis de ambiente obrigatórias para o ambiente local

Certifique-se de definir essas variáveis de ambiente no seu `docker-compose-local.yml`:

```yaml
POSTGRES_USER=usuario
POSTGRES_PASSWORD=senha
POSTGRES_DB=banco
POSTGRES_HOST=postgres
```

### 🔐 Credenciais 

- **`credentials.yml`** – Configuração de canal (WhatsApp, REST, etc.).
- **`endpoints.yml`** – Informações para o endpoint de ações, tracker store (banco), etc.

> Ambos os arquivos devem estar corretamente configurados para o bot funcionar e persistidos.

### 🛠 Permissões

Para rodar localmente você deve alterar as permissões das pastas:

```bash
chown -R 1001: .rasa
chown -R 1001: .tensorboard_diet
chown -R 1001: models
```

Ou melhor: certifique-se que o usuário dentro do container tem permissão para escrita no volume montado.

## 🚀 Execução

Execute localmente com:

```bash
docker-compose -f docker-compose-local.yml up --build
```

Para produção:
```bash
docker-compose up --build
```
###Persistir a pasta media para os arquivos de mídia recebidos pelo bot.

## 🧠 Sobre o Rasa

- Usa o pipeline de processamento de linguagem definido no `config.yml`.
- As histórias (`data/stories.yml`) e regras (`data/rules.yml`) definem como o bot responde a diferentes intents.
- Ações personalizadas (como acesso ao banco) estão em `actions/actions.py`.
