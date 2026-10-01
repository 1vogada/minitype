"""Code snippets to type. Whitespace and newlines collapse to single spaces,
so you practise the symbols and keywords rather than the indentation."""

import random

SNIPPETS = {
    "python": [
        ("fizzbuzz", """for i in range(1, 101):
    if i % 15 == 0: print("FizzBuzz")
    elif i % 3 == 0: print("Fizz")
    elif i % 5 == 0: print("Buzz")
    else: print(i)"""),
        ("fibonacci", """def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a"""),
        ("dataclass", """@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0
    def dist(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5"""),
        ("word count", """counts = {}
with open(path, encoding="utf-8") as f:
    for line in f:
        for word in line.split():
            counts[word] = counts.get(word, 0) + 1
top = sorted(counts.items(), key=lambda kv: -kv[1])[:10]"""),
        ("binary search", """def search(xs, target):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if xs[mid] == target: return mid
        if xs[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1"""),
        ("comprehension", """squares = [n * n for n in range(10) if n % 2]
lookup = {name: len(name) for name in ["ada", "grace", "linus"]}
pairs = list(zip(squares, lookup.values()))"""),
        ("context manager", """from contextlib import contextmanager
@contextmanager
def timer(label):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{label}: {time.perf_counter() - start:.3f}s")"""),
        ("async fetch", """async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(u) for u in urls]
        return await asyncio.gather(*tasks)"""),
    ],
    "javascript": [
        ("debounce", """function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}"""),
        ("fetch json", """const res = await fetch("/api/users?page=" + page);
if (!res.ok) throw new Error(`HTTP ${res.status}`);
const { users, total } = await res.json();"""),
        ("array methods", """const adults = people
  .filter((p) => p.age >= 18)
  .map(({ name, age }) => ({ name, age }))
  .sort((a, b) => a.age - b.age);"""),
        ("class", """class Counter {
  #count = 0;
  increment() { return ++this.#count; }
  get value() { return this.#count; }
}"""),
        ("event listener", """document.querySelector("#save").addEventListener("click", (e) => {
  e.preventDefault();
  localStorage.setItem("draft", editor.value);
});"""),
        ("reduce", """const totals = orders.reduce((acc, o) => {
  acc[o.customer] = (acc[o.customer] ?? 0) + o.amount;
  return acc;
}, {});"""),
        ("promise", """const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
for (const step of steps) {
  await sleep(250);
  console.log(`step ${step.id} done`);
}"""),
    ],
}


def pick(lang):
    """(name, words) of a random snippet in lang."""
    name, text = random.choice(SNIPPETS.get(lang) or SNIPPETS["python"])
    return name, text.split()
