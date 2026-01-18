
# Defesa Climática Popular

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Defesa Climática Popular** é um chatbot de WhatsApp desenvolvido com [Rasa](https://rasa.com/).

## 📄 Licenca

Este projeto esta licenciado sob a **GNU Affero General Public License v3.0 (AGPL-3.0)**.  
Veja `LICENSE` para detalhes.

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

Você pode copiar os arquivos de exemplo e configurar com os dados reais.
- **`credentials.yml`** – Configuração de canal (WhatsApp, REST, etc.).
- **`endpoints.yml`** – Informações para o endpoint de ações, tracker store (banco), etc.

> Ambos os arquivos devem estar corretamente configurados para o bot funcionar e persistidos.

### 🛠 Permissões

Para rodar localmente você deve alterar as permissões das pastas:

```bash
chown -R 1001: .rasa
chown -R 1001: .tensorboard_diet
chown -R 1001: models
chown -R 1001: media
```

Ou melhor: certifique-se que o usuário dentro do container tem permissão para escrita no volume montado.

## 🚀 Execução

Execute localmente com:

```bash
docker-compose -f docker-compose-local.yml up --build
```
### 🌐 Executando Localmente com ngrok

Para rodar o projeto **Defesa Climática Popular** localmente e integrar com o WhatsApp (ou outra interface externa), é necessário expor seu servidor Rasa na internet. A maneira mais simples de fazer isso é utilizando o [ngrok](https://ngrok.com/).

#### Passos:

1. **Instale o ngrok** (caso ainda não tenha):
   ```bash
   sudo apt install snapd
   sudo snap install ngrok
   ```
   ou baixe diretamente pelo site [https://ngrok.com/download](https://ngrok.com/download).

2. **Autentique seu ngrok** (substitua `SEU_TOKEN` pelo seu token pessoal):
   ```bash
   ngrok config add-authtoken SEU_TOKEN
   ```

3. **Inicie o túnel para a porta 5005**, que é onde o Rasa estará ouvindo:
   ```bash
   ngrok http 5005
   ```

4. Copie o **endpoint HTTPS** gerado pelo ngrok (exemplo: `https://abc123.ngrok.io`) e configure esse endereço no seu provedor de WhatsApp ou em sistemas externos que se comuniquem com o bot.

Para produção:
```bash
docker-compose up --build
```
###Persistir a pasta media para os arquivos de mídia recebidos pelo bot.

## 🧠 Sobre o Rasa

- Usa o pipeline de processamento de linguagem definido no `config.yml`.
- As histórias (`data/stories.yml`) e regras (`data/rules.yml`) definem como o bot responde a diferentes intents.
- Ações personalizadas (como acesso ao banco) estão em `actions/actions.py`.
