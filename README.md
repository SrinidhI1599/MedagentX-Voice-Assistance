# 🩺 MedAgentX: AI Medical Intake & Triage Assistant

MedAgentX is a symptom-intake assistant that collects a patient's details (by form or by voice), checks for emergency red flags, retrieves relevant passages from a curated medical knowledge base using RAG, and returns a structured, evidence-backed assessment with a risk level and a downloadable PDF summary.

> ⚠️ **Disclaimer:** This is an educational project and **not a medical device**. It does not diagnose conditions and must not be used for real medical decisions. Always consult a qualified healthcare professional. In an emergency, call your local emergency number.

<!-- Add a screenshot or GIF here, e.g. ![Demo](docs/demo.gif) -->

## ✨ Features

- **Two intake modes:** a Streamlit form, or a conversational **voice assistant** that asks one question at a time (speech-to-text in, text-to-speech out).
- **Safety Gate 1 (red flags):** immediately returns an urgent response for chest pain, severe breathing difficulty, loss of consciousness, severe bleeding, anaphylaxis, stroke signs, severe abdominal pain, and poisoning/overdose.
- **Local RAG assessment:** retrieves the most relevant passages from a FAISS index built from public health sources. No external LLM or API key is required.
- **Deterministic risk engine:** transparent, rule-based `LOW / MODERATE / HIGH` classification with a matching urgency (`routine / priority / urgent`).
- **Safety Gate 2 (output check):** blocks responses that sound like a diagnosis, lack a disclaimer, or contradict the computed risk level.
- **Evidence and citations:** every result includes the source passages and similarity scores behind it.
- **PDF report:** download a summary of the assessment; the session resets afterwards so the next patient starts clean.

## 🏗️ Architecture

```
Streamlit UI (form / voice)
        │  POST /intake
        ▼
FastAPI backend
  ├─ Safety Gate 1 ── red flag? ──► URGENT response (stops here)
  ├─ Local assessment (RAG)
  │     query ─► MiniLM embeddings ─► FAISS search ─► top-k passages
  │             └► grouped into possible conditions + confidence
  ├─ Risk engine (severity + progression + duration)
  ├─ Assessment builder (adds disclaimer)
  └─ Safety Gate 2 ── validated assessment + risk
```

**How confidence works:** the top-k retrieved passages are grouped by source topic. The best cosine-similarity score per topic maps to a bucket: `High` (≥ 0.6), `Moderate` (≥ 0.4), or `Low`. These reflect how closely the reference text matches the symptoms, **not** a calibrated probability of disease.

**Risk rules**

| Risk | Rule |
|------|------|
| HIGH | Severe and worsening, or severe for 7+ days |
| MODERATE | Moderate and worsening, or moderate for 7+ days |
| LOW | Everything else |

## 📚 Knowledge Base

- **Topics:** Asthma, Cancer, Diabetes (Type 1 and Type 2), and Heart Disease (arrhythmias, cardiomyopathy, congenital heart disease, coronary artery disease).
- **Sources:** public health and clinical reference material such as NIH, CDC, WHO, Mayo Clinic, and Cleveland Clinic.
- **Processing:** cleaned, split into ~800-character chunks with 150 overlap, embedded with `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions), and stored in a FAISS `IndexFlatIP` index (~1,450 chunks).

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Backend | FastAPI, Uvicorn, Pydantic |
| Retrieval | sentence-transformers, FAISS, NumPy |
| Frontend | Streamlit, httpx |
| Voice | streamlit-mic-recorder, SpeechRecognition, gTTS, pydub, rapidfuzz |
| Reports | fpdf2 |

## 📁 Project Structure

```
AI_Medical_diagnosis/
├── app/
│   ├── assessment/          # local RAG assessment + assessment builder
│   └── rag/                 # clean, chunk, embed, ingest, retrieve, vector store
├── backend/
│   ├── main.py              # FastAPI app (POST /intake)
│   ├── schemas.py           # PatientIntake validation
│   ├── risk/                # deterministic risk engine
│   └── safety/              # red flags, Safety Gate 1 & 2
├── frontend/
│   ├── streamlit_app.py     # UI entry point
│   ├── voice_assistant.py   # voice intake
│   ├── pdf_report.py        # PDF export
│   └── constants.py         # symptom list
├── knowledge_base/
│   ├── raw/                 # source .txt files by topic
│   └── vector_store/        # index.faiss + metadata.json
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) on your PATH (needed by `pydub` for voice input)

### Installation

```bash
git clone https://github.com/<your-username>/AI_Medical_diagnosis.git
cd AI_Medical_diagnosis

python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install fastapi uvicorn pydantic httpx streamlit numpy \
            sentence-transformers faiss-cpu
pip install -r requirements.txt
```

### Build the knowledge base (optional)

A prebuilt index is included in `knowledge_base/vector_store/`. To rebuild it from the raw sources:

```bash
python -m app.rag.ingest
# or specific topics
python -m app.rag.ingest --source Diabetes --source Heart_Disease
```

### Run the app

Start the backend from the project root:

```bash
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
streamlit run streamlit_app.py
```

- API docs: http://127.0.0.1:8000/docs
- UI: http://localhost:8501

## 📡 API

### `POST /intake`

**Request**

```json
{
  "age": 45,
  "sex": "Male",
  "symptoms": ["Fatigue", "Increased thirst", "Frequent urination"],
  "duration_days": 10,
  "severity": "Moderate",
  "progression": "Worsening",
  "consent": true
}
```

`severity` must be `Mild`, `Moderate`, or `Severe`; `progression` is `Improving`, `Stable`, or `Worsening`; `consent` must be `true`.

**Response (normal case)**

```json
{
  "safe": true,
  "assessment": {
    "patient_summary": "45-year-old male reporting ...",
    "possible_conditions": [
      {"condition": "Diabetes", "confidence": "High", "match_score": 0.64}
    ],
    "evidence": [{"title": "...", "source_file": "...", "score": 0.64, "excerpt": "..."}],
    "risk_level": "MODERATE",
    "urgency": "priority",
    "disclaimer": "This tool does not provide medical diagnoses ..."
  },
  "risk": {"risk_level": "MODERATE", "urgency": "priority"}
}
```

**Response (red flag detected)**

```json
{
  "status": "URGENT",
  "flag": "CHEST_PAIN",
  "severity": "CRITICAL",
  "action": "CALL_EMERGENCY",
  "message": "Patient reports chest pain - requires immediate emergency evaluation",
  "safe_to_continue": false
}
```

## ⚠️ Limitations

- Retrieval matches symptoms to reference text; it is **not** a trained diagnostic model, and scores are not calibrated probabilities.
- Red-flag detection is keyword-based and can miss unusual phrasing.
- Coverage is limited to the topics in the knowledge base.
- Not clinically validated. For learning and demonstration only.

## 🔮 Future Improvements

- [ ] Add an LLM layer to write patient-friendly summaries from the retrieved evidence
- [ ] Evaluate retrieval quality with a labeled test set
- [ ] Expand the knowledge base to more conditions
- [ ] Add unit tests and CI
- [ ] Dockerize and deploy

## 🔒 Privacy

No real patient data is stored or included in this repository. Inputs are processed in memory and are not persisted by the backend.

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

## 👤 Author

**[Your Name]**
[LinkedIn](https://www.linkedin.com/in/sri-nidhi-bb6787197/) · [GitHub](https://github.com/SrinidhI1599)
