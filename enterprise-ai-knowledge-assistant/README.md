# Enterprise AI Knowledge Assistant

Ask questions about a PDF and get answers grounded in that document, with page references to help you check the source.

This guide is written for someone setting up the project for the first time on Windows. You do not need to know how AI works to try it.

## What does this project do?

Reading a long document to find one detail can take time. This app lets you upload a PDF and ask questions in plain language, such as:

> What does the document say about the cancellation policy?

The app uses **Retrieval-Augmented Generation (RAG)**. In everyday terms, it first searches your document for passages related to your question, then gives those passages to an AI model to write an answer. This helps keep the answer tied to the document instead of relying only on the model's general knowledge.

The main steps are:

1. **Upload:** The backend checks the PDF and extracts its text and page numbers.
2. **Prepare:** The text is split into smaller passages (called *chunks*).
3. **Index:** An embedding model turns each passage into a vector, a numerical representation used to find similar meaning. The vectors and passage text are saved in Qdrant.
4. **Ask:** Your question is converted to a vector. Qdrant finds up to five relevant passages from the selected document.
5. **Answer:** Groq's language model writes an answer using those passages. The response includes source page numbers when available.

If relevant text cannot be found, the assistant is instructed to say so rather than make up an answer. Still, always check important information against the cited PDF.

## What you need

- Windows 10 or 11 with Docker Desktop
- A Groq API key and a supported Groq model
- An internet connection to download images and the embedding model and to call Groq

## Run with Docker Compose

From the repository folder, open PowerShell and enter:

```powershell
cd .\enterprise-ai-knowledge-assistant
```

Create `.env` from the example if needed, then set `GROQ_API_KEY` to your own key:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Keep `.env` private and do not commit it. The model used by the app is `openai/gpt-oss-120b`. The backend container uses the internal Qdrant address `http://qdrant:6333`; from Windows, Qdrant is available at `http://localhost:6337`.

Build and start the app and monitoring services:

```powershell
docker compose up -d --build
docker compose ps
```

Open the app and service endpoints:

| Service | Address |
| --- | --- |
| Streamlit UI | [http://localhost:8502](http://localhost:8502) |
| FastAPI docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| FastAPI health | [http://localhost:8000/health](http://localhost:8000/health) |
| Qdrant REST API | [http://localhost:6337](http://localhost:6337) |
| Prometheus | [http://localhost:9091](http://localhost:9091) |

Compose maps host ports `8502`, `8000`, `6337`, and `9091` to container ports `8501`, `8000`, `6333`, and `9090`. Within the Compose network, the frontend talks to `http://backend:8000`, the backend talks to `http://qdrant:6333`, and Prometheus scrapes `http://backend:8000/metrics`.

The relevant environment settings are:

| Variable | Value or use |
| --- | --- |
| `GROQ_API_KEY` | Required; read from `.env`. Never put the key in a manifest or commit it. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` |
| `QDRANT_URL` | Host default: `http://localhost:6337`; Compose and Kubernetes use the internal `qdrant:6333` service address. |
| `QDRANT_COLLECTION` | `enterprise_documents` |
| `API_BASE_URL` | Compose sets `http://backend:8000`; Kubernetes sets `http://backend-service:8000`. The local frontend default is `http://127.0.0.1:8000`. |

Choose a PDF in the app and select **Upload and Start Chat**. After processing finishes, ask a question and expand **View Sources** to see source page numbers. Uploads are limited to one PDF at a time, up to 10 MB; scanned image-only PDFs are not OCR-processed.

Stop the services with:

```powershell
docker compose down
```

The named Qdrant and model-cache volumes are retained. `docker compose down -v` removes those volumes and their data.

## Using the API directly

The web app is the simplest way to try the project. You can also use the interactive API page at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs):

- `POST /documents/upload-and-index` uploads, extracts, and indexes a PDF. Its response contains a `document_id`.
- `POST /chat/query` answers a question for that document. Send a JSON body like:

```json
{
  "document_id": "the-id-returned-by-upload",
  "question": "What does the document say about the cancellation policy?"
}
```

The chat response includes the question, document ID, answer, and a `sources` list with page numbers and retrieval scores. A score indicates how closely a passage matched the question; it is not a guarantee that the answer is correct. Questions must be between 1 and 2,000 characters.

## Project map

| Path | What it is for |
| --- | --- |
| `backend/app/main.py` | Creates the FastAPI application and registers API routes. |
| `backend/app/api/documents.py` | Validates PDF uploads and runs the upload-and-index workflow. |
| `backend/app/api/chat.py` | Defines the chat endpoint and validates questions. |
| `backend/app/services/pdf_service.py` | Extracts text and page numbers from PDFs. |
| `backend/app/services/document_chunking.py` | Splits extracted document text into passages. |
| `backend/app/services/embedding_service.py` | Converts passages and questions into vectors. |
| `backend/app/services/qdrant_service.py` | Stores and searches document passages in Qdrant. |
| `backend/app/services/indexing_service.py` | Connects chunking, embeddings, and Qdrant storage. |
| `backend/app/services/rag_service.py` | Retrieves passages and builds the document-grounded answer. |
| `frontend/ui_app.py` | Provides the Streamlit upload and chat interface. |
| `storage/uploads/` | Holds uploaded PDF files. |
| `storage/processed/` | Holds extracted document text and intermediate chunk data. |

## Kubernetes on Minikube

The app's Kubernetes resources use the `default` namespace. Qdrant is exposed inside the cluster as `qdrant:6333`; the backend and frontend use `backend-service:8000` and `frontend-service:8501`.

Before deploying, ensure the `app-secrets` Secret exists in `default` with a `GROQ_API_KEY` entry. The key must not be added to a manifest or committed. For a local Minikube deployment, build and load the Docker images:

```powershell
docker compose build backend frontend
docker tag enterprise-ai-knowledge-assistant-backend:latest ghcr.io/uditkumar08/final_assessment_gen-backend:latest
docker tag enterprise-ai-knowledge-assistant-frontend:latest ghcr.io/uditkumar08/final_assessment_gen-frontend:latest
minikube image load ghcr.io/uditkumar08/final_assessment_gen-backend:latest
minikube image load ghcr.io/uditkumar08/final_assessment_gen-frontend:latest
```

Apply the app and Grafana resources, then wait for the rollouts:

```powershell
kubectl apply -f k8s/qdrant.yaml -f k8s/backend.yaml -f k8s/frontend.yaml -f k8s/grafana-dashboard.yaml -f k8s/grafana-datasource.yaml
kubectl apply -f k8s/servicemonitor.yaml
kubectl rollout status deployment/qdrant --namespace default --timeout=180s
kubectl rollout status deployment/backend --namespace default --timeout=300s
kubectl rollout status deployment/frontend --namespace default --timeout=180s
```

The CI workflow builds and publishes the same GHCR image names on pushes to `main`, deploys the manifests on the self-hosted runner, and skips the ServiceMonitor only when its CRD is not installed.

Forward the app and dashboards from separate PowerShell windows:

```powershell
kubectl port-forward --namespace default svc/frontend-service 8501:8501
kubectl port-forward --namespace monitoring svc/monitoring-grafana 3001:80
kubectl port-forward --namespace monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open the app at [http://localhost:8501](http://localhost:8501) and Grafana at [http://localhost:3001](http://localhost:3001). Grafana discovers the **Enterprise AI Knowledge Assistant** dashboard from its labeled ConfigMap. It includes backend request rate, p95 latency, status codes, health, and Loki logs. Grafana's preinstalled Kubernetes dashboards remain available as well.

For Prometheus, Grafana, Loki, dashboards, and queries, see [monitoring/README.md](./monitoring/README.md).

## Troubleshooting

- **The chat page cannot connect to the backend:** Run `docker compose ps` and `docker compose logs backend frontend`. In Compose, the frontend uses `http://backend:8000`; in Kubernetes it uses `http://backend-service:8000`.
- **Qdrant connection errors:** From Windows, Compose exposes Qdrant at `http://localhost:6337`. Containers and Kubernetes pods use the service address `http://qdrant:6333`.
- **Missing Groq settings:** Check that `.env` contains a real `GROQ_API_KEY` and the expected `GROQ_MODEL`; restart the backend with `docker compose restart backend`.
- **No readable PDF text:** The current PDF extraction supports text-based PDFs, not OCR for scanned pages.
- **An answer says it could not find information:** Try asking with terms used in the document, or confirm that the uploaded PDF contains the answer.
- **Kubernetes pods are not ready:** Check them with `kubectl get pods --namespace default`, then inspect a failing pod with `kubectl describe pod <pod-name> --namespace default` and `kubectl logs <pod-name> --namespace default`.
