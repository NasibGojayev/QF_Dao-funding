export type UUID = string;
export type DateTime = string; // ISO 8601 string
export type Decimal = string; // Using string to preserve precision for financial data

export enum WalletStatus {
    Active = 'active',
    Frozen = 'frozen',
    Flagged = 'flagged',
}

export interface Wallet {
    wallet_id: UUID;
    address: string;
    balance: Decimal;
    status: WalletStatus;
    last_activity: DateTime;
}

export interface Donor {
    donor_id: UUID;
    wallet: Wallet | UUID; // Can be expanded object or ID depending on API response
    username: string;
    reputation_score: number;
    joined_at: DateTime;
}

export interface SybilScore {
    score_id: UUID;
    wallet: Wallet | UUID;
    score: number;
    verified_by: string;
    last_updated: DateTime;
}

export interface MatchingPool {
    pool_id: UUID;
    total_funds: Decimal;
    allocated_funds: Decimal;
    replenished_by: string;
}

export enum RoundStatus {
    Active = 'active',
    Closed = 'closed',
    Upcoming = 'upcoming',
}

export interface Round {
    round_id: UUID;
    start_date: DateTime;
    end_date: DateTime;
    matching_pool: MatchingPool | UUID;
    status: RoundStatus;
}

export enum ProposalStatus {
    Pending = 'pending',
    Approved = 'approved',
    Rejected = 'rejected',
    Funded = 'funded',
}

export interface Proposal {
    proposal_id: UUID;
    title: string;
    description: string;
    proposer: Donor | UUID;
    status: ProposalStatus;
    round: Round | UUID;
    total_donations: Decimal;
    created_at: DateTime;
}

export interface Donation {
    donation_id: UUID;
    donor: Donor | UUID;
    proposal: Proposal | UUID;
    amount: Decimal;
    sybil_score: number;
    tx_hash: string;
    created_at: DateTime;
}

export interface Match {
    match_id: UUID;
    proposal: Proposal | UUID;
    round: Round | UUID;
    matched_amount: Decimal;
}

export interface QFResult {
    result_id: UUID;
    round: Round | UUID;
    proposal: Proposal | UUID;
    calculated_match: Decimal;
    verified: boolean;
}

export interface Payout {
    payout_id: UUID;
    proposal: Proposal | UUID;
    round: Round | UUID;
    amount: Decimal;
    tx_hash: string;
    distributed_at: DateTime;
}

export interface ContractEvent {
    event_id: UUID;
    event_type: string;
    round?: Round | UUID | null;
    proposal?: Proposal | UUID | null;
    timestamp: DateTime;
    tx_hash: string;
}

export enum GovernanceRole {
    Member = 'member',
    Admin = 'admin',
    Council = 'council',
}

export interface GovernanceToken {
    holder_id: UUID;
    wallet: Wallet | UUID;
    voting_power: Decimal;
    role: GovernanceRole;
}
