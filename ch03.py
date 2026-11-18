"""Run: python ch03.py [starter|solution]. Requires torch."""
import sys

import torch
from torch import Tensor, nn


class Decoder(nn.Module):
    def __init__(self, vocab: int, width: int = 24, limit: int = 64) -> None:
        super().__init__()
        self.token = nn.Embedding(vocab, width)
        self.position = nn.Embedding(limit, width)
        self.qkv = nn.Linear(width, 3 * width)
        self.ff = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, width * 2),
                                nn.GELU(), nn.Linear(width * 2, width))
        self.head = nn.Linear(width, vocab)

    def forward(self, ids: Tensor, cache: tuple[Tensor, Tensor] | None = None
                ) -> tuple[Tensor, tuple[Tensor, Tensor]]:
        offset = 0 if cache is None else cache[0].size(1)
        pos = torch.arange(offset, offset + ids.size(1), device=ids.device)
        x = self.token(ids) + self.position(pos)
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        if cache is not None:
            k, v = torch.cat((cache[0], k), 1), torch.cat((cache[1], v), 1)
        scores = q @ k.transpose(1, 2) / q.size(-1) ** 0.5
        future = torch.arange(k.size(1), device=ids.device)[None, :] > pos[:, None]
        x = x + scores.masked_fill(future, float("-inf")).softmax(-1) @ v
        return self.head(x + self.ff(x)), (k, v)


def run(cached: bool) -> None:
    torch.manual_seed(7)
    torch.set_num_threads(1)
    corpus = "invoice rejected currency mismatch receipt missing " * 12
    alphabet = sorted(set(corpus))
    ids = torch.tensor([alphabet.index(c) for c in corpus])
    net = Decoder(len(alphabet))
    opt = torch.optim.AdamW(net.parameters(), lr=0.003)
    for _ in range(35):
        ix = torch.randint(len(ids)-17, (8, 1)) + torch.arange(17)
        batch = ids[ix]
        logits, _ = net(batch[:, :-1])
        loss = nn.functional.cross_entropy(logits.flatten(0, 1), batch[:, 1:].reshape(-1))
        opt.zero_grad()
        loss.backward()
        opt.step()
    net.eval()
    with torch.inference_mode():
        prefix = ids[:7][None, :]
        logits, kv = net(prefix)
        # Appending more tokens may not alter earlier positions.
        longer, _ = net(ids[:10][None, :])
        torch.testing.assert_close(logits, longer[:, :7], atol=1e-5, rtol=1e-5)
        for _ in range(10):
            token = logits[:, -1].argmax(-1, keepdim=True)
            prefix = torch.cat((prefix, token), 1)
            exact, _ = net(prefix)
            if cached:
                logits, kv = net(token, kv)
                torch.testing.assert_close(logits[:, -1], exact[:, -1], atol=1e-5, rtol=1e-5)
            else:
                logits = exact
        print("".join(alphabet[i] for i in prefix[0].tolist()))

if __name__ == "__main__":
    run("starter" not in sys.argv)
