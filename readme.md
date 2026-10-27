# 📊 EPI-DATA Backend - API e Processamento de Dados

O backend do sistema **EPI-DATA** é uma API REST desenvolvida em **Django (Python)** projetada para gerenciar o mapeamento epidemiológico e a cobertura vacinal do município de Floriano, PI. O sistema processa dados brutos do SINAN (.dbf) e do DataSUS (.csv) utilizando **Pandas**, servindo informações consolidadas e rápidas para o frontend em React.

## 🚀 Tecnologias Utilizadas

* **Framework:** Django & Django REST Framework
* **Banco de Dados:** PostgreSQL (Hospedado no Neon)
* **Processamento de Dados:** Pandas & DBFRead
* **Autenticação:** JWT (JSON Web Tokens)
* **Inteligência Artificial:** Google Gemini API (RAG com Embeddings para suporte contextualizado)
* **Hospedagem:** Render

---

## 💉 Integração DataSUS: Cobertura Vacinal

Devido à conhecida instabilidade e aos constantes *timeouts* da API pública do OpenDataSUS (CKAN), além do tamanho massivo dos microdados nacionais (arquivos ZIP que ultrapassam 1 GB), a arquitetura do EPI-DATA **não realiza chamadas HTTP diretas em tempo real** aos servidores do governo.

Para garantir performance em infraestruturas gratuitas/limitadas (Render/Neon) e evitar falhas por memória (Out of Memory), o sistema utiliza uma abordagem de **Ingestão via Painel Administrativo**.

### O Fluxo de Atualização

1. Obtenção do CSV otimizado do Ministério da Saúde (instruções abaixo).
2. Upload do arquivo `.csv` através do Django Admin (`/admin/api/uploaddbf/`).
3. O backend intercepta o arquivo, e o `Pandas` faz o tratamento, cálculos de porcentagem (`(doses / populacao) * 100`) e filtros exclusivos para o município de Floriano.
4. Os dados são salvos no PostgreSQL na tabela `CoberturaVacinal` e imediatamente disponibilizados no endpoint `/api/coberturavacinal/`.

---

## 📖 Passo a Passo: Como Obter os Dados do DataSUS

Existem duas abordagens para extrair o CSV necessário para o sistema. Escolha a que melhor se adapta à disponibilidade de dados do Ministério da Saúde.

### Opção A: Extração Rápida via TabNet (Para anos consolidados)

O TabNet é o sistema legado do DataSUS, ideal para extrair tabelas já mastigadas e extremamente leves (1 a 2 KB).

1. Acesse a página do **TabNet DataSUS** (Informações de Saúde).
2. Navegue até **Assistência à Saúde** -> **Imunizações**.
3. Selecione a opção **Cobertura** (não escolha "Doses Aplicadas").
4. Selecione a abrangência geográfica: **Piauí**.
5. No formulário de cruzamento de dados, configure exatamente assim:
   * **Linha:** Município
   * **Coluna:** Não ativa
   * **Conteúdo:** Cobertura Vacinal
   * **Medidas:** Selecione todas as vacinas da lista (Segure `Shift` do primeiro ao último item).
   * **Períodos Disponíveis:** Selecione o ano desejado (ex: 2022).
   * **Seleções Disponíveis:** Expanda a aba **Município** e selecione EXCLUSIVAMENTE **"220390 Floriano"**.
6. Clique em **"Mostra"** no final da página.
7. Na página de resultados, clique em **Cópia como .CSV** ou **Download CSV**.
8. Faça o upload deste arquivo no Django Admin do EPI-DATA.

### Opção B: "Força Bruta" Local (Para anos recentes/Microdados de +1GB)

Quando o TabNet estiver desatualizado e você precisar baixar os microdados brutos do ano vigente no **Portal de Dados Abertos (OpenDataSUS)** (ex: `vacinacao_set_2026_csv.zip`), **NÃO** envie o CSV de 3GB extraído para o servidor online. Utilize o script de peneira local para processar os dados na sua máquina.

1. Baixe e extraia o arquivo `.zip` gigante no seu computador local.
2. Coloque o arquivo CSV extraído na mesma pasta do script `peneira_datasus.py` (localizado na raiz do repositório/ferramentas).
3. Abra o script `peneira_datasus.py` e certifique-se de que a variável `arquivo_gigante` contenha o nome exato do arquivo extraído.
4. Execute o script no seu terminal local:

   ```bash
   python peneira_datasus.py
   ```

5. O script utilizará processamento em chunks (blocos) no Pandas para não estourar a memória RAM do seu PC, filtrando as linhas referentes ao município de Floriano (Código IBGE: 220390) e somando as doses.
6. Em poucos minutos, um arquivo chamado `cobertura_floriano_XXXX.csv` será gerado com cerca de 1 KB.
7. Faça o upload deste pequeno arquivo `.csv` no Django Admin.

---

## 🦠 Importação de Dados SINAN (Endemias)

O mapeamento de endemias (Dengue, Sífilis, Hanseníase, Chagas, etc.) segue o mesmo fluxo administrativo, mas consome arquivos originais `.dbf` do SINAN.

O painel admin identifica automaticamente a doença pelo nome do arquivo (ex: `dengon.dbf` para Dengue, `sifi.dbf` para Sífilis). Ao processar casos de Dengue, o sistema também compila endereços para permitir análises georreferenciadas (casos por bairro).

---

## 🔗 Endpoints Principais (API)

| Método | Endpoint                 | Descrição                                                  |
|--------|--------------------------|------------------------------------------------------------|
| `GET` | `/api/coberturavacinal/` | Retorna a lista de cobertura das vacinas por ano.          |
| `GET` | `/api/tuberculose/`      | Registros individuais de tuberculose.                      |
| `GET` | `/api/sifilis/`           | Registros individuais de sifilis.                          |
| `GET` | `/api/chagas/`           | Registros individuais de chagas.                           |
| `GET` | `/api/violenciadomestica/`           | Registros individuais de violência doméstica.              |
| `GET` | `/api/hans/`           | Registros individuais de hanseníase.                       |
| `GET` | `/api/hepatite/`           | Registros individuais de hepatite.                         |
| `GET` | `/api/animaispec/`           | Registros individuais de animais peçonhentos.              |
| `GET` | `/api/intoxicacao/`           | Registros individuais de intoxicação.                      |
| `GET` | `/api/leish/`           | Registros individuais de leishmaniose.                     |
| `GET` | `/api/aidsadulta/`           | Registros individuais de aids adulta.                            |
| `GET` | `/api/casos_por_bairro/` | Dados agrupados de dengue por bairro (útil para Heatmaps). |
| `POST` | `/api/chat/`             | Endpoint do assistente virtual governado por IA (Gemini).  |
| `POST` | `/api/token/`            | Autenticação e geração de JWT.                             |