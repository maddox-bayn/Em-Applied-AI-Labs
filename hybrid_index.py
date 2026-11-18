"""Chapters 5–6. python hybrid_index.py. Requires the search extras in README."""
from qdrant_client import QdrantClient, models
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer
from ch06 import DOCS, tokens


def search(query: str, tenant: str) -> list[str]:
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    db = QdrantClient(":memory:")
    dim = encoder.get_sentence_embedding_dimension()
    assert dim is not None
    db.create_collection("policy",vectors_config=models.VectorParams(size=dim,distance=models.Distance.COSINE))
    for i, p in enumerate(DOCS):
        db.upsert("policy",[models.PointStruct(id=i,vector=encoder.encode(p.text).tolist(),
                  payload={"tenant":p.tenant,"passage":p.id})])
    scope = models.Filter(must=[models.FieldCondition(key="tenant",match=models.MatchValue(value=tenant))])
    hits = db.query_points("policy",query=encoder.encode(query).tolist(),query_filter=scope,limit=4).points
    allowed = [p for p in DOCS if p.tenant==tenant]
    if not allowed:
        return []
    scores = BM25Okapi([tokens(p.text) for p in allowed]).get_scores(tokens(query))
    lexical = [p.id for p,_ in sorted(zip(allowed,scores), key=lambda pair:pair[1],reverse=True)
               if set(tokens(p.text)) & set(tokens(query))]
    fused: dict[str,float] = {}
    for ranking in [lexical,[str(h.payload["passage"]) for h in hits if h.payload]]:
        for rank, key in enumerate(ranking,1):
            fused[key] = fused.get(key,0) + 1/(60+rank)
    shortlist = sorted(fused,key=fused.__getitem__,reverse=True)[:3]
    by_id = {p.id:p.text for p in allowed}
    if not shortlist:
        return []
    rerank = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    relevance = rerank.predict([(query,by_id[key]) for key in shortlist])
    return [key for key,_ in sorted(zip(shortlist,relevance), key=lambda pair:pair[1],reverse=True)]

if __name__ == "__main__":
    print(search("charged twice","A"))
