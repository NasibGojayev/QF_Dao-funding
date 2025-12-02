import {
    Proposal, ProposalStatus,
    Round, RoundStatus,
    Donor,
    Wallet, WalletStatus,
    MatchingPool,
    Donation
} from '../types/models';

// Extended type for Frontend UI requirements
export interface FrontendProposal extends Proposal {
    image: string;
    category: string;
    goal: number; // mapped from total_donations target or similar? For now separate.
    contributor_count: number;
}

// Mock Data Generators
const generateUUID = () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
});

const generateDate = (daysAgo: number = 0) => {
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return date.toISOString();
};

// Mock Wallets
const mockWallets: Wallet[] = [
    {
        wallet_id: generateUUID(),
        address: '0x71C7656EC7ab88b098defB751B7401B5f6d8976F',
        balance: '1000.00',
        status: WalletStatus.Active,
        last_activity: generateDate()
    },
    {
        wallet_id: generateUUID(),
        address: '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
        balance: '500.00',
        status: WalletStatus.Active,
        last_activity: generateDate(1)
    }
];

// Mock Donors
const mockDonors: Donor[] = [
    {
        donor_id: generateUUID(),
        wallet: mockWallets[0],
        username: 'alice_eth',
        reputation_score: 100,
        joined_at: generateDate(30)
    },
    {
        donor_id: generateUUID(),
        wallet: mockWallets[1],
        username: 'bob_builder',
        reputation_score: 85,
        joined_at: generateDate(15)
    }
];

// Mock Round
const mockRound: Round = {
    round_id: generateUUID(),
    start_date: generateDate(10),
    end_date: generateDate(-20), // 20 days in future
    matching_pool: {
        pool_id: generateUUID(),
        total_funds: '100000.00',
        allocated_funds: '0.00',
        replenished_by: 'DAO Treasury'
    },
    status: RoundStatus.Active
};

// Mock Proposals
const mockProposals: FrontendProposal[] = [
    {
        proposal_id: generateUUID(),
        title: 'Open Source Library',
        description: 'A comprehensive JavaScript library for decentralized applications with extensive documentation and community support.',
        proposer: mockDonors[0],
        status: ProposalStatus.Approved,
        round: mockRound,
        total_donations: '45000.00',
        created_at: generateDate(5),
        // Frontend specific fields
        image: 'project1.png',
        category: 'Development',
        goal: 100000,
        contributor_count: 234
    },
    {
        proposal_id: generateUUID(),
        title: 'Climate Research Initiative',
        description: 'Open data platform for climate change research, providing free access to global temperature and weather patterns.',
        proposer: mockDonors[1],
        status: ProposalStatus.Approved,
        round: mockRound,
        total_donations: '72000.00',
        created_at: generateDate(7),
        // Frontend specific fields
        image: 'project2.png',
        category: 'Research',
        goal: 150000,
        contributor_count: 456
    },
    {
        proposal_id: generateUUID(),
        title: 'Educational Platform',
        description: 'Free coding education for underprivileged communities with interactive lessons and mentorship programs.',
        proposer: mockDonors[0],
        status: ProposalStatus.Approved,
        round: mockRound,
        total_donations: '38000.00',
        created_at: generateDate(3),
        // Frontend specific fields
        image: 'project3.png',
        category: 'Education',
        goal: 80000,
        contributor_count: 189
    },
    {
        proposal_id: generateUUID(),
        title: 'Community Gardens Network',
        description: 'Building sustainable urban gardens and teaching organic farming techniques to local communities.',
        proposer: mockDonors[1],
        status: ProposalStatus.Approved,
        round: mockRound,
        total_donations: '24000.00',
        created_at: generateDate(8),
        // Frontend specific fields
        image: 'project4.png',
        category: 'Environment',
        goal: 60000,
        contributor_count: 312
    },
    {
        proposal_id: generateUUID(),
        title: 'Mental Health Toolkit',
        description: 'Open source mental health resources and AI-powered chatbot for immediate support and guidance.',
        proposer: mockDonors[0],
        status: ProposalStatus.Approved,
        round: mockRound,
        total_donations: '56000.00',
        created_at: generateDate(12),
        // Frontend specific fields
        image: 'project5.png',
        category: 'Health',
        goal: 120000,
        contributor_count: 521
    },
    {
        proposal_id: generateUUID(),
        title: 'Accessibility Tools',
        description: 'Comprehensive suite of accessibility tools for web developers to create inclusive digital experiences.',
        proposer: mockDonors[1],
        status: ProposalStatus.Approved,
        round: mockRound,
        total_donations: '41000.00',
        created_at: generateDate(4),
        // Frontend specific fields
        image: 'project6.png',
        category: 'Development',
        goal: 90000,
        contributor_count: 278
    }
];

// API Service
export const getProposals = async (): Promise<FrontendProposal[]> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockProposals;
};

export const getRounds = async (): Promise<Round[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return [mockRound];
};

export const getDonors = async (): Promise<Donor[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockDonors;
};

export const createProposal = async (data: Partial<FrontendProposal>): Promise<FrontendProposal> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const newProposal: FrontendProposal = {
        proposal_id: generateUUID(),
        title: data.title || 'Untitled',
        description: data.description || '',
        proposer: mockDonors[0], // Default to first donor for now
        status: ProposalStatus.Pending,
        round: mockRound,
        total_donations: '0.00',
        created_at: generateDate(),
        image: 'project1.png', // Default image
        category: data.category || 'Public Goods',
        goal: data.goal || 10000,
        contributor_count: 0,
        ...data
    };
    mockProposals.push(newProposal);
    return newProposal;
};

export const createDonation = async (data: { proposalId: string, amount: number }): Promise<Donation> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const donation: Donation = {
        donation_id: generateUUID(),
        donor: mockDonors[0],
        proposal: mockProposals.find(p => p.proposal_id === data.proposalId) || mockProposals[0],
        amount: data.amount.toString(),
        sybil_score: 100,
        tx_hash: '0x' + generateUUID(),
        created_at: generateDate()
    };
    // In a real app, we'd update the proposal's total_donations here
    return donation;
};

export const connectWallet = async (): Promise<Wallet> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    return mockWallets[0];
};
