import math
import re
import unicodedata

TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(texto):
    normalizado = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in normalizado if not unicodedata.combining(c))
    return TOKEN_RE.findall(sem_acento)


def split_passagens(contexto, tamanho=1500, sobreposicao=200):
    if not contexto:
        return []
    blocos = [b.strip() for b in re.split(r"\n\s*---\s*", contexto) if b.strip()]
    if len(blocos) <= 1:
        blocos = [p.strip() for p in re.split(r"\n{2,}", contexto) if p.strip()]
    passagens = []
    for bloco in blocos:
        if len(bloco) <= tamanho:
            passagens.append(bloco)
            continue
        inicio = 0
        tamanho_bloco = len(bloco)
        while inicio < tamanho_bloco:
            fim = min(inicio + tamanho, tamanho_bloco)
            passagens.append(bloco[inicio:fim].strip())
            if fim >= tamanho_bloco:
                break
            inicio = max(fim - sobreposicao, inicio + 1)
    return passagens


class IndiceBM25:
    def __init__(self, passagens, k1=1.5, b=0.75):
        self.passagens = passagens
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(p) for p in passagens]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0.0
        self.df = {}
        for tokens in self.doc_tokens:
            for termo in set(tokens):
                self.df[termo] = self.df.get(termo, 0) + 1
        self.n = len(passagens)

    def _idf(self, termo):
        df = self.df.get(termo, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def search(self, query, top_k=5):
        if not self.passagens:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        scores = []
        for i, tokens in enumerate(self.doc_tokens):
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            score = 0.0
            for termo in query_tokens:
                if termo not in tf:
                    continue
                freq = tf[termo]
                idf = self._idf(termo)
                denom = freq + self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avgdl or 1))
                score += idf * (freq * (self.k1 + 1)) / denom
            if score > 0:
                scores.append((score, i))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [self.passagens[i] for _, i in scores[:top_k]]


def construir_contexto(contexto, pergunta, orcamento):
    if not contexto:
        return ""
    if len(contexto) <= orcamento:
        return contexto
    passagens = split_passagens(contexto)
    if not passagens:
        return contexto[:orcamento]
    indice = IndiceBM25(passagens)
    selecionadas = indice.search(pergunta, top_k=len(passagens))
    partes = []
    total = 0
    for p in selecionadas:
        if total + len(p) + 2 > orcamento:
            restante = orcamento - total - 2
            if restante > 200:
                partes.append(p[:restante])
                total += restante
            break
        partes.append(p)
        total += len(p) + 2
    if not partes:
        return contexto[:orcamento]
    return "\n\n".join(partes)
