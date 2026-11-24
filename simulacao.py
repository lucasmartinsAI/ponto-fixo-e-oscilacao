#!/usr/bin/env python3
"""
simulacao.py - ponto fixo, oscilacao e media das entradas, com o modelo de precos "teia de aranha".

Modelo (todos os numeros sao sinteticos):
  demanda:  D(p_t)   = c - d * p_t            (compradores reagem ao preco de hoje)
  oferta:   S(p_t-1) = a + b * p_(t-1)        (produtores decidem com o preco de ontem)
  mercado limpa:  p_t = F(p_(t-1)) = (c - a - b * p_(t-1)) / d  =  alfa - beta * p_(t-1),   beta = b / d

Consequencias (exatas neste modelo linear):
  - ponto fixo: p* = alfa / (1 + beta)
  - razao entre passos sucessivos: (p_(t+1) - p_t) / (p_t - p_(t-1)) = -beta  (negativa => oscila)
  - |beta| < 1: oscilacao amortecida, converge; beta = 1: oscila sem parar; beta > 1: diverge
  - media das entradas, G(p) = (1 - w) * p + w * F(p) com w = 1/2: razao passa a ser (1 - w) - w * beta,
    que fica dentro de (-1, 1) para beta ate 3; com beta = 0,7 e w = 1/2, e +0,15 (sem oscilar).

Uso:  python simulacao.py            (imprime as tabelas e grava grafico.svg)
Sem dependencias: so a biblioteca padrao do Python 3.
"""
import math
import random
import statistics

# ---- parametros sinteticos (fixos, para reproduzir) -------------------------------------------------
C, D, A = 100.0, 2.0, 10.0          # demanda c - d*p ; oferta base a
P0 = 10.0                           # preco inicial, longe do equilibrio
TOLERANCIA = 0.02                   # criterio de convergencia, ESCRITO ANTES de rodar: erro relativo < 2%
MAX_PASSOS = 200


def modelo(beta):
    """Devolve (F, p_estrela) para um beta dado (b = beta * d)."""
    b = beta * D
    alfa = (C - A) / D
    F = lambda p: alfa - beta * p
    return F, alfa / (1 + beta)


def aitken(x0, x1, x2):
    """Extrapolacao de Aitken a partir de 3 pontos (exata para convergencia geometrica sem ruido)."""
    den = (x2 - x1) - (x1 - x0)
    if den == 0:
        return float("nan")
    return x2 - (x2 - x1) ** 2 / den


def passos_ate_convergir(beta, w, tol=TOLERANCIA):
    """w = 1 e a iteracao simples; w = 0,5 e a media da entrada com a saida. None = nao convergiu."""
    F, pstar = modelo(beta)
    p = P0
    for n in range(1, MAX_PASSOS + 1):
        p = (1 - w) * p + w * F(p)
        if not math.isfinite(p) or abs(p) > 1e9:
            return None
        if abs(p - pstar) / pstar < tol:
            return n
    return None


def trajetoria(beta, w, n):
    F, pstar = modelo(beta)
    p, saida = P0, [P0]
    for _ in range(n):
        p = (1 - w) * p + w * F(p)
        saida.append(p)
    return saida, pstar


def experimento_1():
    """Iteracao simples com beta = 0,7: oscila e a razao entre passos e constante (= -beta)."""
    traj, pstar = trajetoria(0.7, 1.0, 10)
    linhas = ["| passo | preco | erro relativo | razao entre passos |", "|---:|---:|---:|---:|"]
    for t, p in enumerate(traj):
        razao = "" if t < 2 else f"{(traj[t] - traj[t - 1]) / (traj[t - 1] - traj[t - 2]):+.3f}"
        linhas.append(f"| {t} | {p:.3f} | {abs(p - pstar) / pstar:.1%} | {razao} |")
    return pstar, "\n".join(linhas)


def experimento_2():
    """Aitken com 3 pontos, sem ruido, para varios beta (<1): acerta o ponto fixo."""
    linhas = ["| beta | ponto fixo exato | estimativa (3 pontos) |", "|---:|---:|---:|"]
    for beta in (0.3, 0.7, 0.9):
        F, pstar = modelo(beta)
        x = [P0, F(P0), F(F(P0))]
        linhas.append(f"| {beta} | {pstar:.4f} | {aitken(*x):.4f} |")
    return "\n".join(linhas)


def experimento_3():
    """Passos ate o erro relativo < 2%: iteracao simples x media da entrada."""
    linhas = ["| beta | iteracao simples | media entrada/saida (w = 0,5) |", "|---:|---:|---:|"]
    for beta in (0.3, 0.7, 0.9, 1.3):
        s, m = passos_ate_convergir(beta, 1.0), passos_ate_convergir(beta, 0.5)
        linhas.append(f"| {beta} | {s if s else 'nao converge'} | {m if m else 'nao converge'} |")
    return "\n".join(linhas)


def experimento_4(repeticoes=2000, semente=7):
    """Aitken com ruido: erro relativo (mediana e percentil 90) conforme o ruido e o tamanho do passo."""
    rng = random.Random(semente)
    F, pstar = modelo(0.7)
    linhas = ["| ponto de partida | ruido (desvio) | erro mediano | erro no percentil 90 |", "|---|---:|---:|---:|"]
    for rotulo, p0 in (("longe do equilibrio (10)", 10.0), ("perto do equilibrio (25)", 25.0)):
        for sigma in (0.0, 0.5, 1.0, 2.0):
            erros = []
            for _ in range(repeticoes):
                x1 = F(p0) + rng.gauss(0, sigma)
                x2 = F(x1) + rng.gauss(0, sigma)
                est = aitken(p0, x1, x2)
                if math.isfinite(est):
                    erros.append(abs(est - pstar) / pstar)
            erros.sort()
            linhas.append(f"| {rotulo} | {sigma} | {statistics.median(erros):.1%} | {erros[int(0.9 * len(erros))]:.1%} |")
    return "\n".join(linhas)


def grafico_svg(caminho="grafico.svg", n=16):
    """Dois paineis em SVG puro (sem bibliotecas): (1) preco por passo, beta = 0,7, mostrando o zigue-zague;
    (2) erro relativo por passo em escala log, quatro combinacoes. Pontos abaixo de 1e-6 nao sao desenhados."""
    W, H, L, R = 760, 760, 70, 20
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="white"/>']
    px = lambda i: L + (W - L - R) * i / n

    # painel 1: precos (beta = 0,7)
    T1, B1 = 40, 340
    pmin, pmax = 5.0, 40.0
    py1 = lambda v: T1 + (B1 - T1) * (pmax - v) / (pmax - pmin)
    out.append(f'<text x="{W/2}" y="20" text-anchor="middle" font-size="14">1) Preco por passo, beta = 0,7 (dados sinteticos)</text>')
    for v in range(10, 41, 10):
        out.append(f'<line x1="{L}" y1="{py1(v)}" x2="{W-R}" y2="{py1(v)}" stroke="#ddd"/><text x="{L-8}" y="{py1(v)+4}" text-anchor="end">{v}</text>')
    _, pstar = modelo(0.7)
    out.append(f'<line x1="{L}" y1="{py1(pstar)}" x2="{W-R}" y2="{py1(pstar)}" stroke="#555" stroke-dasharray="5,4"/><text x="{W-R-4}" y="{py1(pstar)-5}" text-anchor="end" fill="#555">ponto fixo ({pstar:.1f})</text>')
    for k, (nome, w, cor) in enumerate((("iteracao simples (oscila)", 1.0, "#1f77b4"), ("com media entrada/saida (w = 0,5)", 0.5, "#2ca02c"))):
        traj, _ = trajetoria(0.7, w, n)
        pts = " ".join(f"{px(i):.1f},{py1(p):.1f}" for i, p in enumerate(traj))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="2"/>')
        out.append(f'<rect x="{L+10}" y="{T1+8+k*18}" width="14" height="3" fill="{cor}"/><text x="{L+30}" y="{T1+14+k*18}">{nome}</text>')
    out.append(f'<text x="{(L + W - R)/2}" y="{B1+30}" text-anchor="middle">passo</text>')
    for i in range(0, n + 1, 2):
        out.append(f'<text x="{px(i)}" y="{B1+16}" text-anchor="middle">{i}</text>')

    # painel 2: erro relativo (log)
    T2, B2 = 420, 700
    ymin, ymax = -6.0, 2.0
    py2 = lambda v: T2 + (B2 - T2) * (ymax - v) / (ymax - ymin)
    out.append(f'<text x="{W/2}" y="400" text-anchor="middle" font-size="14">2) Erro relativo por passo (escala log)</text>')
    for e in range(int(ymin), int(ymax) + 1):
        out.append(f'<line x1="{L}" y1="{py2(e)}" x2="{W-R}" y2="{py2(e)}" stroke="#ddd"/><text x="{L-8}" y="{py2(e)+4}" text-anchor="end">1e{e}</text>')
    ty = py2(math.log10(TOLERANCIA))
    out.append(f'<line x1="{L}" y1="{ty}" x2="{W-R}" y2="{ty}" stroke="#555" stroke-dasharray="5,4"/><text x="{W-R-4}" y="{ty-5}" text-anchor="end" fill="#555">tolerancia 2%</text>')
    series = [("beta 0,7 | iteracao simples", 0.7, 1.0, "#1f77b4"), ("beta 0,7 | com media", 0.7, 0.5, "#2ca02c"),
              ("beta 1,3 | iteracao simples (diverge)", 1.3, 1.0, "#d62728"), ("beta 1,3 | com media", 1.3, 0.5, "#ff7f0e")]
    for k, (nome, beta, w, cor) in enumerate(series):
        traj, ps = trajetoria(beta, w, n)
        pts = []
        for i, p in enumerate(traj):
            e = abs(p - ps) / ps
            if e >= 1e-6:
                pts.append(f"{px(i):.1f},{py2(math.log10(e)):.1f}")
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{cor}" stroke-width="2"/>')
        out.append(f'<rect x="{L+10}" y="{T2+8+k*18}" width="14" height="3" fill="{cor}"/><text x="{L+30}" y="{T2+14+k*18}">{nome}</text>')
    for i in range(0, n + 1, 2):
        out.append(f'<text x="{px(i)}" y="{B2+16}" text-anchor="middle">{i}</text>')
    out.append(f'<text x="{(L + W - R)/2}" y="{B2+36}" text-anchor="middle">passo</text>')
    out.append("</svg>")
    open(caminho, "w", encoding="utf-8").write("\n".join(out))


if __name__ == "__main__":
    pstar, t1 = experimento_1()
    print(f"Preco de equilibrio (beta = 0,7): {pstar:.4f}\n\n### Experimento 1 - iteracao simples, beta = 0,7\n{t1}")
    print(f"\n### Experimento 2 - Aitken com 3 pontos, sem ruido\n{experimento_2()}")
    print(f"\n### Experimento 3 - passos ate o erro relativo < {TOLERANCIA:.0%}\n{experimento_3()}")
    print(f"\n### Experimento 4 - Aitken com ruido (2000 repeticoes, semente 7), beta = 0,7\n{experimento_4()}")
    grafico_svg()
    print("\nGrafico gravado em grafico.svg")
