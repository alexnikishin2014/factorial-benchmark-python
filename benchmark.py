"""
Benchmark factorial implementations.
Goal: показать разницу между O(N) и O(N^2) подходами на реальных цифрах.
Автор: [Thymebra - Алексей Никишин]
Дата: [08.10.2026]
"""

import sys
import time
import math
import tracemalloc
from functools import reduce

# -------------------------
# НАСТРОЙКИ
# -------------------------
N = 990

# -------------------------
# ТЕСТИРУЕМЫЕ ФУНКЦИИ
# -------------------------

def for_loop(n):
    result = 1
    for x in range(1, n + 1): # мы не сохраняем список в переменную
        result *= x
    return result

def forLoop(repslist):
    first, *rest = repslist
    for x in rest:
        first *= x
    return first

# whileloop: АНТИПАТТЕРН.
# Выглядит просто, но каждый rest[1:] создаёт новый список и копирует все элементы.
# В тесте на N=990 это дало +11 КБ памяти и 34x замедление.
# Никогда не использовать в циклах на больших данных.
# Старый антипаттерн: каждый раз новый список (O(N^2))
def whileloop(repslist):
    first, *rest = repslist
    while rest:
        first *= rest[0]
        rest = rest[1:]
    return first

# Антипаттерн 2: pop(0) тоже O(N) на шаг → суммарно O(N^2), но константа меньше
def whileloop_pop(repslist):
    rest = repslist[:]
    result = 1
    while rest:
        result *= rest.pop(0)
    return result

# ПРАВИЛЬНЫЙ while: индекс + длина вынесена наружу (O(N))
def whileloop_index(repslist):
    i = 0
    n = len(repslist)      # <-- выносим длину один раз
    result = 1
    while i < n:           # <-- теперь только сравнение, без вызова len()
        result *= repslist[i]
        i += 1
    return result

# Оптимальный while !
# Оптимальный while: работает по счётчику, без списков, без лишних аллокаций.
# Сложность O(N), память O(1). На практике почти неотличим от for_loop.
def whileloop_index_N(n):
    i = 1
    result = 1
    while i <= n:
        result *= i
        i += 1
    return result


def recursive(repslist):
    if not repslist:
        return 1
    return repslist[0] * recursive(repslist[1:])

def reduced(n):
    return reduce(lambda x, y: x * y, range(1, n + 1), 1)

def prod_builtin(n):
    return math.prod(range(1, n + 1))

def builtinFunc(n):
    return math.factorial(n)

def iter_factorial(n):
    result = 1
    nums = list(range(1, n + 1)) # <-- вот эта строка съедает память
    it = iter(nums)       # встроенная функция
    
    for _ in range(n):    # просто цикл
        first = next(it)  # аналог: взять голову без копирования хвоста
        result *= first
    
    return result

def iter_factorial_clean(n):
    result = 1
    it = iter(range(1, n + 1))  # range — ленивый, памяти почти нет
    
    for _ in range(n):          # или просто: for x in it:
        first = next(it)
        result *= first
    
    return result

def iter_factorial_simple(n):
    result = 1
    for x in range(1, n + 1):  # range ленивый, никаких списков
        result *= x
    return result

# -------------------------
# ИНСТРУМЕНТЫ ЗАМЕРОВ
# -------------------------

def total(reps, func, *args, **kwargs):
    start = time.time()
    ret = None
    for _ in range(reps):
        ret = func(*args, **kwargs)
    return (time.time() - start, ret)

def bestof(reps, func, *args, **kwargs):
    best = float('inf')
    ret = None
    for _ in range(reps):
        t, r = total(1, func, *args, **kwargs)
        if t < best:
            best = t
            ret = r
    return (best, ret)

def bestoftotal(reps1, reps2, func, *args, **kwargs):
    return bestof(reps1, total, reps2, func, *args, **kwargs)

def measure_memory(func, *args, **kwargs):
    tracemalloc.start()
    _ = func(*args, **kwargs)          # прогрев
    tracemalloc.clear_traces()
    func(*args, **kwargs)              # замер
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak                        # возвращаем peak — это самое показательно

def best_memory(reps, func, *args, **kwargs):
    best = float('inf')
    for _ in range(reps):
        m = measure_memory(func, *args, **kwargs)
        if m < best:
            best = m
    return best

# -------------------------
# ФУНКЦИЯ АНАЛИЗА
# -------------------------

def analyze(results_time, results_mem, base_name):
    base_time = results_time[base_name]
    base_mem = results_mem[base_name]

    print()
    print(" " * 3 + "=" * 90)
    print(f"    АНАЛИЗ: относительно {base_name}")
    print(" " * 3 + "=" * 90)
    print()

    print("{:<22} | {:>12} | {:>13} | {:>14} | {:>15}".format(
        "Метод", "Время (с)", "Замедление", "Пик.память(байт)", "Доп. память"
    ))
    print("-" * 90)

    for name, t in sorted(results_time.items(), key=lambda x: x[1]):
        mem_bytes = results_mem[name]
        extra_bytes = mem_bytes - base_mem

        if name == base_name:
            ratio_str = "  —  (эталон)"
        else:
            ratio = t / base_time
            ratio_str = f"{ratio:.1f}x"

        print("{:<22} | {:>12.5f} | {:>13} | {:>16,} | {:>+15,}".format(
            name, t, ratio_str, mem_bytes, extra_bytes
        ))

    print()
    fastest_time = min(results_time, key=results_time.get)
    slowest_time = max(results_time, key=results_time.get)
    spread_time = results_time[slowest_time] / results_time[fastest_time]

    most_memory = max(results_mem, key=results_mem.get)
    least_memory = min(results_mem, key=results_mem.get)
    spread_mem = (results_mem[most_memory] / results_mem[least_memory]) if results_mem[least_memory] > 0 else 0

    print(f"  Быстрейший по времени: {fastest_time} ({results_time[fastest_time]:.5f} с)")
    print(f"  Медленнейший по времени: {slowest_time} ({results_time[slowest_time]:.5f} с), разница: {spread_time:.0f}x")
    print(f"  Больше всего пиковой памяти: {most_memory} ({results_mem[most_memory]:,} байт)")
    print(f"  Меньше всего пиковой памяти: {least_memory} ({results_mem[least_memory]:,} байт), разница: {spread_mem:.0f}x")
    print(" " * 3 + "=" * 90)

# -------------------------
# ЗАПУСК И ОСНОВНАЯ ЛОГИКА
# -------------------------

if __name__ == "__main__":
    print(sys.version)
    print()

    repslist = list(range(1, N + 1))

    tests = [
        (for_loop,       N),
        (forLoop,        repslist),
        (whileloop,      repslist),       # старый, с rest[1:]
        (whileloop_pop,  repslist),       # pop(0), всё ещё O(N^2)
        (whileloop_index,repslist),       # правильный while: n = len(...) снаружи
        (whileloop_index_N,N),# ✅ оптимальный while: чистый счётчик <-- теперь N, а не repslist
        (recursive,      repslist),
        (reduced,        N),
        (prod_builtin,   N),
        (builtinFunc,    N),
        (iter_factorial, N), #  Аналог сдвига указателя, без лишних аллокаций
        (iter_factorial_clean, N), # Ленивый range экономит память
        (iter_factorial_simple, N), # Минимум кода и никаких списков
    ]

    results_time = {}
    results_mem = {}

    # 1. Замер времени
    for func, arg in tests:
        best, (t, result) = bestoftotal(5, 1000, func, arg)
        results_time[func.__name__] = best
        print("{:<22}: {:.5f} => [{}!]".format(func.__name__, best, N))

    # 2. Замер памяти
    for func, arg in tests:
        m_best = best_memory(5, func, arg)
        results_mem[func.__name__] = m_best

    # 3. Автоматически находим самого быстрого по времени
    fastest_name = min(results_time, key=results_time.get)

    # 4. Запускаем анализ
    analyze(results_time, results_mem, fastest_name)

