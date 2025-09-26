# SmartReads Architecture Diagrams

## System Context Diagram
Shows how SmartReads fits into the school district ecosystem.

```mermaid
graph TB
    subgraph "School District Ecosystem"
        subgraph "Users"
            ST[Students]
            LB[Librarians]
            TC[Teachers]
            AD[Administrators]
        end
        
        subgraph "SmartReads System"
            SR[SmartReads Core]
            API[API Gateway]
            WEB[Web Interface]
            MOB[Mobile App]
        end
        
        subgraph "External Systems"
            LMS[Library Management System]
            SIS[Student Information System]
            CAT[Card Catalog]
        end
        
        subgraph "AI Services"
            LLM[LLM API<br/>GPT-4/Claude]
            EMB[Embedding Service]
        end
    end
    
    ST --> WEB
    ST --> MOB
    LB --> WEB
    TC --> WEB
    AD --> WEB
    
    WEB --> API
    MOB --> API
    API --> SR
    
    SR <--> LMS
    SR <--> SIS
    SR <--> CAT
    SR <--> LLM
    SR <--> EMB
```

## Data Flow Diagram
Illustrates how data moves through the system to generate recommendations.

```mermaid
graph LR
    subgraph "Input Layer"
        U[User Request]
        H[Historical Data]
        C[Catalog Data]
    end
    
    subgraph "Processing Pipeline"
        direction TB
        DP[Data Processor]
        FE[Feature Extractor]
        PE[Privacy Engine]
    end
    
    subgraph "ML Pipeline"
        direction TB
        CF[Collaborative<br/>Filtering]
        CB[Content-Based<br/>Filtering]
        LLM[LLM Analysis]
        EN[Ensemble<br/>Combiner]
    end
    
    subgraph "Output Layer"
        RR[Ranked<br/>Recommendations]
        EX[Explanations]
        AN[Analytics]
    end
    
    U --> DP
    H --> DP
    C --> DP
    DP --> FE
    FE --> PE
    PE --> CF
    PE --> CB
    PE --> LLM
    CF --> EN
    CB --> EN
    LLM --> EN
    EN --> RR
    EN --> EX
    EN --> AN
```

## Recommendation Engine Architecture
Detailed view of the recommendation engine's internal components.

```mermaid
graph TB
    subgraph "Request Handler"
        RQ[Incoming Request]
        CTX[Context Extractor]
        VAL[Request Validator]
    end
    
    subgraph "User Profile"
        UP[User Preferences]
        UH[Reading History]
        UD[Demographics]
    end
    
    subgraph "Recommendation Strategies"
        direction LR
        subgraph "Collaborative"
            UCF[User-Based CF]
            ICF[Item-Based CF]
            MF[Matrix Factorization]
        end
        
        subgraph "Content"
            TF[TF-IDF Matching]
            SE[Semantic Embeddings]
            GN[Genre Matching]
        end
        
        subgraph "Knowledge"
            KG[Knowledge Graph]
            RL[Reading Level]
            TH[Thematic Analysis]
        end
    end
    
    subgraph "LLM Enhancement"
        LP[LLM Prompt Builder]
        LC[LLM Client]
        LR[Response Parser]
    end
    
    subgraph "Post-Processing"
        RK[Ranker]
        DV[Diversity Filter]
        EG[Explanation Generator]
    end
    
    RQ --> CTX
    CTX --> VAL
    VAL --> UP
    UP --> UCF
    UP --> ICF
    UH --> MF
    UD --> GN
    
    UCF --> RK
    ICF --> RK
    MF --> RK
    TF --> RK
    SE --> RK
    GN --> RK
    
    UP --> LP
    RK --> LP
    LP --> LC
    LC --> LR
    LR --> EG
    
    RK --> DV
    DV --> EG
    EG --> |Final Output| O[Recommendations with Explanations]
```

## Infrastructure Architecture
Shows the deployment and infrastructure components.

```mermaid
graph TB
    subgraph "Client Layer"
        WB[Web Browser]
        MB[Mobile App]
    end
    
    subgraph "CDN/Load Balancer"
        CDN[CloudFront CDN]
        ALB[Application Load Balancer]
    end
    
    subgraph "Application Tier"
        subgraph "Kubernetes Cluster"
            API1[API Pod 1]
            API2[API Pod 2]
            API3[API Pod 3]
            WK1[Worker Pod 1]
            WK2[Worker Pod 2]
        end
    end
    
    subgraph "Data Tier"
        subgraph "Databases"
            PG[(PostgreSQL<br/>Primary)]
            PGR[(PostgreSQL<br/>Read Replica)]
            RD[(Redis Cache)]
            CH[(ChromaDB<br/>Vector Store)]
        end
    end
    
    subgraph "ML Services"
        ML[ML Model Server]
        GPU[GPU Instances]
    end
    
    subgraph "External Services"
        LLM[LLM API]
        S3[S3 Storage]
        LOG[CloudWatch Logs]
    end
    
    WB --> CDN
    MB --> CDN
    CDN --> ALB
    ALB --> API1
    ALB --> API2
    ALB --> API3
    
    API1 --> PG
    API2 --> PG
    API3 --> PG
    API1 --> RD
    API2 --> RD
    API3 --> RD
    
    API1 --> WK1
    API2 --> WK2
    
    WK1 --> ML
    WK2 --> ML
    ML --> GPU
    
    WK1 --> CH
    WK2 --> CH
    WK1 --> LLM
    WK2 --> LLM
    
    API1 --> S3
    WK1 --> LOG
```

## Security Architecture
Illustrates security measures and data protection.

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Network Security"
            FW[Web Application Firewall]
            IDS[Intrusion Detection]
            VPN[VPN Gateway]
        end
        
        subgraph "Application Security"
            AUTH[Authentication Service]
            AUTHZ[Authorization Service]
            AUDIT[Audit Logger]
        end
        
        subgraph "Data Security"
            ENC[Encryption at Rest]
            TLS[TLS/SSL]
            MASK[Data Masking]
            ANON[Anonymization Engine]
        end
        
        subgraph "Compliance"
            FERPA[FERPA Compliance]
            COPPA[COPPA Compliance]
            GDPR[GDPR Compliance]
        end
    end
    
    subgraph "Data Flow"
        U[User] --> FW
        FW --> AUTH
        AUTH --> AUTHZ
        AUTHZ --> |Authorized| APP[Application]
        APP --> ANON
        ANON --> DB[(Database)]
        DB --> ENC
        APP --> AUDIT
        AUDIT --> LOG[(Audit Logs)]
    end
    
    TLS -.->|Encrypts| FW
    TLS -.->|Encrypts| APP
    MASK -.->|Protects| DB
    
    FERPA --> ANON
    COPPA --> AUTHZ
    GDPR --> MASK
```

## Machine Learning Pipeline
Details the ML model training and deployment pipeline.

```mermaid
graph LR
    subgraph "Data Collection"
        H[Historical Data]
        C[Catalog Data]
        F[Feedback Data]
    end
    
    subgraph "Data Preparation"
        CL[Cleaning]
        TR[Transformation]
        FE[Feature Engineering]
        SP[Train/Test Split]
    end
    
    subgraph "Model Training"
        subgraph "Models"
            CF[Collaborative Filtering]
            CB[Content-Based]
            DL[Deep Learning]
        end
        HP[Hyperparameter Tuning]
        CV[Cross Validation]
    end
    
    subgraph "Model Evaluation"
        ME[Metrics Calculation]
        AB[A/B Testing]
        HE[Human Evaluation]
    end
    
    subgraph "Deployment"
        MR[Model Registry]
        MS[Model Server]
        MC[Model Cache]
    end
    
    subgraph "Monitoring"
        PM[Performance Monitor]
        DM[Drift Monitor]
        RT[Retraining Trigger]
    end
    
    H --> CL
    C --> CL
    F --> CL
    CL --> TR
    TR --> FE
    FE --> SP
    SP --> CF
    SP --> CB
    SP --> DL
    CF --> HP
    CB --> HP
    DL --> HP
    HP --> CV
    CV --> ME
    ME --> AB
    AB --> HE
    HE --> MR
    MR --> MS
    MS --> MC
    MS --> PM
    PM --> DM
    DM --> RT
    RT --> CL
```
