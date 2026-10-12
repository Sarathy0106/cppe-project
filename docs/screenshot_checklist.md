# CampusVoice: Report Screenshot Mapping & Placement Guide

> **Aligned Directly with:** `CPPE Mini project 2 report_template.docx`  
> **Institution:** Sri Manakula Vinayagar Engineering College (Autonomous), Madagadipet, Puducherry  
> **Department:** Department of Computer Science and Engineering  
> **Degree:** Bachelor of Technology in CSE, Pondicherry University  

---

## Structure Overview & Screenshot Distribution

In the official `CPPE Mini project 2 report_template.docx`, each technical chapter has a dedicated **`4.x.2 SCREENSHOTS FOR [MODULE]`** subsection and a **`4.x.3 ACTIVITY DIAGRAM`** subsection. Below is the exact mapping of figure numbers, captions, AWS console/UI locations, and key evidence criteria to insert under each section:

---

## CHAPTER 3: ARCHITECTURE DIAGRAM

* **Figure 3.1: End-to-End Serverless Lakehouse Architecture Diagram**  
  * **Placement:** Under Chapter 3, after the introductory architecture narrative.  
  * **Source:** Diagram generated from [docs/architecture.md](file:///c:/Users/toura/Developer/Projects/cppe-project/docs/architecture.md) (Client SPA, API Gateway, Step Functions, S3 Data Lake, Athena, Bedrock, and Security Perimeter).  
  * **Caption:** *Figure 3.1: CampusVoice End-to-End Serverless AI & Big-Data Architecture on AWS.*

---

## CHAPTER 4.1: MODULE 1 — DATA ENGINEERING

### 4.1.2 SCREENSHOTS FOR DATA ENGINEERING
Place the following figures with captions in subsection `4.1.2`:

1. **Figure 4.1.1: S3 Curated Data Lake with Monthly Partitions**  
   - **Console Location:** Amazon S3 -> Buckets -> `campusvoice-processed-657878533694-dev` -> `curated/`  
   - **Key Evidence:** Folders `month=2026-04/` through `month=2026-09/` containing Snappy-compressed `.parquet` files.  
   - **Caption:** *Figure 4.1.1: Curated feedback Parquet data lake organized by monthly partition keys in Amazon S3.*

2. **Figure 4.1.2: Machine Learning Classification Model Evaluation (metrics.json)**  
   - **Console / Editor Location:** S3 -> `models/metrics.json` or local code editor showing `metrics.json`.  
   - **Key Evidence:** Comparison table showing Logistic Regression (Accuracy: 91.7%, F1: 0.916) vs. Naive Bayes (Accuracy: 86.7%, F1: 0.866), confusion matrix, and 480/120 split.  
   - **Caption:** *Figure 4.1.2: Machine learning classification evaluation metrics comparing TF-IDF Logistic Regression and Naive Bayes.*

3. **Figure 4.1.3: Amazon Athena Query Execution & Results**  
   - **Console Location:** Amazon Athena -> Query Editor (Workgroup: `campusvoice-analytics-dev`).  
   - **Key Evidence:** Query execution on table `campusvoice_db_dev.feedback`, runtime (< 2s), data scanned (< 20 KB), and tabular sentiment output.  
   - **Caption:** *Figure 4.1.3: Interactive Athena SQL query execution demonstrating partition pruning and sub-20 KB scan performance.*

4. **Figure 4.1.4: AWS Glue Data Catalog Schema & Partition Discovery**  
   - **Console Location:** AWS Glue -> Databases -> `campusvoice_db_dev` -> Tables -> `feedback`.  
   - **Key Evidence:** Table type `EXTERNAL_TABLE`, classification `parquet`, column schemas, and partition key `month`.  
   - **Caption:** *Figure 4.1.4: AWS Glue Data Catalog table definition for curated Parquet student feedback.*

### 4.1.3 ACTIVITY DIAGRAM
- **Figure 4.1.5: Data Engineering ETL & Partitioning Activity Diagram**  
  - **Source:** Mermaid Activity flow from [docs/architecture.md](file:///c:/Users/toura/Developer/Projects/cppe-project/docs/architecture.md#2-step-functions-orchestration-pipeline) (CSV Validation -> PII Offset Redaction -> TF-IDF Logistic Regression -> Parquet Snappy Compression -> Catalog Sync).

---

## CHAPTER 4.2: MODULE 2 — CLOUD ENGINEERING

### 4.2.2 SCREENSHOTS FOR CLOUD ENGINEERING
Place the following figures with captions in subsection `4.2.2`:

1. **Figure 4.2.1: AWS CloudFormation Stack Outputs & Deployed Resources**  
   - **Console Location:** CloudFormation -> Stacks -> `campusvoice-dev` -> Outputs tab.  
   - **Key Evidence:** Stack status `UPDATE_COMPLETE`, exported ARNs for KMS keys, S3 buckets, State Machine, and HTTP API endpoint URL.  
   - **Caption:** *Figure 4.2.1: AWS CloudFormation stack resources and exported infrastructure ARNs.*

2. **Figure 4.2.2: AWS Step Functions State Machine Execution Graph**  
   - **Console Location:** Step Functions -> State Machines -> `campusvoice-pipeline-dev` -> Execution `cv-*`.  
   - **Key Evidence:** Complete green execution path through `MaskPII`, `GlueClean`, `StartCrawler`, `EmbedFeedback`, and `SignManifest` with `SUCCEEDED` status.  
   - **Caption:** *Figure 4.2.2: End-to-end green execution status of the Step Functions serverless data pipeline.*

3. **Figure 4.2.3: Amazon API Gateway HTTP API Routes & JWT Authorizer**  
   - **Console Location:** Amazon API Gateway -> `campusvoice-api-dev` -> Routes tree.  
   - **Key Evidence:** Deployed routes (`/stats`, `/feedback`, `/chat`, `/agent`, `/upload-url`, `/pipeline-status`) protected by Cognito JWT DefaultAuthorizer.  
   - **Caption:** *Figure 4.2.3: API Gateway HTTP routes protected with Cognito JWT authorizer and rate throttling.*

4. **Figure 4.2.4: Vue 3 Executive Analytics Dashboard**  
   - **Local UI Location:** Browser at `http://localhost:5173/` (Dashboard view).  
   - **Key Evidence:** 4 KPI metric cards and all 3 Chart.js visualizations (sentiment by department, category distribution doughnut, and monthly trend line).  
   - **Caption:** *Figure 4.2.4: Executive feedback analytics dashboard with interactive Chart.js visualizations.*

5. **Figure 4.2.5: Admin Data Ingestion & Live Pipeline Stepper**  
   - **Local UI Location:** Browser at `http://localhost:5173/upload` (Upload view).  
   - **Key Evidence:** Drag-and-drop CSV uploader, S3 PUT progress bar, and live 5-step `PipelineStepper` component.  
   - **Caption:** *Figure 4.2.5: Admin CSV ingestion interface with real-time Step Functions execution stepper.*

6. **Figure 4.2.6: GitHub Actions Automated CI/CD Workflow Run**  
   - **GitHub Location:** GitHub Repository -> Actions tab -> `CampusVoice CI/CD Pipeline`.  
   - **Key Evidence:** Green workflow run showing `backend-checks` (pytest), `frontend-checks` (Vite build), and `deploy` (AWS OIDC).  
   - **Caption:** *Figure 4.2.6: Automated GitHub Actions CI/CD deployment pipeline authenticated via AWS OIDC.*

### 4.2.3 ACTIVITY DIAGRAM
- **Figure 4.2.7: Cloud Engineering Serverless Microservices Activity Diagram**  
  - **Source:** Client S3 Presigned URL Request -> S3 Event Notification -> Step Functions Invocation -> Lambda Execution -> State Polling.

---

## CHAPTER 4.3: MODULE 3 — AI ENGINEERING

### 4.3.2 SCREENSHOTS FOR AI ENGINEERING
Place the following figures with captions in subsection `4.3.2`:

1. **Figure 4.3.1: Amazon Bedrock Titan Text Embeddings Vector Store in S3**  
   - **Console Location:** S3 -> `campusvoice-processed-657878533694-dev` -> `vectors/` -> `<batch_id>.json`.  
   - **Key Evidence:** JSON structure containing feedback IDs and 256-dimensional normalized embedding vectors (`L2 norm = 1.0`).  
   - **Caption:** *Figure 4.3.1: Bedrock Titan Text Embeddings V2 256-dimensional vector store in Amazon S3.*

2. **Figure 4.3.2: GenAI RAG Conversational Interface with Grounded Source Citations**  
   - **Local UI Location:** Browser at `http://localhost:5173/ask` (RAG Q&A mode).  
   - **Key Evidence:** Assistant answer citing `[1]`, `[2]`, with interactive source chips displaying department, category, sentiment, and similarity percentage.  
   - **Caption:** *Figure 4.3.2: Retrieval-Augmented Generation (RAG) assistant providing grounded answers with bracketed citation chips.*

3. **Figure 4.3.3: Autonomous ReAct AI Agent with Multi-Step Reasoning Trail**  
   - **Local UI Location:** Browser at `http://localhost:5173/ask` (ReAct Agent mode).  
   - **Key Evidence:** Collapsible "Agent Reasoning Trail" revealing sequential tool invocations (`run_stats_query`, `search_feedback`) and intermediate observations.  
   - **Caption:** *Figure 4.3.3: ReAct autonomous agent interface displaying multi-step tool calls and intermediate reasoning observations.*

4. **Figure 4.3.4: GenAI Safety: Out-of-Domain Refusal & Prompt Injection Defense**  
   - **Local UI Location:** Browser at `http://localhost:5173/ask` showing test query: *"What is the capital of France?"*.  
   - **Key Evidence:** Deterministic refusal: *"I could not find information about this in the student feedback records."*  
   - **Caption:** *Figure 4.3.4: Verified model refusal on out-of-domain inquiries preventing hallucination.*

### 4.3.3 ACTIVITY DIAGRAM
- **Figure 4.3.5: Generative AI RAG Retrieval & ReAct Tool Loop Activity Diagram**  
  - **Source:** Query Ingestion -> Titan Vectorization -> Cosine Similarity Top-6 Filter -> System Prompt Wrapping -> Claude Haiku 4.5 Synthesis -> Citation Generation.

---

## CHAPTER 4.4: MODULE 4 — SECURITY ENGINEERING

### 4.4.2 SCREENSHOTS FOR SECURITY ENGINEERING
Place the following figures with captions in subsection `4.4.2`:

1. **Figure 4.4.1: AWS KMS Customer Managed Keys & Automated Key Rotation**  
   - **Console Location:** AWS KMS -> Customer managed keys -> `alias/campusvoice-data`.  
   - **Key Evidence:** Key status `Enabled`, Key spec `SYMMETRIC_DEFAULT`, and Key rotation `Enabled`.  
   - **Caption:** *Figure 4.4.1: AWS KMS symmetric Customer Managed Key (CMK) with annual rotation enabled.*

2. **Figure 4.4.2: Asymmetric RSA Key & Manifest Digital Signature Verification**  
   - **Console / Terminal Location:** Terminal output running `aws kms verify --key-id alias/campusvoice-sign ...`.  
   - **Key Evidence:** Terminal output showing `SignatureValid: true` for the batch manifest digest.  
   - **Caption:** *Figure 4.4.2: Terminal verification confirming cryptographic authenticity of the batch manifest signature via KMS.*

3. **Figure 4.4.3: S3 Storage Hardening: 100% Public Access Block & SSE-KMS**  
   - **Console Location:** Amazon S3 -> Buckets list.  
   - **Key Evidence:** All 4 buckets (`raw`, `processed`, `logs`, `frontend`) showing "Bucket and objects not public".  
   - **Caption:** *Figure 4.4.3: Amazon S3 storage hardening with public access block enforced across all project buckets.*

4. **Figure 4.4.4: CloudTrail Captured AccessDenied Events from Threat Simulation**  
   - **Console Location:** CloudWatch Logs -> Log Groups -> `/aws/cloudtrail/campusvoice-dev`.  
   - **Key Evidence:** Log events matching `AccessDenied` from the threat simulation script execution.  
   - **Caption:** *Figure 4.4.4: AWS CloudTrail audit log stream capturing simulated unauthorized API calls in CloudWatch Logs.*

5. **Figure 4.4.5: CloudWatch Security Alarm & Real-Time SNS Email Notification**  
   - **Console / Email Location:** CloudWatch -> Alarms -> `campusvoice-access-denied-dev` or Email inbox showing alert.  
   - **Key Evidence:** Alarm state `ALARM` with threshold breach ($\ge 3$ events) and email alert delivered to `sarathy01062005@gmail.com`.  
   - **Caption:** *Figure 4.4.5: Real-time CloudWatch security alarm notification dispatched via Amazon SNS.*

6. **Figure 4.4.6: CloudWatch Operations Dashboard (campusvoice-ops-dev)**  
   - **Console Location:** CloudWatch -> Dashboards -> `campusvoice-ops-dev`.  
   - **Key Evidence:** 4 operational widgets showing Access Denied security events, Step Functions runs, Lambda invocations/errors, and API traffic.  
   - **Caption:** *Figure 4.4.6: Unified CloudWatch operations and security threat monitoring dashboard.*

7. **Figure 4.4.7: VPC Network Baseline & S3 Gateway VPC Endpoint**  
   - **Console Location:** VPC Console -> Endpoints -> `vpce-07cc650cad7e11459`.  
   - **Key Evidence:** Endpoint type `Gateway`, service `com.amazonaws.us-east-1.s3`, attached to `campusvoice-vpc-dev` private route tables at $0.00 cost.  
   - **Caption:** *Figure 4.4.7: Zero-cost S3 Gateway VPC Endpoint providing isolated private data lake communication.*

8. **Figure 4.4.8: Vue 3 Security Controls & Compliance Matrix Page**  
   - **Local UI Location:** Browser at `http://localhost:5173/security`.  
   - **Key Evidence:** Web dashboard detailing all 12 implemented security controls with green verification badges.  
   - **Caption:** *Figure 4.4.8: Security controls and compliance verification matrix interface in the web application.*

### 4.4.3 ACTIVITY DIAGRAM
- **Figure 4.4.9: Security Threat Detection & Incident Response Activity Diagram**  
  - **Source:** CloudTrail Event Delivery -> Metric Filter Match -> Alarm Threshold Breach -> SNS Notification -> SOC Runbook 7-Phase Isolation.

---

## CHAPTER 5: CONCLUSION & COST SUMMARY

* **Figure 5.1: AWS Budgets & Month-to-Date Spend Verification**  
  * **Console Location:** AWS Budgets Console -> `campusvoice-budget-dev`.  
  * **Key Evidence:** $10.00 monthly budget limit showing **$0.00 actual spend** and `HEALTHY` status.  
  * **Caption:** *Figure 5.1: AWS Budgets financial report verifying zero active spend within the $10.00 project threshold.*
