# Quadratic Funding DAO - System Design (SDF1)

## 1. Use Case Diagram
```mermaid
usecaseDiagram
    actor "Donor" as D
    actor "Proposer" as P
    actor "Admin" as A
    actor "System/Smart Contract" as S

    package "Quadratic Funding DAO" {
        usecase "Connect Wallet" as UC1
        usecase "Submit Proposal" as UC2
        usecase "View Proposals" as UC3
        usecase "Donate to Proposal" as UC4
        usecase "Create Funding Round" as UC5
        usecase "Resolve Round" as UC6
        usecase "Claim Funds" as UC7
        usecase "Manage Knowledge Tags" as UC8
    }

    D --> UC1
    D --> UC3
    D --> UC4
    P --> UC1
    P --> UC2
    P --> UC7
    A --> UC1
    A --> UC5
    A --> UC6
    A --> UC8
    
    UC4 ..> S : "Record Donation"
    UC6 ..> S : "Calculate Matching"
```

## 2. Class Diagram
```mermaid
classDiagram
    class User {
        +address wallet_address
        +string username
        +login()
        +connectWallet()
    }

    class Proposal {
        +int id
        +string title
        +string description
        +string[] knowledge_tags
        +address proposer
        +float total_donations
        +submit()
        +update()
    }

    class Round {
        +int id
        +datetime start_date
        +datetime end_date
        +float matching_pool
        +start()
        +end()
        +calculateMatching()
    }

    class Donation {
        +int id
        +float amount
        +datetime timestamp
        +address donor
        +int proposal_id
        +verify()
    }

    class GrantRegistry {
        +registerGrant()
        +verifyGrant()
    }

    User "1" -- "*" Donation : makes
    User "1" -- "*" Proposal : creates
    Proposal "1" -- "*" Donation : receives
    Round "1" -- "*" Proposal : includes
    Round "1" -- "*" Donation : tracks
```

## 3. Sequence Diagram (Donation Flow)
```mermaid
sequenceDiagram
    participant Donor
    participant Frontend
    participant API as FastAPI/Django
    participant Contract as DonationVault
    participant DB

    Donor->>Frontend: Select Proposal & Amount
    Frontend->>Frontend: Connect Wallet
    Donor->>Frontend: Confirm Transaction
    Frontend->>Contract: sendDonation(proposalId)
    Contract-->>Frontend: Transaction Hash
    Frontend->>API: POST /api/tx/verify {hash}
    API->>Contract: verifyTransaction(hash)
    Contract-->>API: Status: Confirmed
    API->>DB: Record Donation (Off-chain Index)
    DB-->>API: Success
    API-->>Frontend: Donation Success
    Frontend-->>Donor: Show "Donation Confirmed" Toast
```

## 4. Activity Diagram (Round Lifecycle)
```mermaid
activityDiagram
    start
    :Admin creates Round;
    :Set Matching Pool & Dates;
    if (Date >= Start Date?) then (yes)
        :Round Active;
        fork
            :Accept Proposals;
        fork again
            :Accept Donations;
            :Calculate Quadratic Match;
        end fork
        if (Date > End Date?) then (yes)
            :Round Ended;
            :Admin calls Resolve();
            :Calculate Final Distribution;
            :Distribute Funds;
            stop
        else (no)
            :Continue;
        endif
    else (no)
        :Pending Start;
    endif
```

## 5. Entity Relationship Diagram (ERD)
```mermaid
erDiagram
    USERS ||--o{ PROPOSALS : creates
    USERS ||--o{ DONATIONS : makes
    ROUNDS ||--|{ PROPOSALS : contains
    PROPOSALS ||--o{ DONATIONS : receives
    ROUNDS ||--o{ MATCHING_POOL : has

    USERS {
        string wallet_address PK
        string username
        datetime created_at
        string role
    }

    PROPOSALS {
        int id PK
        string title
        text description
        string status
        xml knowledge_tags
        string proposer_address FK
        int round_id FK
    }

    ROUNDS {
        int id PK
        string name
        datetime start_time
        datetime end_time
        decimal matching_pool_amount
        string status
    }

    DONATIONS {
        int id PK
        decimal amount
        string token_symbol
        datetime timestamp
        string donor_address FK
        int proposal_id FK
        string tx_hash
    }

    MATCHING_POOL {
        int id PK
        int round_id FK
        decimal total_amount
        string token_address
    }
```
