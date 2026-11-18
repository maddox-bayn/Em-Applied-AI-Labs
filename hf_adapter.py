"""Chapter 7. python hf_adapter.py OUT_DIR. Requires transformers, torch, peft, sentencepiece."""
import sys
from pathlib import Path
import torch
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

TRAIN = [("count invoices in bills", "SELECT COUNT(*) FROM bills"),
         ("list ids in bills", "SELECT id FROM bills"),
         ("count invoices in sales", "SELECT COUNT(*) FROM sales"),
         ("list ids in sales", "SELECT id FROM sales")]


def fit(out: Path) -> None:
    torch.manual_seed(7)
    base = "google/flan-t5-small"
    tok = AutoTokenizer.from_pretrained(base)
    model = get_peft_model(AutoModelForSeq2SeqLM.from_pretrained(base),
        LoraConfig(task_type=TaskType.SEQ_2_SEQ_LM, r=4, lora_alpha=8,
                   target_modules=["q","v"], lora_dropout=0.0))
    opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=0.002)
    x = tok([x for x,_ in TRAIN],return_tensors="pt",padding=True)
    labels = tok([y for _,y in TRAIN],return_tensors="pt",padding=True).input_ids
    labels[labels == tok.pad_token_id] = -100
    query = tok("count invoices in ledger",return_tensors="pt")
    def predict() -> str:
        model.eval()
        with torch.inference_mode():
            return tok.decode(model.generate(**query,max_new_tokens=24)[0], skip_special_tokens=True)
    print("before",predict())
    model.train()
    for _ in range(12):
        loss = model(**x,labels=labels).loss
        opt.zero_grad()
        loss.backward()
        opt.step()
    print("after",predict(), "expected SELECT COUNT(*) FROM ledger")
    model.save_pretrained(out)
    tok.save_pretrained(out)

if __name__ == "__main__":
    fit(Path(sys.argv[1]))
