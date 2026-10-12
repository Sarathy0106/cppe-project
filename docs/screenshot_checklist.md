# CampusVoice: Project Evaluation Screenshot Checklist

> **Purpose:** Numbered guide of all required screenshots for final Wipro CPPE report submission and evaluation presentation.

---

| # | Screenshot Item | AWS Console / Local UI Location | Key Evidence to Highlight | Status |
|---|---|---|---|:---:|
| **1** | **CloudFormation Stack** | CloudFormation -> Stacks -> `campusvoice-dev` | Stack status `UPDATE_COMPLETE`, description, and Outputs tab showing all exported ARNs. | Ready |
| **2** | **S3 Buckets & Public Access Block** | Amazon S3 -> Buckets list | 4 buckets (`raw`, `processed`, `logs`, `frontend`) showing "Bucket and objects not public". | Ready |
| **3** | **S3 Encryption & Versioning** | S3 -> `campusvoice-processed-*` -> Properties | Server-side encryption showing `SSE-KMS` with CMK `alias/campusvoice-data`, Bucket Versioning `Enabled`. | Ready |
| **4** | **KMS Cryptographic Keys** | KMS -> Customer managed keys | Symmetric key `alias/campusvoice-data` (rotation Enabled) and Asymmetric key `alias/campusvoice-sign` (RSA_2048). | Ready |
| **5** | **Step Functions Pipeline Execution** | Step Functions -> `campusvoice-pipeline-dev` | Execution graph in green state (`SUCCEEDED`) with all 5 task states completed. | Ready |
| **6** | **Curated Parquet Partitions in S3** | S3 -> `campusvoice-processed-*` -> `curated/` | Monthly partitions (`month=2026-04/` through `month=2026-09/`) containing `.snappy.parquet` files. | Ready |
| **7** | **Machine Learning Metrics** | Local editor / S3 -> `models/metrics.json` | Comparison table showing Logistic Regression (91.7% accuracy) vs Naive Bayes (86.7% accuracy). | Ready |
| **8** | **Amazon Athena Query Results** | Athena Query Editor -> `campusvoice-analytics-dev` | Query execution showing scan size (< 20 KB), execution time (< 2s), and curated feedback tabular results. | Ready |
| **9** | **Cognito User Pool & Groups** | Cognito -> `campusvoice-users-dev` | Users tab showing seed users and Groups tab showing `Admin` and `Viewer` groups with precedence. | Ready |
| **10** | **API Gateway Routes & Auth** | API Gateway -> `campusvoice-api-dev` | Routes tree (`/upload-url`, `/pipeline-status`, `/stats`, `/feedback`, `/chat`, `/agent`) with Cognito JWT Authorizer. | Ready |
| **11** | **UI: Login View with Role Selectors** | Browser (`http://localhost:5173/login`) | Clean login card showing quick demo buttons for Admin and Viewer roles. | Captured |
| **12** | **UI: Executive Dashboard & Charts** | Browser (`http://localhost:5173/`) | 4 KPI metric cards and all 3 Chart.js graphs (stacked bar, doughnut, monthly line chart). | Captured |
| **13** | **UI: Admin Ingestion & Live Stepper** | Browser (`http://localhost:5173/upload`) | Drag-and-drop CSV uploader with S3 progress bar and live 5-step `PipelineStepper`. | Ready |
| **14** | **UI: Curated Feedback Explorer** | Browser (`http://localhost:5173/explorer`) | Table with department/category/sentiment filters, pagination controls, and "Zero PII" privacy badge. | Captured |
| **15** | **UI: GenAI RAG Q&A Assistant** | Browser (`http://localhost:5173/ask` -> RAG) | Assistant response citing `[1]`, `[2]` with clickable source chips and excerpt inspection card. | Ready |
| **16** | **UI: Autonomous ReAct AI Agent** | Browser (`http://localhost:5173/ask` -> Agent) | Agent answer with collapsible "Agent Reasoning Trail" showing multi-step tool calls. | Ready |
| **17** | **UI: Security Controls Matrix** | Browser (`http://localhost:5173/security`) | Clean compliance matrix showcasing all 10 Module 4 security controls with status badges. | Captured |
| **18** | **CloudTrail Threat Detection Events** | CloudTrail -> Event history / CloudWatch Logs | Log stream `/aws/cloudtrail/campusvoice-dev` showing `AccessDenied` events from simulation script. | Ready |
| **19** | **CloudWatch Security Alarm & SNS** | CloudWatch -> Alarms -> `campusvoice-access-denied-dev` | Alarm graph showing metric breach ($\ge 3$), status in `ALARM`, and SNS notification delivery. | Ready |
| **20** | **CloudWatch Operations Dashboard** | CloudWatch -> Dashboards -> `campusvoice-ops-dev` | Full 4-widget dashboard showing security events, pipeline runs, Lambda errors, and API traffic. | Ready |
| **21** | **VPC Network & S3 Endpoint** | VPC -> Endpoints & Subnets | VPC `10.0.0.0/16`, private subnets, and free S3 Gateway Endpoint (`vpce-*`) attached to route tables. | Ready |
| **22** | **GitHub Actions CI/CD Pipeline** | GitHub -> Actions -> `CampusVoice CI/CD Pipeline` | Green workflow run showing `backend-checks`, `frontend-checks`, and `deploy` jobs passing. | Ready |
| **23** | **AWS Budget & Cost Verification** | AWS Budgets Console -> `campusvoice-budget-dev` | $10.00 monthly budget showing $0.00 actual spend and HEALTHY status. | Ready |
