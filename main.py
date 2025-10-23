from datetime import datetime, timezone, timedelta

print(datetime.now(timezone(timedelta(hours=-3))).strftime("%H:%M:%S"))

from src.extractors.dinamicoAgendamentosIntegrado import agendamentos_integrado


def main():
    agendamentos_integrado()


if __name__ == "__main__":
    main()
    print(datetime.now(timezone(timedelta(hours=-3))).strftime("%H:%M:%S"))
