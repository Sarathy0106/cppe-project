# CampusVoice: System Architecture & Technical Design

> **Project:** CampusVoice — Secure, Serverless AI & Big-Data Student Feedback Intelligence  
> **Course Program:** Wipro CPPE (Cloud Platform & Platform Engineering)  
> **Status:** Production Deployed & Verified  

---

## 1. End-to-End System Architecture

CampusVoice operates on a serverless lakehouse design on AWS, structured around the four Wipro CPPE core engineering modules:

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Presentation Layer (Vue 3 SPA)"]
        SPA["Vue 3 + Vite + TS SPA\nTailwind CSS & Chart.js"]
        AUTH_UI["Cognito SRP & JWT Auth\nRole: Admin / Viewer"]
    end

    subgraph SecurityAuth ["2. Edge & Security Perimeter"]
        CF["CloudFront CDN / S3\nHTTPS Only, OAC, Strict CSP"]
        APIGW["HTTP API Gateway\nJWT Authorizer & Rate Throttling"]
        COG["Amazon Cognito User Pool\nGroups: Admin, Viewer"]
    end

    subgraph IngestionCompute ["3. Microservices & Ingestion Engine"]
        UP_LAMBDA["api_upload_url Lambda\nAdmin Presigned S3 PUT URL"]
        START_LAMBDA["start_pipeline Lambda\nS3 Event Notification Trigger"]
        SFN["AWS Step Functions\ncampusvoice-pipeline-dev"]
    end

    subgraph PipelineTasks ["4. Serverless Processing Pipeline"]
        MASK_TASK["MaskPII Lambda\nComprehend PII Redaction & Lexicon Sentiment"]
        CLEAN_TASK["CleanFeedback Lambda / Glue\nTF-IDF + MLlib Logistic Regression Classifier"]
        CRAWL_TASK["StartCrawler Lambda\nGlue Data Catalog Partition Discovery"]
        EMBED_TASK["EmbedFeedback Lambda\nBedrock Titan Embeddings V2 (256-d)"]
        SIGN_TASK["SignManifest Lambda\nKMS RSA-2048 Digital Signature"]
    end

    subgraph LakehouseStorage ["5. Cryptographic Storage & Catalog"]
        S3_RAW[("campusvoice-raw\nAdmin Encrypted Uploads")]
        S3_PROC[("campusvoice-processed\nStaging, Curated Parquet, Vectors")]
        GLUE_CAT["Glue Data Catalog\ncampusvoice_db_dev.feedback"]
        KMS_DATA["KMS CMK (Symmetric)\nalias/campusvoice-data"]
        KMS_SIGN["KMS RSA Key (Asymmetric)\nalias/campusvoice-sign"]
    end

    subgraph QueryInference ["6. Analytics & GenAI Inference Engine"]
        ATHENA["Amazon Athena Workgroup\n100MB Scan Cutoff, KMS Results"]
        BEDROCK["Amazon Bedrock\nTitan Embeddings & Claude Haiku 4.5"]
        STATS_API["api_stats Lambda\nSub-50ms Cached Analytical KPIs"]
        FEEDBACK_API["api_feedback Lambda\nParameterized SQL Allow-List Queries"]
        CHAT_API["api_chat Lambda\nRAG Excerpt Search & Citation Grounding"]
        AGENT_API["api_agent Lambda\nAutonomous ReAct Tool-Loop Agent"]
    end

    SPA --> AUTH_UI
    AUTH_UI --> COG
    SPA --> CF
    SPA --> APIGW
    COG -.->|JWT Bearer Token| APIGW

    APIGW --> UP_LAMBDA
    UP_LAMBDA -->|Presigned URL| S3_RAW
    S3_RAW -->|s3:ObjectCreated| START_LAMBDA
    START_LAMBDA --> SFN

    SFN --> MASK_TASK
    MASK_TASK --> S3_PROC
    SFN --> CLEAN_TASK
    CLEAN_TASK --> S3_PROC
    SFN --> CRAWL_TASK
    CRAWL_TASK --> GLUE_CAT
    SFN --> EMBED_TASK
    EMBED_TASK --> BEDROCK
    EMBED_TASK --> S3_PROC
    SFN --> SIGN_TASK
    SIGN_TASK --> KMS_SIGN
    SIGN_TASK --> S3_PROC

    S3_RAW -.-> KMS_DATA
    S3_PROC -.-> KMS_DATA

    APIGW --> STATS_API
    APIGW --> FEEDBACK_API
    APIGW --> CHAT_API
    APIGW --> AGENT_API

    STATS_API --> ATHENA
    FEEDBACK_API --> ATHENA
    ATHENA --> GLUE_CAT
    ATHENA --> S3_PROC

    CHAT_API --> BEDROCK
    CHAT_API --> S3_PROC
    AGENT_API --> BEDROCK
    AGENT_API --> STATS_API
    AGENT_API --> CHAT_API
```

---

## 2. Step Functions Orchestration Pipeline

The automated batch ingestion workflow coordinates data validation, PII redaction, machine learning classification, catalog discovery, embedding generation, and cryptographic manifest signing:

```mermaid
stateDiagram-v2
    [*] --> UploadReceived: Admin uploads raw CSV to S3
    UploadReceived --> StartPipeline: s3:ObjectCreated:* triggers Lambda
    
    state "AWS Step Functions: campusvoice-pipeline-dev" as Pipeline {
        StartPipeline --> MaskPII: Extract rows & redact PII
        
        state MaskPII {
            [*] --> ComprehendDetect
            ComprehendDetect --> BackwardOffsetMask: Replace PII from end
            BackwardOffsetMask --> SentimentScoring: Compute sentiment & confidence
            SentimentScoring --> WriteStagingCSV: Save to processed/staging/
        }

        MaskPII --> CleanFeedback: Trigger ML classification
        
        state CleanFeedback {
            [*] --> LoadModelWeights: Fetch TF-IDF vectorizer & weights
            LoadModelWeights --> PredictCategories: Logistic Regression classification
            PredictCategories --> WritePartitionedParquet: Write to curated/month=YYYY-MM/
        }

        CleanFeedback --> StartCrawler: Discover partitions
        
        state StartCrawler {
            [*] --> SyncGlueCatalog: Run crawler / sync partition schema
            SyncGlueCatalog --> WaitCatalogReady: Poll until table ready
        }

        StartCrawler --> EmbedFeedback: Vectorize text
        
        state EmbedFeedback {
            [*] --> ReadMaskedExcerpts: Fetch batch records
            ReadMaskedExcerpts --> CallTitanEmbeddings: Titan V2 256-d unit vectors
            CallTitanEmbeddings --> WriteVectorStore: Save vectors/<batch_id>.json
        }

        EmbedFeedback --> SignManifest: Cryptographic audit
        
        state SignManifest {
            [*] --> GenerateBatchDigest: SHA-256 hash of batch contents
            GenerateBatchDigest --> KMSRSASign: Asymmetric RSA_2048 signing
            KMSRSASign --> SaveSignature: Write manifests/<batch_id>.sig
        }

        SignManifest --> ExecutionSuccess
    }

    ExecutionSuccess --> [*]: Pipeline finished green
    MaskPII --> PipelineFailed: Catch error
    CleanFeedback --> PipelineFailed: Catch error
    StartCrawler --> PipelineFailed: Catch error
    EmbedFeedback --> PipelineFailed: Catch error
    SignManifest --> PipelineFailed: Catch error
    PipelineFailed --> [*]: Trigger SNS Security/Ops Alert
```

---

## 3. Defense-in-Depth Security Architecture

CampusVoice enforces multiple independent concentric security perimeters spanning identity, networking, compute, storage, cryptography, and application security:

```mermaid
flowchart TD
    subgraph Layer1 ["Layer 1: Identity & Access Management (IAM & Cognito)"]
        L1_A["Cognito User Pool with Self-Signup Disabled"]
        L1_B["Strict Password Policy (Min 10, Mixed Case, Digits)"]
        L1_C["Role-Based Access Control (RBAC): Admin vs. Viewer"]
        L1_D["Dedicated Least-Privilege IAM Roles per Lambda"]
        L1_E["GitHub Actions OIDC Trust (Zero Long-Lived Keys)"]
    end

    subgraph Layer2 ["Layer 2: Network Perimeter & VPC Isolation"]
        L2_A["VPC 10.0.0.0/16 with Isolated Private Subnets"]
        L2_B["Zero NAT Gateway (No Outbound Internet Egress)"]
        L2_C["AWS Gateway VPC Endpoint for S3 (Zero Cost Private Routing)"]
        L2_D["Default-Deny Security Groups & Glue Cluster SG"]
    end

    subgraph Layer3 ["Layer 3: Cryptography & Data Protection at Rest/Transit"]
        L3_A["AWS KMS Customer Managed Keys (CMKs) with Auto-Rotation"]
        L3_B["Compulsory SSE-KMS at Rest (DenyNonKmsPutObject Policy)"]
        L3_C["TLS 1.2+ Transport Enforcement (aws:SecureTransport = false)"]
        L3_D["S3 Public Access Block: 100% Enforced Across All 4 Buckets"]
        L3_E["RSA-2048 Asymmetric Digital Signatures on Batch Manifests"]
    end

    subgraph Layer4 ["Layer 4: Data Privacy & GenAI Safety"]
        L4_A["Amazon Comprehend Automated PII Masking (Names, Emails, Phones)"]
        L4_B["Student Direct Identifier Elimination (Data Minimization)"]
        L4_C["Bedrock XML Delimiter Wrapping (Prompt Injection Defense)"]
        L4_D["Strict Ground-Truth Citation Constraint ([1], [2] Only)"]
        L4_E["Automated Refusal on Out-of-Domain Inquiries"]
    end

    subgraph Layer5 ["Layer 5: Continuous Auditing & Threat Detection"]
        L5_A["AWS CloudTrail Global Management & S3 Data Events Logging"]
        L5_B["CloudWatch Logs Group with 7-Day KMS-Encrypted Retention"]
        L5_C["Metric Filter for UnauthorizedOperation & AccessDenied"]
        L5_D["Real-Time Security Alarm (>3 Denials in 5m -> SNS Alert)"]
        L5_E["CloudWatch Operational Dashboard (campusvoice-ops-dev)"]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Layer5
```

---

## 4. Data Flow & Cryptographic Encryption Checkpoints

All data moving through the lifecycle transitions through well-defined cryptographic state checkpoints:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin User
    participant Web as Vue 3 Client
    participant GW as API Gateway
    participant S3Raw as S3 Raw Bucket
    participant SFN as Step Functions
    participant S3Proc as S3 Processed Bucket
    participant KMS as AWS KMS
    participant Ath as Amazon Athena

    Admin->>Web: Selects raw student feedback CSV
    Web->>GW: POST /upload-url (Bearer JWT)
    GW-->>Web: Returns Presigned S3 PUT URL
    Web->>S3Raw: PUT /uploads/<batch>/feedback.csv (SSE-KMS via Data CMK)
    Note over S3Raw,KMS: Encrypted at rest: alias/campusvoice-data

    S3Raw->>SFN: s3:ObjectCreated triggers pipeline
    SFN->>SFN: Step 1: Comprehend masks PII entities
    SFN->>S3Proc: Writes staging/<batch>.csv (Encrypted via Data CMK)
    
    SFN->>SFN: Step 2: TF-IDF MLlib classification
    SFN->>S3Proc: Writes curated/month=YYYY-MM/*.parquet (Snappy + SSE-KMS)
    
    SFN->>SFN: Step 3: Bedrock Titan vectorization
    SFN->>S3Proc: Writes vectors/<batch>.json (256-d vectors, SSE-KMS)
    
    SFN->>KMS: Signs batch digest with alias/campusvoice-sign (RSA_2048)
    KMS-->>SFN: Returns cryptographic digital signature
    SFN->>S3Proc: Writes manifests/<batch>.json and .sig
    Note over S3Proc,KMS: Manifest integrity guaranteed by asymmetric cryptography

    actor Viewer as College Staff
    Viewer->>Web: Opens Dashboard / Explorer
    Web->>GW: GET /stats?type=kpis (Bearer JWT)
    GW->>Ath: Executes canned query (100MB scan limit)
    Ath->>S3Proc: Scans Parquet partition metadata
    Ath-->>Web: Returns aggregated JSON metrics (<50ms cached)
```
