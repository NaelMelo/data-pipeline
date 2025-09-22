import time
from functools import wraps


def medir_tempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fim = time.time()

        tempo_total = fim - inicio
        minutos = int(tempo_total // 60)
        segundos = int(tempo_total % 60)

        print(f"Tempo de execução de {func.__name__}: {minutos:02d}:{segundos:02d}\n")
        return resultado

    return wrapper
