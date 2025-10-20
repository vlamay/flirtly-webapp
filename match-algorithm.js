// match-algorithm.js - Advanced matching algorithm for dating app

class MatchAlgorithm {
    constructor() {
        this.weights = {
            demographics: 0.20,    // возраст, локация
            interests: 0.30,       // общие интересы
            personality: 0.25,     // совместимость характеров
            behavior: 0.15,        // взаимные лайки
            popularity: 0.10       // популярность кандидата
        };
        
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    // ===================================
    // MAIN MATCHING FUNCTION
    // ===================================

    async findMatches(userId, limit = 50) {
        const cacheKey = `matches_${userId}_${limit}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            // Get user profile
            const user = await this.getUserProfile(userId);
            if (!user) {
                throw new Error('User profile not found');
            }

            // Step 1: Quick pre-filtering
            const candidates = await this.quickFilter(user);
            
            // Step 2: Calculate compatibility scores
            const scoredCandidates = await this.calculateCompatibilityScores(user, candidates);
            
            // Step 3: Sort and rank
            const sortedCandidates = scoredCandidates
                .sort((a, b) => b.score - a.score)
                .slice(0, limit);

            // Cache results
            this.cache.set(cacheKey, {
                data: sortedCandidates,
                timestamp: Date.now()
            });

            return sortedCandidates;

        } catch (error) {
            console.error('Match algorithm error:', error);
            return [];
        }
    }

    // ===================================
    // QUICK FILTERING
    // ===================================

    async quickFilter(user) {
        const filters = {
            // Basic demographic filters
            ageRange: this.getAgeRange(user.age, user.preferences?.ageRange),
            gender: user.looking_for,
            location: user.city,
            
            // Exclude already interacted users
            excludeUsers: await this.getExcludedUsers(user.id),
            
            // Active users only
            isActive: true,
            
            // Has profile completeness
            profileComplete: true
        };

        // In real app, this would query the database
        return await this.queryCandidates(filters);
    }

    getAgeRange(userAge, preferences) {
        const defaultRange = 5; // ±5 years by default
        const minAge = preferences?.minAge || Math.max(18, userAge - defaultRange);
        const maxAge = preferences?.maxAge || Math.min(99, userAge + defaultRange);
        
        return { min: minAge, max: maxAge };
    }

    async getExcludedUsers(userId) {
        // Get users that this user has already liked/disliked/blocked
        const interactions = await this.getUserInteractions(userId);
        return interactions.map(interaction => interaction.targetUserId);
    }

    // ===================================
    // COMPATIBILITY CALCULATION
    // ===================================

    async calculateCompatibilityScores(user, candidates) {
        const scoredCandidates = [];

        for (const candidate of candidates) {
            try {
                const score = await this.calculateCompatibilityScore(user, candidate);
                scoredCandidates.push({
                    user: candidate,
                    score: score.total,
                    breakdown: score.breakdown,
                    explanation: score.explanation
                });
            } catch (error) {
                console.error(`Error calculating score for candidate ${candidate.id}:`, error);
            }
        }

        return scoredCandidates;
    }

    async calculateCompatibilityScore(user, candidate) {
        const scores = {};

        // Demographics score (age, location)
        scores.demographics = this.calculateDemographicsScore(user, candidate);

        // Interests score (common interests)
        scores.interests = this.calculateInterestsScore(user, candidate);

        // Personality score (compatibility)
        scores.personality = this.calculatePersonalityScore(user, candidate);

        // Behavior score (mutual interactions)
        scores.behavior = await this.calculateBehaviorScore(user, candidate);

        // Popularity score (how popular the candidate is)
        scores.popularity = await this.calculatePopularityScore(candidate);

        // Calculate weighted total
        const totalScore = Object.keys(scores).reduce((total, key) => {
            return total + (scores[key] * this.weights[key]);
        }, 0);

        return {
            total: Math.min(1.0, Math.max(0.0, totalScore)), // Clamp between 0 and 1
            breakdown: scores,
            explanation: this.generateExplanation(scores, user, candidate)
        };
    }

    // ===================================
    // SCORING FUNCTIONS
    // ===================================

    calculateDemographicsScore(user, candidate) {
        let score = 0;

        // Age compatibility
        const ageDiff = Math.abs(user.age - candidate.age);
        const ageScore = Math.max(0, 1 - (ageDiff / 10)); // Perfect at same age, decreases with difference
        score += ageScore * 0.6;

        // Location compatibility
        if (user.city === candidate.city) {
            score += 0.4; // Same city = perfect location match
        } else if (user.country === candidate.country) {
            score += 0.2; // Same country = partial match
        }

        return Math.min(1.0, score);
    }

    calculateInterestsScore(user, candidate) {
        const userInterests = new Set(user.interests || []);
        const candidateInterests = new Set(candidate.interests || []);

        if (userInterests.size === 0 || candidateInterests.size === 0) {
            return 0.5; // Neutral score if no interests specified
        }

        // Jaccard similarity
        const intersection = new Set([...userInterests].filter(x => candidateInterests.has(x)));
        const union = new Set([...userInterests, ...candidateInterests]);
        
        const jaccardSimilarity = intersection.size / union.size;

        // Boost score for having many common interests
        const commonInterestsBonus = Math.min(0.2, intersection.size * 0.05);
        
        return Math.min(1.0, jaccardSimilarity + commonInterestsBonus);
    }

    calculatePersonalityScore(user, candidate) {
        // This would integrate with personality assessment
        // For now, use a simplified version based on bio analysis
        
        const userPersonality = this.analyzePersonalityFromBio(user.bio);
        const candidatePersonality = this.analyzePersonalityFromBio(candidate.bio);

        // Calculate personality compatibility
        let score = 0.5; // Default neutral score

        // Introvert/Extrovert compatibility
        if (userPersonality.introvert !== candidatePersonality.introvert) {
            score += 0.2; // Opposites attract
        }

        // Similar values and interests
        const valuesSimilarity = this.calculateValuesSimilarity(userPersonality, candidatePersonality);
        score += valuesSimilarity * 0.3;

        return Math.min(1.0, score);
    }

    analyzePersonalityFromBio(bio) {
        if (!bio) {
            return { introvert: 0.5, values: [] };
        }

        const bioLower = bio.toLowerCase();
        
        // Simple keyword analysis
        const introvertKeywords = ['тихий', 'спокойный', 'домосед', 'интроверт', 'одиночество'];
        const extrovertKeywords = ['активный', 'общительный', 'вечеринки', 'друзья', 'экстраверт'];

        const introvertScore = introvertKeywords.reduce((score, keyword) => 
            score + (bioLower.includes(keyword) ? 1 : 0), 0);
        const extrovertScore = extrovertKeywords.reduce((score, keyword) => 
            score + (bioLower.includes(keyword) ? 1 : 0), 0);

        return {
            introvert: introvertScore > extrovertScore ? 1 : 0,
            values: this.extractValuesFromBio(bio)
        };
    }

    extractValuesFromBio(bio) {
        const values = [];
        const bioLower = bio.toLowerCase();

        const valueKeywords = {
            'travel': ['путешествия', 'путешествовать', 'мир', 'страны'],
            'sports': ['спорт', 'тренировки', 'фитнес', 'бег', 'йога'],
            'music': ['музыка', 'концерт', 'группа', 'песни'],
            'art': ['искусство', 'живопись', 'театр', 'музей'],
            'nature': ['природа', 'горы', 'море', 'лес', 'походы'],
            'technology': ['технологии', 'программирование', 'гаджеты'],
            'food': ['кулинария', 'рестораны', 'готовить', 'вкусно']
        };

        for (const [value, keywords] of Object.entries(valueKeywords)) {
            if (keywords.some(keyword => bioLower.includes(keyword))) {
                values.push(value);
            }
        }

        return values;
    }

    calculateValuesSimilarity(userPersonality, candidatePersonality) {
        const userValues = new Set(userPersonality.values);
        const candidateValues = new Set(candidatePersonality.values);

        if (userValues.size === 0 || candidateValues.size === 0) {
            return 0.5;
        }

        const intersection = new Set([...userValues].filter(x => candidateValues.has(x)));
        const union = new Set([...userValues, ...candidateValues]);

        return intersection.size / union.size;
    }

    async calculateBehaviorScore(user, candidate) {
        // Check if candidate has liked this user
        const hasMutualLike = await this.checkMutualLike(user.id, candidate.id);
        
        if (hasMutualLike) {
            return 1.0; // Perfect score for mutual likes
        }

        // Check if candidate is active and responsive
        const candidateActivity = await this.getUserActivity(candidate.id);
        
        // Boost score for active users
        const activityScore = Math.min(0.8, candidateActivity.responseRate * 0.8);
        
        return activityScore;
    }

    async calculatePopularityScore(candidate) {
        // Get candidate's popularity metrics
        const popularityMetrics = await this.getUserPopularity(candidate.id);
        
        // Normalize popularity score (0-1)
        const maxLikes = 1000; // Assume max likes for normalization
        const popularityScore = Math.min(1.0, popularityMetrics.likesReceived / maxLikes);
        
        return popularityScore;
    }

    // ===================================
    // EXPLANATION GENERATION
    // ===================================

    generateExplanation(scores, user, candidate) {
        const explanations = [];

        // Demographics explanation
        if (scores.demographics > 0.8) {
            explanations.push("Отличное совпадение по возрасту и локации");
        } else if (scores.demographics > 0.6) {
            explanations.push("Хорошее совпадение по демографии");
        }

        // Interests explanation
        if (scores.interests > 0.7) {
            explanations.push("Много общих интересов");
        } else if (scores.interests > 0.4) {
            explanations.push("Есть общие интересы");
        }

        // Personality explanation
        if (scores.personality > 0.8) {
            explanations.push("Отличная совместимость характеров");
        } else if (scores.personality > 0.6) {
            explanations.push("Хорошая совместимость");
        }

        // Behavior explanation
        if (scores.behavior >= 1.0) {
            explanations.push("Взаимная симпатия!");
        } else if (scores.behavior > 0.7) {
            explanations.push("Активный и отзывчивый пользователь");
        }

        // Popularity explanation
        if (scores.popularity > 0.8) {
            explanations.push("Очень популярный профиль");
        }

        return explanations.length > 0 ? explanations.join(", ") : "Потенциальное совпадение";
    }

    // ===================================
    // DATA ACCESS METHODS (Mock implementations)
    // ===================================

    async getUserProfile(userId) {
        // In real app, this would query the database
        return {
            id: userId,
            age: 25,
            gender: 'male',
            looking_for: 'female',
            city: 'Москва',
            country: 'Россия',
            interests: ['музыка', 'спорт', 'путешествия'],
            bio: 'Люблю активный отдых и хорошую музыку',
            preferences: {
                ageRange: { minAge: 20, maxAge: 30 }
            }
        };
    }

    async queryCandidates(filters) {
        // In real app, this would query the database with filters
        return [
            {
                id: 101,
                age: 23,
                gender: 'female',
                city: 'Москва',
                country: 'Россия',
                interests: ['музыка', 'искусство', 'путешествия'],
                bio: 'Художница, люблю живопись и классическую музыку',
                isActive: true,
                profileComplete: true
            },
            {
                id: 102,
                age: 27,
                gender: 'female',
                city: 'Москва',
                country: 'Россия',
                interests: ['спорт', 'фитнес', 'здоровье'],
                bio: 'Фитнес-тренер, веду активный образ жизни',
                isActive: true,
                profileComplete: true
            }
        ];
    }

    async getUserInteractions(userId) {
        // Mock implementation
        return [];
    }

    async checkMutualLike(userId, candidateId) {
        // Mock implementation
        return false;
    }

    async getUserActivity(userId) {
        // Mock implementation
        return {
            responseRate: 0.8,
            lastActive: new Date(),
            averageResponseTime: 2 // hours
        };
    }

    async getUserPopularity(userId) {
        // Mock implementation
        return {
            likesReceived: 150,
            viewsCount: 500,
            matchesCount: 25
        };
    }

    // ===================================
    // CACHE MANAGEMENT
    // ===================================

    clearCache() {
        this.cache.clear();
    }

    clearUserCache(userId) {
        for (const key of this.cache.keys()) {
            if (key.includes(`_${userId}_`)) {
                this.cache.delete(key);
            }
        }
    }
}

// Export for use in other modules
window.MatchAlgorithm = MatchAlgorithm;
