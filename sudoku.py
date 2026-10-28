import random

LAYOUT = {4: (2, 2), 6: (2, 3), 9: (3, 3)}      # размер блока: строк, столбцов
CLUES = {4: (9, 7, 6), 6: (22, 17, 14), 9: (40, 34, 28)}  # подсказки: легко/средне/сложно


class Sudoku:
    def __init__(self, n):
        self.n = n
        self.br, self.bc = LAYOUT[n]
        self.N = n * n
        self.full = (1 << n) - 1
        self.peers = []
        for i in range(self.N):
            r, c = divmod(i, n)
            p = set()
            for k in range(n):
                p.add(r * n + k)
                p.add(k * n + c)
            r0, c0 = r // self.br * self.br, c // self.bc * self.bc
            for rr in range(r0, r0 + self.br):
                for cc in range(c0, c0 + self.bc):
                    p.add(rr * n + cc)
            p.discard(i)
            self.peers.append(tuple(p))

    def box(self, i):
        r, c = divmod(i, self.n)
        return (r // self.br) * (self.n // self.bc) + c // self.bc

    def _cand(self, g, i):
        m = 0
        for p in self.peers[i]:
            if g[p]:
                m |= 1 << (g[p] - 1)
        return self.full & ~m

    def _pick(self, g):
        best, bm, bc = -1, 0, 99
        for i in range(self.N):
            if g[i] == 0:
                m = self._cand(g, i)
                c = bin(m).count("1")
                if c < bc:
                    best, bm, bc = i, m, c
                    if c <= 1:
                        break
        return best, bm

    def count(self, g, limit=2):
        i, m = self._pick(g)
        if i < 0:
            return 1
        t = 0
        for d in range(self.n):
            if m >> d & 1:
                g[i] = d + 1
                t += self.count(g, limit - t)
                g[i] = 0
                if t >= limit:
                    break
        return t

    def _fill(self, g):
        i, m = self._pick(g)
        if i < 0:
            return True
        ds = [d for d in range(self.n) if m >> d & 1]
        random.shuffle(ds)
        for d in ds:
            g[i] = d + 1
            if self._fill(g):
                return True
        g[i] = 0
        return False

    def make(self, level):
        """Возвращает (головоломка, решение) с единственным решением."""
        sol = [0] * self.N
        self._fill(sol)
        puz = sol[:]
        target = CLUES[self.n][level]
        order = list(range(self.N))
        random.shuffle(order)
        left = self.N
        for i in order:
            if left <= target:
                break
            v = puz[i]
            puz[i] = 0
            if self.count(puz[:], 2) == 1:
                left -= 1
            else:
                puz[i] = v
        return puz, sol
