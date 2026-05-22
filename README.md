# Visual Field Labeling Tool (local)

Ferramenta em Streamlit para rotular campos visuais (HFA 24-2 / 30-2) de pacientes
com glaucoma. Roda **localmente** em cada máquina: os labelers recebem as imagens
prontas e os rótulos são salvos no próprio computador, para depois serem
consolidados.

---

## Fluxo geral

1. **Você (preparação)** roda `scripts/prepare_data.py` para gerar:
   - `data/prepared/manifest.csv` — um exame por linha (paciente, olho, nº do campo,
     idade, data, MD/PSD/VFI/GHT, nome da imagem);
   - `data/prepared/images/*.png` — os printouts convertidos de PDF para PNG.
2. **Distribuição** — envie para cada labeler: o código, o `manifest.csv` e a pasta
   `images/`. (O `.dta` e os PDFs originais ficam só com você.)
3. **Cada labeler** preenche `labeler_config.yaml` com o nome e roda o app.
4. **Coleta** — cada labeler te envia a pasta `labels/<nome>/`, em especial o
   `labels_<nome>.csv` consolidado.

---

## Preparação dos dados (você)

```bash
pip install -r requirements.txt
python scripts/prepare_data.py            # gera manifest + PNGs
python scripts/prepare_data.py --force    # reconverte PNGs existentes
python scripts/prepare_data.py --no-images  # só atualiza o manifest
```

O script lê `data/opv_export_masked_20220901.dta`, mantém apenas os exames cujo PDF
está em `data/hfa_gradings/`, calcula a idade e o número do campo visual (ordem
cronológica por olho) e converte cada PDF em PNG. É seguro re-rodar conforme novos
PDFs forem chegando — PNGs já gerados são pulados.

---

## Uso pelo labeler

1. Abra `labeler_config.yaml` e preencha `labeler_name` com o seu nome.
2. Rode:
   ```bash
   pip install streamlit pandas pyyaml pillow
   streamlit run app.py
   ```
3. Para cada paciente, todos os campos visuais aparecem lado a lado:
   **olho direito (R) na coluna da esquerda**, **olho esquerdo (L) na coluna da
   direita**, em ordem cronológica.

### Replicação automática (cascata)

- O **1º campo (mais antigo)** de cada olho é a fonte.
- Os campos seguintes do mesmo olho **copiam automaticamente** os rótulos da fonte.
- Ao **editar qualquer rótulo de um campo seguinte**, só aquele campo muda — ele
  passa a ser independente e deixa de seguir a fonte.
- Um botão **"↻ Copiar do #1"** permite re-acoplar um campo à fonte.

Botões **Salvar** e **Salvar e próximo paciente** gravam todos os campos do paciente.

---

## Onde os rótulos são salvos

```
labels/<nome>/
  progress.json                       # pacientes concluídos
  json/<maskedid>__<olho>__<nº>.json  # backup por exame
  labels_<nome>.csv                   # consolidado (1 linha por campo visual)
```

O `labels_<nome>.csv` é o arquivo a consolidar entre todos os labelers.
