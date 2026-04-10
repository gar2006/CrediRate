document.addEventListener('DOMContentLoaded', () => {
    const dashboardView = document.getElementById('dashboard-view');
    const detailView = document.getElementById('detail-view');
    const userProfileView = document.getElementById('user-profile-view');
    const entitiesGrid = document.getElementById('entities-grid');
    const backBtn = document.getElementById('back-button');
    const profileBackBtn = document.getElementById('profile-back-button');
    const filterVerified = document.getElementById('filter-verified');

    const profileUsername = document.getElementById('profile-username');
    const profileVerifiedBadge = document.getElementById('profile-verified-badge');
    const profileJoinDate = document.getElementById('profile-join-date');
    const profileReputation = document.getElementById('profile-reputation');
    const profileRatingsList = document.getElementById('profile-ratings-list');

    const detailTitle = document.getElementById('detail-title');
    const detailDesc = document.getElementById('detail-desc');
    const detailTrustScore = document.getElementById('detail-trust-score');
    const detailAvgScore = document.getElementById('detail-avg-score');
    const ratingsList = document.getElementById('ratings-list');
    const feedbackForm = document.getElementById('feedback-form');
    const feedbackList = document.getElementById('feedback-list');
    const feedbackStatus = document.getElementById('feedback-status');
    const starRating = document.getElementById('star-rating');
    const starButtons = Array.from(document.querySelectorAll('.star-btn'));
    const ratingInput = document.getElementById('feedback-rating');
    const starRatingLabel = document.getElementById('star-rating-label');
    let activeEntityId = null;
    let currentRatingsData = [];

    if (filterVerified) {
        filterVerified.addEventListener('change', () => {
            renderAuditTrail();
        });
    }

    // Fetch and display dashboard
    async function loadDashboard() {
        dashboardView.classList.remove('hidden');
        detailView.classList.add('hidden');
        userProfileView.classList.add('hidden');
        entitiesGrid.innerHTML = '<p>Loading entities...</p>';

        try {
            const res = await fetch('/api/entities');
            const entities = await res.json();
            
            entitiesGrid.innerHTML = '';
            entities.forEach((entity, index) => {
                const card = document.createElement('div');
                card.className = `glass-panel entity-card animate-in`;
                card.style.animationDelay = `${index * 0.1}s`;
                
                const score = entity.trust_score ? Number(entity.trust_score).toFixed(2) : 'N/A';
                
                card.innerHTML = `
                    <h3 class="entity-name">${entity.entity_name}</h3>
                    <p class="entity-desc">${entity.description}</p>
                    <div class="score-display">
                        <span class="score-label" style="margin:0;">Trust Score</span>
                        <span class="score-value">${score}</span>
                    </div>
                `;
                
                card.addEventListener('click', () => loadDetailView(entity.entity_id));
                entitiesGrid.appendChild(card);
            });
        } catch (err) {
            console.error(err);
            entitiesGrid.innerHTML = '<p>Error loading data.</p>';
        }
    }

    // Load Detail View (The Explainer)
    async function loadDetailView(entityId) {
        activeEntityId = entityId;
        dashboardView.classList.add('hidden');
        userProfileView.classList.add('hidden');
        detailView.classList.remove('hidden');
        ratingsList.innerHTML = '<p>Loading audit trail...</p>';
        if (feedbackList) {
            feedbackList.innerHTML = '<p>Loading feedback...</p>';
        }
        feedbackStatus.textContent = '';

        try {
            const res = await fetch(`/api/entities/${entityId}/details`);
            const data = await res.json();
            
            const entity = data.entity;
            detailTitle.textContent = entity.entity_name;
            detailDesc.textContent = entity.description;
            detailTrustScore.textContent = entity.trust_score ? Number(entity.trust_score).toFixed(2) : 'N/A';
            detailAvgScore.textContent = entity.simple_average ? Number(entity.simple_average).toFixed(2) : 'N/A';
            
            currentRatingsData = data.ratings;
            renderAuditTrail();
            renderFeedback(data.feedback || []);
            
        } catch (err) {
            console.error(err);
            ratingsList.innerHTML = '<p>Error loading entity details.</p>';
            if (feedbackList) {
                feedbackList.innerHTML = '<p>Error loading feedback.</p>';
            }
        }
    }

    // Render the Explainer Cards
    function renderAuditTrail() {
        ratingsList.innerHTML = '';
        
        let ratings = currentRatingsData || [];
        if (filterVerified && filterVerified.checked) {
            ratings = ratings.filter(r => r.is_verified);
        }

        if (ratings.length === 0) {
            ratingsList.innerHTML = '<p>No ratings found matching criteria.</p>';
            return;
        }

        ratings.forEach((r, index) => {
            const card = document.createElement('div');
            card.className = 'rating-card animate-in';
            card.style.animationDelay = `${index * 0.1}s`;
            
            const stars = '★'.repeat(r.rating_value) + '☆'.repeat(5 - r.rating_value);
            const dateStr = new Date(r.created_at).toLocaleDateString();
            
            // Format weights
            const wRecency = Number(r.recency_factor).toFixed(2);
            const wReliability = Number(r.user_reliability_factor).toFixed(2);
            const wReputation = Number(r.reputation_factor).toFixed(2);
            const wVerified = Number(r.verification_bonus || 0).toFixed(2);
            const wHistory = Number(r.history_factor || 1).toFixed(2);
            const wRepeat = Number(r.repeat_reviewer_factor || 1).toFixed(2);
            const wFinal = Number(r.final_weight).toFixed(2);
            
            const verifiedBadge = r.is_verified ? '<span class="verified-badge">✔ Verified</span>' : '';
            
            card.innerHTML = `
                <div class="rating-content">
                    <div class="rating-meta">
                        <div><span class="rating-author clickable-author" data-userid="${r.user_id}" style="cursor: pointer; text-decoration: underline;">${r.username}</span>${verifiedBadge}</div>
                        <span class="rating-date">${dateStr} (${r.age_days} days ago)</span>
                    </div>
                    <div class="rating-stars">${stars}</div>
                    <p class="rating-text">"${r.review_text}"</p>
                </div>
                
                <div class="rating-explainer">
                    <div class="explainer-title">Credibility Breakdown</div>
                    <div class="factor-row">
                        <span class="label">Recency Band</span>
                        <span class="value">${r.recency_bucket}</span>
                    </div>
                    <div class="factor-row">
                        <span class="label">Recency Factor</span>
                        <span class="value">x${wRecency}</span>
                    </div>
                    <div class="factor-row" title="Reputation score: ${r.reputation_score}">
                        <span class="label">Reputation Factor</span>
                        <span class="value">x${wReputation}</span>
                    </div>
                    <div class="factor-row" title="Verification bonus applied from account status">
                        <span class="label">Verified Bonus</span>
                        <span class="value">+${wVerified}</span>
                    </div>
                    <div class="factor-row" title="Total submitted reviews by this user: ${r.total_reviews_by_user}">
                        <span class="label">History Factor</span>
                        <span class="value">x${wHistory}</span>
                    </div>
                    <div class="factor-row" title="Previous reviews by this user for this entity: ${r.prior_reviews_for_entity}">
                        <span class="label">Repeat Factor</span>
                        <span class="value">x${wRepeat}</span>
                    </div>
                    <div class="factor-row" title="Reputation plus verification bonus">
                        <span class="label">Reliability</span>
                        <span class="value">x${wReliability}</span>
                    </div>
                    <div class="weight-row">
                        <span>Net Weight</span>
                        <span class="value">${wFinal}</span>
                    </div>
                    <p class="breakdown-copy">${r.credibility_breakdown}</p>
                </div>
            `;
            
            const authorLink = card.querySelector('.clickable-author');
            if (authorLink) {
                authorLink.addEventListener('click', (e) => {
                    loadUserProfile(r.user_id || e.target.dataset.userid);
                });
            }
            
            ratingsList.appendChild(card);
        });
    }

    function renderFeedback(feedbackItems) {
        if (!feedbackList) {
            return;
        }

        feedbackList.innerHTML = '';

        if (!feedbackItems.length) {
            feedbackList.innerHTML = '<div class="glass-panel feedback-empty">No feedback submitted for this entity yet.</div>';
            return;
        }

        feedbackItems.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'glass-panel feedback-card animate-in';
            card.style.animationDelay = `${index * 0.08}s`;

            const dateStr = new Date(item.created_at).toLocaleString();
            const stars = item.rating_value
                ? '★'.repeat(item.rating_value) + '☆'.repeat(5 - item.rating_value)
                : '';

            card.innerHTML = `
                <div class="feedback-card-header">
                    <span class="feedback-author">${item.user_name}</span>
                    <span class="feedback-date">${dateStr}</span>
                </div>
                <div class="feedback-stars">${stars}</div>
                <p class="feedback-text">${item.feedback_text}</p>
            `;

            feedbackList.appendChild(card);
        });
    }

    function updateStarRating(value) {
        const numericValue = Number(value) || 0;
        ratingInput.value = numericValue ? String(numericValue) : '';
        starRating.dataset.value = numericValue;
        starRatingLabel.textContent = numericValue ? `${numericValue} of 5 stars selected` : 'Select a rating';

        starButtons.forEach((button) => {
            const buttonValue = Number(button.dataset.value);
            const active = buttonValue <= numericValue;
            button.textContent = active ? '★' : '☆';
            button.classList.toggle('active', active);
            button.setAttribute('aria-checked', String(buttonValue === numericValue));
        });
    }

    function attachStarHandlers() {
        starButtons.forEach((button) => {
            button.addEventListener('click', () => {
                updateStarRating(button.dataset.value);
            });

            button.addEventListener('mouseenter', () => {
                const hoverValue = Number(button.dataset.value);
                starButtons.forEach((star) => {
                    const starValue = Number(star.dataset.value);
                    star.textContent = starValue <= hoverValue ? '★' : '☆';
                    star.classList.toggle('hovered', starValue <= hoverValue);
                });
            });

            button.addEventListener('keydown', (event) => {
                if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
                    event.preventDefault();
                    updateStarRating(Math.min(5, Number(ratingInput.value || 0) + 1));
                }

                if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
                    event.preventDefault();
                    updateStarRating(Math.max(1, Number(ratingInput.value || 1) - 1));
                }
            });
        });

        starRating.addEventListener('mouseleave', () => {
            starButtons.forEach((star) => star.classList.remove('hovered'));
            updateStarRating(ratingInput.value);
        });
    }

    async function handleFeedbackSubmit(event) {
        event.preventDefault();

        if (!activeEntityId) {
            feedbackStatus.textContent = 'Select an entity before submitting feedback.';
            feedbackStatus.className = 'feedback-status error';
            return;
        }

        const formData = new FormData(feedbackForm);
        const payload = {
            user_name: formData.get('user_name').trim(),
            rating_value: Number(formData.get('rating_value')),
            feedback_text: formData.get('feedback_text').trim()
        };

        feedbackStatus.textContent = 'Submitting feedback...';
        feedbackStatus.className = 'feedback-status';

        try {
            const res = await fetch(`/api/entities/${activeEntityId}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Unable to submit feedback.');
            }

            feedbackStatus.textContent = `${data.message} Trust score updated.`;
            feedbackStatus.className = 'feedback-status success';
            feedbackForm.reset();
            updateStarRating(0);
            await loadDetailView(activeEntityId);
        } catch (err) {
            console.error(err);
            feedbackStatus.textContent = err.message;
            feedbackStatus.className = 'feedback-status error';
        }
    }

    // Load User Profile View
    async function loadUserProfile(userId) {
        dashboardView.classList.add('hidden');
        detailView.classList.add('hidden');
        userProfileView.classList.remove('hidden');
        profileRatingsList.innerHTML = '<p>Loading profile...</p>';

        try {
            const res = await fetch(`/api/users/${userId}`);
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error);
            
            profileUsername.textContent = data.user.username;
            if (data.user.is_verified) {
                profileVerifiedBadge.classList.remove('hidden');
            } else {
                profileVerifiedBadge.classList.add('hidden');
            }
            profileJoinDate.textContent = `Joined: ${new Date(data.user.join_date).toLocaleDateString()}`;
            profileReputation.textContent = data.user.reputation_score;
            
            profileRatingsList.innerHTML = '';
            if (data.ratings.length === 0) {
                profileRatingsList.innerHTML = '<p>No reviews from this user.</p>';
            } else {
                data.ratings.forEach((r, index) => {
                    const card = document.createElement('div');
                    card.className = 'glass-panel entity-card animate-in';
                    card.style.animationDelay = `${index * 0.1}s`;
                    const stars = '★'.repeat(r.rating_value) + '☆'.repeat(5 - r.rating_value);
                    const finalW = r.final_weight ? Number(r.final_weight).toFixed(2) : '1.00';
                    card.innerHTML = `
                        <h4 style="margin:0 0 10px; color:var(--accent-blue)">For: ${r.entity_name}</h4>
                        <div class="rating-meta" style="margin-bottom:12px;">
                            <span class="rating-date">${new Date(r.created_at).toLocaleDateString()}</span>
                            <span style="font-family:monospace; color:var(--accent-teal);">Weight: x${finalW}</span>
                        </div>
                        <div class="rating-stars">${stars}</div>
                        <p class="rating-text">"${r.review_text}"</p>
                    `;
                    profileRatingsList.appendChild(card);
                });
            }
        } catch (err) {
            console.error(err);
            profileRatingsList.innerHTML = '<p>Error loading user profile.</p>';
        }
    }

    backBtn.addEventListener('click', loadDashboard);
    if(profileBackBtn) profileBackBtn.addEventListener('click', loadDashboard);
    feedbackForm.addEventListener('submit', handleFeedbackSubmit);
    attachStarHandlers();
    updateStarRating(0);

    // Init
    loadDashboard();
});
