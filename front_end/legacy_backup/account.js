// Account page JavaScript
console.log('🔐 DonCoin Account Page Loaded');

// Wallet state
let walletConnected = false;
let userAddress = null;

// Mock wallet connection (in production, this would connect to MetaMask, WalletConnect, etc.)
function connectWallet() {
    // Simulate wallet connection
    walletConnected = true;
    userAddress = '0x742d' + Math.random().toString(16).substr(2, 4) + '...' + Math.random().toString(16).substr(2, 4);

    // Update UI
    updateWalletUI();

    // Simulate loading user data
    loadUserData();

    // Store connection state
    localStorage.setItem('walletConnected', 'true');
    localStorage.setItem('userAddress', userAddress);

    // Show success message
    console.log('✅ Wallet connected:', userAddress);
}

function disconnectWallet() {
    walletConnected = false;
    userAddress = null;

    // Clear stored state
    localStorage.removeItem('walletConnected');
    localStorage.removeItem('userAddress');

    updateWalletUI();
    console.log('👋 Wallet disconnected');
}

function updateWalletUI() {
    const disconnectedState = document.getElementById('wallet-disconnected');
    const connectedState = document.getElementById('wallet-connected');

    if (walletConnected) {
        disconnectedState.style.display = 'none';
        connectedState.style.display = 'block';
        document.getElementById('user-address').textContent = userAddress;
    } else {
        disconnectedState.style.display = 'block';
        connectedState.style.display = 'none';
    }
}

function loadUserData() {
    // Simulate loading user data
    const totalDonated = Math.floor(Math.random() * 1000) + 100;
    const projectsSupported = Math.floor(Math.random() * 10) + 1;
    const matchingEarned = Math.floor(totalDonated * 0.6);

    document.getElementById('total-donated').textContent = '$' + totalDonated;
    document.getElementById('projects-supported').textContent = projectsSupported;
    document.getElementById('matching-earned').textContent = '$' + matchingEarned;

    // Calculate and display trust score
    calculateAndDisplayTrustScore(totalDonated, projectsSupported);
}

// ===================================
// TRUST SCORE SYSTEM
// ===================================

function calculateTrustScore(userData) {
    // Metric 1: Account Age (15 points max)
    const accountAgeDays = userData.accountAgeDays || Math.floor(Math.random() * 500);
    const accountAgeScore = Math.min(accountAgeDays / 365, 1.0) * 15;

    // Metric 2: Contribution Frequency (20 points max)
    const totalContributions = userData.totalContributions || Math.floor(Math.random() * 60);
    const frequencyScore = Math.min(totalContributions / 50, 1.0) * 20;

    // Metric 3: Total Amount Donated (15 points max)
    const totalDonated = userData.totalDonated || 0;
    const totalDonatedScore = Math.min(totalDonated / 5000, 1.0) * 15;

    // Metric 4: Project Diversity (15 points max)
    const uniqueProjects = userData.uniqueProjects || 0;
    const diversityScore = Math.min(uniqueProjects / 20, 1.0) * 15;

    // Metric 5: Contribution Consistency (15 points max)
    // Simulate consistency (lower std dev = more consistent = higher score)
    const avgContribution = totalDonated / Math.max(totalContributions, 1);
    const simulatedStdDev = avgContribution * 0.3; // Simulate 30% deviation
    const consistencyScore = (1 - Math.min(simulatedStdDev / avgContribution, 1.0)) * 15;

    // Metric 6: Average Contribution Size (10 points max)
    const medianContribution = avgContribution;
    const avgContributionScore = Math.min(medianContribution / 100, 1.0) * 10;

    // Metric 7: Verification Status (10 points max)
    const verifiedCount = userData.verified ? 2 : 0; // 2 verifications = 10 points
    const verificationScore = Math.min(verifiedCount * 5, 10);

    // Calculate total score
    const totalScore = Math.round(
        accountAgeScore +
        frequencyScore +
        totalDonatedScore +
        diversityScore +
        consistencyScore +
        avgContributionScore +
        verificationScore
    );

    return {
        totalScore: Math.min(totalScore, 100),
        breakdown: {
            accountAge: Math.round(accountAgeScore),
            frequency: Math.round(frequencyScore),
            totalDonated: Math.round(totalDonatedScore),
            diversity: Math.round(diversityScore),
            consistency: Math.round(consistencyScore),
            avgContribution: Math.round(avgContributionScore),
            verification: Math.round(verificationScore)
        },
        rawData: {
            accountAgeDays,
            totalContributions,
            uniqueProjects,
            avgContribution: Math.round(avgContribution)
        }
    };
}

function getTrustTier(score) {
    if (score >= 81) return { name: 'Platinum', icon: '💎', color: '#00d4ff' };
    if (score >= 61) return { name: 'Gold', icon: '🥇', color: '#ffd700' };
    if (score >= 41) return { name: 'Silver', icon: '🥈', color: '#c0c0c0' };
    if (score >= 21) return { name: 'Bronze', icon: '🥉', color: '#cd7f32' };
    return { name: 'New', icon: '🌱', color: '#4ade80' };
}

function calculateAndDisplayTrustScore(totalDonated, projectsSupported) {
    // Prepare user data
    const userData = {
        accountAgeDays: Math.floor(Math.random() * 500) + 30,
        totalContributions: Math.floor(Math.random() * 60) + 5,
        totalDonated: totalDonated,
        uniqueProjects: projectsSupported,
        verified: Math.random() > 0.5 // 50% chance of being verified
    };

    // Calculate score
    const scoreData = calculateTrustScore(userData);
    const tier = getTrustTier(scoreData.totalScore);

    // Update UI
    const scoreElement = document.getElementById('trust-score');
    const tierElement = document.getElementById('trust-tier');
    const progressBar = document.getElementById('trust-progress');

    if (scoreElement) {
        scoreElement.textContent = scoreData.totalScore;
        scoreElement.style.color = tier.color;
    }

    if (tierElement) {
        tierElement.textContent = `${tier.icon} ${tier.name}`;
        tierElement.style.color = tier.color;
    }

    if (progressBar) {
        progressBar.style.width = scoreData.totalScore + '%';
        progressBar.style.background = `linear-gradient(90deg, ${tier.color}, ${tier.color}dd)`;
    }

    // Store score data for breakdown
    window.trustScoreData = scoreData;

    // Log for debugging
    console.log('📊 Trust Score:', scoreData.totalScore, tier.name);
}

function toggleScoreBreakdown() {
    const modal = document.getElementById('score-breakdown-modal');
    if (!modal) return;

    if (modal.style.display === 'none' || !modal.style.display) {
        // Show modal and populate data
        const data = window.trustScoreData;
        if (data) {
            document.getElementById('breakdown-account-age').textContent = `${data.breakdown.accountAge}/15`;
            document.getElementById('breakdown-frequency').textContent = `${data.breakdown.frequency}/20`;
            document.getElementById('breakdown-donated').textContent = `${data.breakdown.totalDonated}/15`;
            document.getElementById('breakdown-diversity').textContent = `${data.breakdown.diversity}/15`;
            document.getElementById('breakdown-consistency').textContent = `${data.breakdown.consistency}/15`;
            document.getElementById('breakdown-avg').textContent = `${data.breakdown.avgContribution}/10`;
            document.getElementById('breakdown-verification').textContent = `${data.breakdown.verification}/10`;
            document.getElementById('breakdown-total').textContent = `${data.totalScore}/100`;
        }
        modal.style.display = 'flex';
    } else {
        modal.style.display = 'none';
    }
}


// Check if wallet was previously connected
function checkWalletConnection() {
    const wasConnected = localStorage.getItem('walletConnected');
    const savedAddress = localStorage.getItem('userAddress');

    if (wasConnected === 'true' && savedAddress) {
        walletConnected = true;
        userAddress = savedAddress;
        updateWalletUI();
        loadUserData();
    }
}

// Event listeners
document.getElementById('connect-wallet-main')?.addEventListener('click', () => {
    connectWallet();
});

document.getElementById('disconnect-wallet-btn')?.addEventListener('click', () => {
    disconnectWallet();
});

// Header scroll effect
const header = document.getElementById('header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Initialize
checkWalletConnection();
