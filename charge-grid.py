"""
App ChargeGrid - Prova de Conceito interativa (Sprint 02)
=========================================================
Equipe Pringles - FIAP x GoodWe - Pensamento Computacional

Simula a JORNADA DO USUARIO no App ChargeGrid direto no terminal: a pessoa
navega pelas "telas" escolhendo opcoes (1, 2, 3...), como se estivesse no app.

Como rodar:
  python3 chargegrid_app.py            (usa o horario atual)
  python3 chargegrid_app.py --hora 20  (simula um horario, p/ demonstrar pico)
"""
import sys
from datetime import datetime

# --------------------------------------------------------------------------
# Parametros do cenario
# --------------------------------------------------------------------------
TARIFA_BASE = 1.20          # R$/kWh
LIMITE_CONTRATADO = 75.0    # kW - demanda contratada do estabelecimento
POTENCIA_TOTAL = 7.0        # kW - HCA G2 monofasico (GW7K-HCA-20)
POTENCIA_REDUZIDA = 3.5     # kW

VAGAS = {1: "CP-01", 2: "CP-03", 3: "CP-07"}
CARTAO = "**** 4071"

# Veiculos salvos na conta (em memoria, so durante a sessao)
veiculos = [
    {"placa": "FIA2C26", "modelo": "BYD Dolphin", "bateria": 44},
    {"placa": "RJ4E2030", "modelo": "VW ID.4", "bateria": 77},
]


# --------------------------------------------------------------------------
# Utilitarios de tela e entrada
# --------------------------------------------------------------------------
def tela(titulo):
    print("\n" + "=" * 52)
    print(f"  {titulo}")
    print("=" * 52)


def perguntar(texto, padrao=""):
    """Le entrada; se rodar sem terminal (EOF), devolve o padrao."""
    try:
        r = input(texto).strip()
    except EOFError:
        r = ""
    return r if r else padrao


def escolher(opcoes, padrao=1):
    """Mostra um menu numerado e devolve a opcao escolhida (1..n)."""
    for i, o in enumerate(opcoes, 1):
        print(f"    {i}. {o}")
    while True:
        r = perguntar(f"  Escolha [{padrao}]: ", str(padrao))
        if r.isdigit() and 1 <= int(r) <= len(opcoes):
            return int(r)
        print("  Opcao invalida, tente de novo.")


# --------------------------------------------------------------------------
# Dados que o APP RECEBE do backend (simulados a partir do horario).
# Em producao viriam do medidor principal e do inversor solar via Modbus.
# --------------------------------------------------------------------------
def estado_da_rede(hora):
    if hora in (11, 12, 13, 19, 20, 21):
        carga = 70.0
    elif 9 <= hora <= 18:
        carga = 50.0
    else:
        carga = 25.0
    solar = round(18.0 * max(0.0, 1 - abs(13 - hora) / 6), 1) if 7 <= hora <= 17 else 0.0
    fracao_solar = round(min(0.80, solar / 25.0), 2)
    return carga, solar, fracao_solar


# Os 4 conceitos, isolados em funcoes faceis de apontar no video -----------
def calcular_tarifa(modo, carga, fracao_solar):
    """IA / precificacao dinamica: sobe com a demanda, cai com o sol,
    e o modo Economico ainda da um desconto."""
    fator_demanda = 1.0 + 0.6 * (carga / LIMITE_CONTRATADO)
    fator_modo = 1.0 if modo == "Rapido" else 0.90      # Economico = -10%
    tarifa = TARIFA_BASE * fator_demanda * fator_modo * (1 - 0.25 * fracao_solar)
    return round(max(tarifa, 0.40), 2)


def potencia_para_modo(modo, carga, solar):
    """Controle de demanda (o Maestro decide, o app exibe).
    Rapido = pega o maximo que a rede liberar; Economico = ritmo reduzido."""
    disponivel = (LIMITE_CONTRATADO - carga) + solar
    if modo == "Economico":
        if disponivel >= POTENCIA_REDUZIDA:
            return POTENCIA_REDUZIDA, "ritmo economico (3,5 kW)"
        return 0.0, "rede sem folga"
    # Rapido
    if disponivel >= POTENCIA_TOTAL:
        return POTENCIA_TOTAL, "potencia total (7 kW)"
    if disponivel >= POTENCIA_REDUZIDA:
        return POTENCIA_REDUZIDA, "potencia reduzida (3,5 kW) - rede sob demanda alta"
    return 0.0, "rede sem folga"


def enviar_ao_carregador(comando, valor=None):
    """Interoperabilidade: app fala REST -> gateway traduz p/ OCPP -> Modbus."""
    extra = f" ({valor})" if valor else ""
    print(f"    > app -> gateway (OCPP/Modbus) -> carregador: {comando}{extra}")


# --------------------------------------------------------------------------
# Jornada do usuario (as telas)
# --------------------------------------------------------------------------
def rodar(hora):
    carga, solar, fracao_solar = estado_da_rede(hora)

    # 1. Boas-vindas
    tela("App ChargeGrid")
    nome = perguntar("  Qual o seu nome? ", "Cliente")
    print(f"  Seja bem-vindo ao ChargeGrid, {nome}!")

    # 2. Escolher a vaga (QR)
    tela("Qual carregador voce vai usar?")
    v = escolher([f"Vaga {VAGAS[1]}", f"Vaga {VAGAS[2]}", f"Vaga {VAGAS[3]}"])
    vaga = VAGAS[v]
    print(f"  Vaga {vaga} selecionada (QR lido).")

    # 3. Escolher o veiculo (ou cadastrar novo - guarda na sessao)
    tela("Escolha seu veiculo")
    opcoes_veic = [f"{vc['placa']} - {vc['modelo']}" for vc in veiculos]
    opcoes_veic.append("Novo veiculo")
    esc = escolher(opcoes_veic)
    if esc == len(opcoes_veic):  # novo veiculo
        placa = perguntar("  Digite a placa: ", "ABC1D23").upper()
        novo = {"placa": placa, "modelo": "BYD Dolphin", "bateria": 44}
        veiculos.append(novo)            # guarda na sessao
        veiculo = novo
        print(f"  Veiculo cadastrado: {placa} - {novo['modelo']} (salvo na conta).")
    else:
        veiculo = veiculos[esc - 1]
    soc_inicial = 30
    print(f"  {veiculo['placa']} - {veiculo['modelo']} | bateria {veiculo['bateria']} kWh "
          f"| carga atual {soc_inicial}%")

    # 4. Quanto carregar
    tela("Quanto voce quer carregar?")
    q = escolher(["Ate 80% (recomendado)", "Ate 100%", "Outro valor"])
    if q == 1:
        meta = 80
    elif q == 2:
        meta = 100
    else:
        try:
            meta = max(int(perguntar("  Carregar ate quantos %? ", "80")), soc_inicial + 1)
        except ValueError:
            meta = 80
    print(f"  Meta: carregar ate {meta}%.")

    # 5. Modo de carga (simples: Rapido x Economico; solar entra no preco sozinho)
    tela("Modo de carga")
    print("    Rapido: carrega o mais rapido possivel.")
    print("    Economico: um pouco mais lento, com desconto na tarifa.")
    m = escolher(["Rapido", "Economico"])
    modo = "Rapido" if m == 1 else "Economico"

    # 6. Tarifa e pagamento
    tela("Tarifa e pagamento")
    tarifa = calcular_tarifa(modo, carga, fracao_solar)
    pot, desc_pot = potencia_para_modo(modo, carga, solar)
    print(f"  Tarifa agora: R$ {tarifa:.2f}/kWh  (modo {modo})")
    if fracao_solar >= 0.2:
        print(f"  Energia solar disponivel agora ({fracao_solar*100:.0f}%): preco reduzido.")
    print(f"  Carregamento liberado: {desc_pot}")
    if pot == 0.0:
        print("  Sem folga na rede agora. Tente em outro horario.")
        return

    energia_alvo = veiculo["bateria"] * (meta - soc_inicial) / 100.0
    pre_auth = round(energia_alvo * tarifa * 1.2, 2)
    print(f"  Estimativa: {energia_alvo:.1f} kWh -> pre-autorizacao de R$ {pre_auth:.2f}")
    print("  Forma de pagamento:")
    formas = [f"Cartao {CARTAO}", "Pix", "Apple Pay"]
    forma = formas[escolher(formas) - 1]

    # 7. Confirmacao e liberacao
    tela("Confirmacao")
    print(f"  Veiculo {veiculo['placa']} | meta {meta}% | modo {modo}")
    print(f"  Tarifa R$ {tarifa:.2f}/kWh | pagamento via {forma}")
    if escolher(["Confirmar e iniciar", "Cancelar"]) == 2:
        print("  Sessao cancelada.")
        return
    enviar_ao_carregador("DEFINIR_POTENCIA", f"{pot} kW")
    enviar_ao_carregador("LIBERAR")
    print("  Carga liberada! Acompanhe abaixo.")

    # 8. Monitoramento em tempo real
    tela("Carregando")
    energia = custo = 0.0
    soc = float(soc_inicial)
    minutos = 0
    while soc < meta:
        print(f"    Bateria {soc:4.0f}% | {energia:4.1f} kWh | R$ {custo:5.2f} "
              f"| solar {energia*fracao_solar:3.1f} kWh | {minutos} min")
        if escolher(["Continuar carregando (+30 min)", "Desconectar agora"]) == 2:
            break
        passo = min(pot * 0.5, energia_alvo - energia)   # nao passa da meta
        energia += passo
        custo += passo * tarifa
        minutos += round(passo / pot * 60)
        soc = min(soc_inicial + (energia / veiculo["bateria"]) * 100.0, meta)

    # 9. Recibo
    tela("Recibo ChargeGrid")
    enviar_ao_carregador("ENCERRAR")
    print(f"  Cliente ............ {nome}")
    print(f"  Veiculo ............ {veiculo['placa']} - {veiculo['modelo']}")
    print(f"  Energia entregue ... {energia:.1f} kWh  (bateria em {soc:.0f}%)")
    print(f"  Tarifa ............. R$ {tarifa:.2f}/kWh")
    print(f"  Origem ............. {fracao_solar*100:.0f}% solar / {(1-fracao_solar)*100:.0f}% rede")
    print(f"  Tempo .............. {minutos} min")
    print(f"  Pagamento .......... {forma}")
    print(f"  VALOR COBRADO ...... R$ {custo:.2f}  (pre-auth de R$ {pre_auth:.2f} liberada)")
    print(f"\n  Obrigado por usar o ChargeGrid, {nome}!")


def main():
    hora = datetime.now().hour
    if "--hora" in sys.argv:
        try:
            hora = int(sys.argv[sys.argv.index("--hora") + 1]) % 24
        except (ValueError, IndexError):
            pass
    rodar(hora)


if __name__ == "__main__":
    main()