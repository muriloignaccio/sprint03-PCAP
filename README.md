# ChargeGrid Intelligence — App ChargeGrid (Sprint 02)

Prova de conceito da **jornada de carga do App ChargeGrid**, desenvolvida para o desafio **EV Challenge 2026 — FIAP × GoodWe**, disciplina de **Pensamento Computacional**.

> Esta PoC simula a **lógica de uma sessão de carga** num carregador comercial (Linha GoodWe HCA G2), do QR code até o recibo, rodando direto no terminal. Não é o app de produção: é o **fluxo lógico** que o app executa, com fundamento técnico real.

---

## 🎯 A solução

Na Sprint 01, a equipe analisou o desafio (4 pilares, 5 problemas) e propôs uma arquitetura de 4 módulos — **Maestro de Demanda, Gateway Modbus→OCPP, App ChargeGrid e Núcleo de IA** — declarando o **App ChargeGrid** como foco de entrega.

Nesta Sprint 02, esse foco vira código: a lógica de decisão de uma sessão de carga, **funcionando e tomando decisões** conforme o estado da rede.

### Evolução desde a Sprint 01

| Sprint 01 | Sprint 02 |
|-----------|-----------|
| Análise e proposta no papel | Lógica do App **rodando** |
| Arquitetura dos 4 módulos | Uma funcionalidade prática e funcional |
| Diagramas e matriz problema × solução | Decisões executáveis (tarifa e potência reais) |

---

## 🔌 Os 4 conceitos do desafio (pela ótica do app)

O App é o "maestro da sessão": ele não constrói os outros módulos, mas **consome e exibe** o que eles fariam. Cada conceito está isolado numa função do código:

- **Tarifação e pagamento** — `calcular_tarifa()`, pré-autorização e cobrança pelo consumido
- **IA aplicada** — `calcular_tarifa()` (precificação dinâmica) que sobe no pico e cai com o sol
- **Controle de demanda** — `potencia_para_modo()` exibe a potência liberada (7 kW total ou 3,5 kW reduzida)
- **Interoperabilidade** — `enviar_ao_carregador()` simula `REST → OCPP → Modbus`

---

## 🧭 Fluxo do sistema

```mermaid
flowchart LR
  A["QR / vaga"] --> B["Login"]
  B --> C["Veiculo"]
  C --> D["Quanto carregar"]
  D --> E["Modo: Rapido / Economico"]
  E --> F["Tarifa dinamica"]
  F --> G["Pagamento"]
  G --> H["Liberar (gateway OCPP/Modbus)"]
  H --> I["Monitorar em tempo real"]
  I --> J["Recibo"]
```

---

## ▶️ Como rodar

Requisito: **Python 3.8+** (sem dependências externas).

```bash
python3 chargegrid_app.py            # usa o horario atual
python3 chargegrid_app.py --hora 20  # simula horario de pico (demonstracao)
python3 chargegrid_app.py --hora 23  # simula madrugada (rede com folga)
```

Basta seguir os menus digitando o número da opção desejada.

### Demonstração da inteligência (dois cenários)

| Horário | Rede | Potência liberada | Tarifa |
|---------|------|-------------------|--------|
| `--hora 23` (madrugada) | com folga | **7 kW (total)** | mais baixa |
| `--hora 20` (pico) | sob demanda alta | **3,5 kW (reduzida)** | mais alta |

Mesmo app, decisões diferentes conforme o estado da rede.

---

## ⚙️ Fundamento técnico

A simulação é ancorada em elementos reais do ecossistema:

- **Hardware:** Linha GoodWe HCA G2 (modelo `GW7K-HCA-20`, 7 kW monofásico) e seu modo **Controle Dinâmico de Carga**.
- **Registros Modbus** que o gateway leria/escreveria: potência atual (`10015`), status (`10017`), potência máxima (`10029`), limite de rede (`10039`).
- **Interoperabilidade:** padrão **OCPP** (1.6 / 2.0.1) traduzido a partir do Modbus nativo.
- **Tarifação:** a Resolução **ANEEL nº 1.000/2021** permite tarifa livre na recarga comercial — base da precificação dinâmica.

**Lógica de precificação:** `tarifa = base × fator_demanda × fator_modo × (1 − desconto_solar)`, onde o `fator_demanda` cresce conforme a carga do prédio se aproxima do limite contratado e o desconto cresce com a fração de energia solar no mix.

**Lógica de potência:** `disponível = (limite_contratado − carga_do_prédio) + geração_solar`; se `≥ 7 kW` libera potência total, senão potência reduzida (3,5 kW).

---

## 📁 Estrutura do repositório

```
.
├── chargegrid_app.py   # PoC interativa (jornada do App ChargeGrid)
└── README.md
```

---

## 👥 Equipe Pringles

| Integrante | RM |
|------------|-----|
| Enzo Ricardo Silva | 571333 |
| Eric Hernandes Penhalbel | 570237 |
| João Guilherme Figuereido | 572697 |
| Matheus Borges Soares | 574085 |
| Murilo Henrique Souza Ignacio | 573621 |
| Ryan Luther Roque | 572993 |

**Curso:** Ciência da Computação · 1º ano · FIAP
**Desafio:** ChargeGrid Intelligence — EV Challenge 2026 (FIAP × GoodWe)

---

## 🔗 Links

- 🎥 **Vídeo (YouTube, não listado):** https://www.youtube.com/watch?v=1mStMXvpGok
- 📋 **Quadro Kanban (público):** https://trello.com/b/kVtEAEet