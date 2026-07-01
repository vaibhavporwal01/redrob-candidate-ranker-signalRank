# Three-minute demo script

## 0:00–0:25 — Frame the failure mode

“Most ranking systems embed the JD, embed the résumé, and reward whoever repeats the most AI vocabulary. Redrob’s brief explicitly says that misses the person they want: a backend engineer who shipped recommendation or retrieval but never wrote ‘RAG’ on their profile.”

Point to the headline: **Find the engineer behind the keywords.**

## 0:25–1:05 — Show the hidden gem

Open `RR-1842`, the Senior Backend Engineer. Call out:

- scaled FAISS search serving 14M monthly users;
- production latency evidence;
- a strong hidden-gem bar despite a non-ML title; and
- career evidence outweighing the explicit skills list.

Then open `RR-7714`, whose skills list does not contain embeddings even though the career record says they shipped embedding-based API-documentation search.

## 1:05–1:45 — Prove the gates bite

Filter **Risk → Flagged profiles**.

- `RR-8890` has perfect buzzwords and response rate, but an impossible reversed timeline and expert skills with zero duration.
- `RR-6002` has the AI title, but a career entirely at named consultancies and only recent wrapper work.
- `RR-4021` is accomplished but research-only computer vision, not production NLP/IR.

Say: “These are multiplicative gates, not cosmetic deductions. A do-not-hire condition cannot be allowed back into the top 100 through keyword volume.”

## 1:45–2:20 — Show practical hiring intelligence

Open `RR-1580`: technically relevant, but inactive for months with an 8% response rate. The availability bar makes clear why the candidate is lower despite credible ML platform work.

Call out location and notice-period fit as a joint signal, matching the brief’s “30+ days remains in scope, but the bar gets higher” language.

## 2:20–2:50 — Defend engineering choices

Open **Method** and quickly walk the four stages: retrieve, verify, gate, rank. Mention:

- one shared package powers CLI, API, and evaluation;
- no hosted model, network, or GPU in `rank.py`;
- all values are in config;
- deterministic explanations quote actual career evidence; and
- the validator and tests run in one command.

## 2:50–3:00 — Close

“Signalrank is not trying to automate judgment. It makes judgment faster, consistent, and auditable—while finding the shippers a keyword baseline leaves behind.”

