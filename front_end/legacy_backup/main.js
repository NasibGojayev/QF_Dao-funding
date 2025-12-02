import './style.css';
import { projects } from './projects.js';

// Lazy load 3D Scene
let scene3D = null;
let sceneInitialized = false;

const canvasContainer = document.getElementById('canvas-container');

// Initialize 3D scene only when it's in viewport
const initScene = async () => {
    if (sceneInitialized) return;
    sceneInitialized = true;

    const { Scene3D } = await import('./scene.js');
    scene3D = new Scene3D(canvasContainer);
};

// Use Intersection Observer to lazy load 3D scene
const sceneObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            initScene();
            sceneObserver.unobserve(entry.target);
        }
    });
}, { rootMargin: '50px' });

if (canvasContainer) {
    sceneObserver.observe(canvasContainer);
}


// Header scroll effect
const header = document.getElementById('header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Animated counter for stats
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = formatNumber(target);
            clearInterval(timer);
        } else {
            element.textContent = formatNumber(Math.floor(current));
        }
    }, 16);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return '$' + (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return '$' + (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
}

// Initialize counters with Intersection Observer
const observerOptions = {
    threshold: 0.5,
    rootMargin: '0px'
};

const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            const target = parseInt(entry.target.dataset.target);
            animateCounter(entry.target, target);
            entry.target.classList.add('counted');
        }
    });
}, observerOptions);

document.querySelectorAll('.stat-number').forEach(stat => {
    statsObserver.observe(stat);
});

// Fade in animations on scroll
const fadeElements = document.querySelectorAll('.fade-in-up');
const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animationPlayState = 'running';
        }
    });
}, observerOptions);

fadeElements.forEach(element => {
    element.style.animationPlayState = 'paused';
    fadeObserver.observe(element);
});

// Render projects
let projectsToShow = 6; // Initially show 6 projects
let allProjectsLoaded = false;

function renderProjects(showAll = false) {
    const projectsGrid = document.getElementById('projects-grid');
    const viewMoreContainer = document.getElementById('view-more-container');

    // Clear existing projects if re-rendering
    if (showAll && !allProjectsLoaded) {
        projectsGrid.innerHTML = '';
    }

    const projectsToRender = showAll ? projects : projects.slice(0, projectsToShow);

    projectsToRender.forEach(project => {
        const progress = (project.raised / project.goal) * 100;
        const matching = calculateMatching(project.contributors, project.raised);
        const daysLeft = Math.floor(Math.random() * 30) + 1; // Simulate days left
        const isTrending = Math.random() > 0.7; // 30% chance of trending
        const statusBadge = progress >= 100 ? '✓ Funded' : progress >= 75 ? '🔥 Hot' : daysLeft <= 7 ? '⏰ Ending Soon' : '';

        const card = document.createElement('div');
        card.className = 'project-card';
        card.innerHTML = `
      <div style="position: relative;">
        <img src="/images/${project.image}" alt="${project.title}" class="project-image" loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22220%22%3E%3Cdefs%3E%3ClinearGradient id=%22grad%22 x1=%220%25%22 y1=%220%25%22 x2=%22100%25%22 y2=%22100%25%22%3E%3Cstop offset=%220%25%22 style=%22stop-color:%23667eea;stop-opacity:1%22 /%3E%3Cstop offset=%22100%25%22 style=%22stop-color:%23764ba2;stop-opacity:1%22 /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill=%22url(%23grad)%22 width=%22400%22 height=%22220%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2228%22 fill=%22white%22 font-weight=%22bold%22%3E${project.category}%3C/text%3E%3C/svg%3E'">
        ${isTrending ? '<span style="position: absolute; top: 12px; left: 12px; background: rgba(236, 72, 153, 0.95); color: white; padding: 0.4rem 0.8rem; border-radius: 2rem; font-size: 0.75rem; font-weight: 700; backdrop-filter: blur(10px); box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4);">🔥 Trending</span>' : ''}
        ${statusBadge ? `<span style="position: absolute; top: 12px; right: 12px; background: rgba(139, 92, 246, 0.95); color: white; padding: 0.4rem 0.8rem; border-radius: 2rem; font-size: 0.75rem; font-weight: 700; backdrop-filter: blur(10px); box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);">${statusBadge}</span>` : ''}
      </div>
      <div class="project-content">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
          <h3 class="project-title">${project.title}</h3>
        </div>
        <div style="margin-bottom: 0.75rem;">
          <span style="display: inline-block; background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2)); color: var(--primary-purple); padding: 0.35rem 0.85rem; border-radius: 1.5rem; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(139, 92, 246, 0.3);">
            <span style="opacity: 0.8;">📁</span> ${project.category}
          </span>
          <span style="display: inline-block; margin-left: 0.5rem; color: var(--text-tertiary); font-size: 0.75rem;">
            ${daysLeft} days left
          </span>
        </div>
        <p class="project-description">${project.description}</p>
        
        <div style="margin: 1rem 0;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem; font-size: 0.875rem;">
            <span style="color: var(--text-secondary); font-weight: 500;">${progress.toFixed(0)}% funded</span>
            <span style="color: var(--primary-purple); font-weight: 700;">$${(project.raised / 1000).toFixed(0)}K <span style="color: var(--text-tertiary); font-weight: 400;">/ $${(project.goal / 1000).toFixed(0)}K</span></span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${Math.min(progress, 100)}%"></div>
          </div>
        </div>
        
        <div class="project-meta">
          <div class="project-funding">
            <span class="funding-label">👥 Contributors</span>
            <span class="funding-amount">${project.contributors}</span>
          </div>
          <div class="project-funding">
            <span class="funding-label">💎 Matching</span>
            <span class="funding-amount" style="color: var(--primary-cyan);">$${(matching / 1000).toFixed(1)}K</span>
          </div>
        </div>
        
        <button class="btn btn-primary" style="width: 100%; margin-top: 1.25rem; padding: 0.85rem 1.5rem; font-weight: 600; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);" onclick="contributeToProject(${project.id})">
          💰 Contribute Now
        </button>
      </div>
    `;

        projectsGrid.appendChild(card);
    });

    // Show/hide View More button
    if (viewMoreContainer) {
        if (showAll || projects.length <= projectsToShow) {
            viewMoreContainer.style.display = 'none';
            allProjectsLoaded = true;
        } else {
            viewMoreContainer.style.display = 'flex';
        }
    }
}

function loadMoreProjects() {
    renderProjects(true);
}

// Calculate quadratic funding matching
function calculateMatching(contributors, raised) {
    // Simplified quadratic formula simulation
    // In reality, this would calculate sum of sqrt of individual contributions
    const avgContribution = raised / contributors;
    const sqrtSum = Math.sqrt(avgContribution) * contributors;
    const matching = Math.pow(sqrtSum, 2) * 0.3; // 30% matching rate
    return matching;
}

// Contribute to project (placeholder)
window.contributeToProject = function (projectId) {
    const project = projects.find(p => p.id === projectId);
    alert(`Contributing to: ${project.title}\n\nIn a production app, this would open a Web3 wallet connection dialog.`);
};

// 3D card tilt effect
document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.project-card');

    cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;

        if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
        } else {
            card.style.transform = '';
        }
    });
});

// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offsetTop = target.offsetTop - 80;
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// Initialize projects
renderProjects();

// Add fade-in animations to card elements
const cards = document.querySelectorAll('.card');
const cardObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            setTimeout(() => {
                entry.target.classList.add('fade-in-up');
                entry.target.style.animationPlayState = 'running';
            }, index * 100);
            cardObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

cards.forEach(card => {
    card.style.opacity = '0';
    cardObserver.observe(card);
});

console.log('🚀 DonCoin initialized!');
console.log('💎 3D Model loaded with', projects.length, 'active projects');
