from src.extractors.utils import now_fortaleza

print(now_fortaleza("%H:%M:%S"))

from src.extractors.dinamicoFilaEspera import dinamicoFilaEspera
from src.extractors.dinamicoVisaoGeral import dinamicoVisaoGeralAI, dinamicoVisaoGeralCP
from src.extractors.dinamicoAgendamentosIntegrado import agendamentos_integrado
from src.extractors.dinamicoAgendamento import dinamicoAgendamento

if __name__ == "__main__":
    agendamentos_integrado()
    dinamicoVisaoGeralCP()
    dinamicoVisaoGeralAI()
    dinamicoAgendamento()
    dinamicoFilaEspera()

    print(now_fortaleza("%H:%M:%S"))
