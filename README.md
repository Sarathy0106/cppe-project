# CampusVoice: Secure Serverless AI & Big-Data Student Feedback Intelligence Platform

> **Wipro CPPE Mini Project (Capstone)**  
> **Course Modules Covered:**  
> 1. Cloud Product & Platform Engineering (Lambda, API Gateway, Step Functions, SAM IaC, GitHub Actions CI/CD, Vue 3 SPA)  
> 2. Data Engineering, Big Data & ML (Athena, Glue Catalog, Partitioned Parquet, MLlib Classifier, Redshift Star Schema)  
> 3. GenAI, Foundation Models & RAG (Bedrock Titan Embeddings V2, Claude Haiku 4.5, Vector RAG with Citations, ReAct AI Agent)  
> 4. Cloud Security, Cryptography & Governance (KMS CMK Symmetric & Asymmetric RSA Signatures, Cognito RBAC, S3 Hardening, VPC S3 Endpoint, CloudTrail Alarms)

---

## 1. System Overview

CampusVoice transforms sensitive, unstructured student feedback into masked, queryable, and AI-searchable institutional insights on AWS without incurring idle server costs:

- **Frontend:** Vue 3 (Composition API) + Vite + TypeScript + Pinia + Vue Router + Tailwind CSS + Chart.js.
- **API & Compute:** Amazon API Gateway (HTTP API) with Cognito JWT authorizer, AWS Lambda (Python 3.12).
- **Pipeline Orchestration:** AWS Step Functions state machine (`campusvoice-pipeline-dev`) coordinating PII redaction, ML classification, catalog discovery, vectorization, and manifest signing.
- **Data Lake:** Amazon S3 (Encrypted via KMS CMK, TLS-only, 100% Public Access Blocked, partitioned Parquet).
- **GenAI & Analytics:** Amazon Bedrock (Titan V2 256-d Embeddings + Claude Haiku 4.5), Amazon Athena (100 MB scan cutoff).
- **Security & Threat Detection:** AWS CloudTrail logging to CloudWatch Logs with metric filter and real-time SNS security alarm.

---

## 2. Seed Credentials for Evaluation

The platform includes two pre-configured evaluation accounts in Amazon Cognito:

| Role | Username / Email | Password | Access Scope |
|---|---|---|---|
| **Admin** | `admin@campusvoice.local` | `CampusVoice@2026!` | Full access: Upload CSV, trigger pipeline, view live stepper, dashboard, explorer, AI chat, agent, security matrix. |
| **Viewer** | `viewer@campusvoice.local` | `CampusVoice@2026!` | Read-only: Dashboard, explorer, AI chat, agent, and security matrix (blocked from upload). |

---

## 3. Five-Minute Evaluation & Demo Walkthrough

### Step 1: Launch Local Frontend
```powershell
cd frontend
npm run preview -- --port 5173
```
Open **`http://localhost:5173/`** in your browser.

### Step 2: Test Authentication & RBAC (Module 1 & 4)
1. On the login screen, click the **👑 Admin Role** quick-fill button, then click **Sign In via Cognito**.
2. Notice the navigation bar displaying your authenticated role badge (`Admin`) and email.
3. Sign out and sign in with the **👀 Viewer Role** button.
4. Verify that the **Data Pipeline** tab is automatically hidden from the navigation bar. Attempting to browse directly to `/upload` displays a friendly access-denied advisory notice.

### Step 3: Executive Analytics Dashboard (Module 2)
1. Sign back in as **Admin**.
2. Navigate to **Dashboard (`/`)**.
3. Inspect the 4 real-time KPI metric cards (Total Feedback, Positive %, Negative %, Departments).
4. Review the 3 interactive Chart.js visualizations:
   - **Stacked Bar Chart:** Sentiment breakdown by academic department.
   - **Doughnut Chart:** Feedback distribution across categories (Hostel, Canteen, Faculty, Labs, Infrastructure).
   - **Monthly Line Chart:** Long-term complaint trends across partitions.

### Step 4: Curated Feedback Explorer & PII Redaction (Module 2 & 4)
1. Click **Feedback Explorer (`/explorer`)**.
2. Filter feedback by Department (`CSE`), Category (`HOSTEL`), or Sentiment (`NEGATIVE`).
3. Notice that all student names, emails, and phone numbers are completely redacted with `[NAME]`, `[EMAIL]`, `[PHONE]` badges while the original student voices remain actionable.
4. Test pagination controls (`Previous` / `Next`).

### Step 5: GenAI RAG Q&A & ReAct Autonomous Agent (Module 3)
1. Click **Ask AI & Agent (`/ask`)**.
2. In **📖 RAG Q&A mode**, click the suggested question: *"What are the main hostel complaints?"*
   - Observe the synthesized answer citing specific excerpt numbers `[1]`, `[2]`.
   - Inspect the interactive source chips showing department, category, sentiment, and cosine similarity percentage. Click any chip to inspect the underlying excerpt modal.
3. Toggle to **🧠 ReAct Agent mode**.
4. Ask: *"Which department has the most negative feedback and why?"*
   - Observe the agent autonomously invoke tools (`run_stats_query`, `search_feedback`) and expand the collapsible **Agent Reasoning Trail** to review each intermediate step.
5. Test an out-of-domain question: *"What is the capital of France?"*
   - Observe the verified refusal response without hallucination.

### Step 6: Trigger Security Alarm & Threat Detection (Module 4)
1. In your terminal, run the threat simulation script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\simulate_suspicious_activity.ps1
   ```
2. The script executes 5 unauthorized API operations.
3. Within 1–3 minutes, CloudTrail detects the events, the metric filter increments `AccessDeniedCount`, and the CloudWatch Alarm **`campusvoice-access-denied-dev`** trips into `ALARM`, dispatching an alert email to `sarathy01062005@gmail.com`.
4. Navigate to **Security Controls (`/security`)** in the web UI to review the compliance evidence matrix.

---

## 4. Automated Testing & CI/CD

### Run Local Unit Tests
```bash
python -m pytest tests/test_backend.py -v
```
Verifies 7 unit tests covering PII backward offset masking, SQL injection allow-list validation, and pure-Python vector cosine similarity in < 0.1s.

### GitHub Actions CI/CD
The repository includes `.github/workflows/ci.yml` which automatically:
- Runs Python 3.12 linting and pytest unit tests.
- Runs Node 20 TypeScript and Vue 3 frontend compilation.
- Deploys infrastructure and syncs frontend to S3 on push to `main` using **GitHub OpenID Connect (OIDC)** (zero long-lived AWS keys).

---

## 5. Teardown Instructions

To completely clean up all provisioned AWS resources and prevent any ongoing charges:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\teardown.ps1
```
Or on Linux/macOS:
```bash
./scripts/teardown.sh
```
The teardown script automatically empties all versioned S3 buckets, deletes the CloudFormation stack, and schedules KMS CMK deletion.
