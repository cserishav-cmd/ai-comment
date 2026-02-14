document.addEventListener('DOMContentLoaded', () => {
    // --- State ---
    let currentTab = 'ai';

    // AI State
    let aiMood = 'Romantic';
    let aiLang = 'english';

    // Search State
    let searchMood = 'Romantic';
    let searchLang = 'english';

    // Browse State
    let browseMood = 'Romantic';
    let browseLang = 'english';
    let browseStyle = 'all';
    let browseSort = 'random';
    let browsePage = 1;
    let browseTotalPages = 1;

    // Favorites State
    let favorites = [];
    let currentAIResult = null;

    // --- Elements: Tabs ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const aiSection = document.getElementById('aiSection');
    const searchSection = document.getElementById('searchSection');
    const browseSection = document.getElementById('browseSection');

    // --- Elements: AI Generator ---
    const aiMoodSelect = document.getElementById('aiMoodSelect');
    const aiLangBtns = document.querySelectorAll('.lang-btn.ai-lang');
    const aiContextInput = document.getElementById('aiContextInput');
    const aiGenerateBtn = document.getElementById('aiGenerateBtn');
    const aiResultContainer = document.getElementById('aiResultContainer');
    const aiCommentText = document.getElementById('aiCommentText');
    const aiTagsContainer = document.getElementById('aiTags');
    const aiSourceTag = document.getElementById('sourceTag');
    const aiCopyBtn = document.getElementById('aiCopyBtn');
    const aiFavoriteBtn = document.getElementById('aiFavoriteBtn');

    // --- Elements: Smart Search ---
    const searchMoodSelect = document.getElementById('searchMoodSelect');
    const searchLangBtns = document.querySelectorAll('.lang-btn.search-lang');
    const promptInput = document.getElementById('promptInput');
    const searchBtn = document.getElementById('searchBtn');
    const resultsList = document.getElementById('resultsList');

    // --- Elements: Browse Mode ---
    const browseMoodSelect = document.getElementById('browseMoodSelect');
    const browseLangBtns = document.querySelectorAll('.lang-btn.browse-lang');
    const browseStyleSelect = document.getElementById('browseStyleSelect');
    const browseSortSelect = document.getElementById('browseSortSelect');
    const browseBtn = document.getElementById('browseBtn');
    const browseResultsList = document.getElementById('browseResultsList');
    const favoritesList = document.getElementById('favoritesList');
    const favoritesSection = document.getElementById('favoritesSection');
    const paginationInfo = document.getElementById('paginationInfo');
    const paginationControls = document.getElementById('paginationControls');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageIndicator = document.getElementById('pageIndicator');

    // --- Elements: Global ---
    const globalErrorMessage = document.getElementById('globalErrorMessage');

    // --- Tab Switching Logic ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });

    function switchTab(tab) {
        currentTab = tab;

        tabBtns.forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tab);
        });

        aiSection.classList.add('hidden');
        searchSection.classList.add('hidden');
        browseSection.classList.add('hidden');

        if (tab === 'ai') {
            aiSection.classList.remove('hidden');
        } else if (tab === 'search') {
            searchSection.classList.remove('hidden');
        } else if (tab === 'browse') {
            browseSection.classList.remove('hidden');
            loadBrowseData(); // Load styles and populate moods
        } else if (tab === 'favorites') {
            favoritesSection.classList.remove('hidden');
            renderFavorites();
        }

        globalErrorMessage.classList.add('hidden');
    }

    // --- AI Generator Logic ---

    // Mood Selection (Dropdown)
    aiMoodSelect.addEventListener('change', (e) => {
        aiMood = e.target.value;
    });

    // Language Selection
    aiLangBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            aiLangBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aiLang = btn.dataset.lang;
        });
    });

    aiGenerateBtn.addEventListener('click', async () => {
        const context = aiContextInput.value;
        setLoading(aiGenerateBtn, true);
        hideError();
        aiResultContainer.classList.add('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mood: aiMood,
                    language: aiLang,
                    context: context
                })
            });

            if (!response.ok) throw new Error('Generation failed');
            const data = await response.json();

            // Store current AI result
            currentAIResult = {
                comment: data.comment,
                mood: data.mood,
                style: data.style,
                source: 'AI',
                id: Date.now().toString() // Simple ID
            };

            aiCommentText.textContent = `"${data.comment}"`;
            aiSourceTag.textContent = data.source;

            // Render Tags
            aiTagsContainer.innerHTML = '';
            if (data.mood) {
                const moodTag = document.createElement('span');
                moodTag.className = 'tag tag-mood';
                moodTag.textContent = data.mood;
                aiTagsContainer.appendChild(moodTag);
            }
            if (data.style) {
                const styleTag = document.createElement('span');
                styleTag.className = 'tag tag-style';
                styleTag.textContent = data.style;
                aiTagsContainer.appendChild(styleTag);
            }

            // Update Favorite Button State
            updateFavoriteBtnState(aiFavoriteBtn, currentAIResult.comment);

            aiResultContainer.classList.remove('hidden');

        } catch (error) {
            console.error(error);
            showError('Failed to generate comment. Please try again.');
        } finally {
            setLoading(aiGenerateBtn, false);
            fetchUsageStats(); // Update usage counter after generation
        }
    });

    aiFavoriteBtn.addEventListener('click', () => {
        if (currentAIResult) {
            toggleFavorite(currentAIResult, aiFavoriteBtn);
        }
    });

    aiCopyBtn.addEventListener('click', () => {
        copyToClipboard(aiCommentText.textContent.replace(/^"|"$/g, ''), aiCopyBtn);
    });

    // --- Smart Search Logic ---

    // Search Mood Selection (Dropdown)
    searchMoodSelect.addEventListener('change', (e) => {
        searchMood = e.target.value;
    });

    // Search Language Selection
    searchLangBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            searchLangBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            searchLang = btn.dataset.lang;
        });
    });

    searchBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();

        setLoading(searchBtn, true);
        hideError();
        resultsList.classList.add('hidden');
        resultsList.innerHTML = '';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    mood: searchMood,
                    language: searchLang
                })
            });

            if (!response.ok) throw new Error('Search failed');
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                data.results.forEach(result => {
                    let commentText = '';
                    let itemMood = searchMood;

                    if (typeof result === 'string') {
                        commentText = result;
                    } else {
                        commentText = result.comment;
                        if (result.mood) itemMood = result.mood;
                    }

                    const item = {
                        comment: commentText,
                        mood: itemMood,
                        style: 'Smart Search',
                        source: 'Search'
                    };
                    const card = createResultCard(item);
                    resultsList.appendChild(card);
                });
                resultsList.classList.remove('hidden');
            } else {
                showError('No comments found. Try changing filters.');
            }

        } catch (error) {
            showError('Failed to search comments. Please try again.');
        } finally {
            setLoading(searchBtn, false);
        }
    });

    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBtn.click();
    });

    // --- Browse Mode Logic ---

    async function loadBrowseData() {
        // Load styles from API
        try {
            const response = await fetch('/api/styles');
            const data = await response.json();
            populateStyleSelect(data.styles || []);
        } catch (error) {
            console.error('Failed to load styles:', error);
        }

        // Populate mood select with all moods (same as AI/Search)
        populateBrowseMoodSelect();
    }

    function populateStyleSelect(styles) {
        browseStyleSelect.innerHTML = '<option value="all">All Styles</option>';
        styles.forEach(style => {
            const option = document.createElement('option');
            option.value = style;
            option.textContent = style;
            browseStyleSelect.appendChild(option);
        });
    }

    function populateBrowseMoodSelect() {
        // Copy all moods from aiMoodSelect
        const moods = Array.from(aiMoodSelect.options).map(opt => opt.value);
        browseMoodSelect.innerHTML = '';
        moods.forEach(mood => {
            const option = document.createElement('option');
            option.value = mood;
            option.textContent = mood;
            browseMoodSelect.appendChild(option);
        });
    }

    // Browse Language Selection
    browseLangBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            browseLangBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            browseLang = btn.dataset.lang;
        });
    });

    // Browse Mood Selection
    browseMoodSelect.addEventListener('change', (e) => {
        browseMood = e.target.value;
    });

    // Browse Style Selection
    browseStyleSelect.addEventListener('change', (e) => {
        browseStyle = e.target.value;
    });

    // Browse Sort Selection
    browseSortSelect.addEventListener('change', (e) => {
        browseSort = e.target.value;
    });

    // Browse Button Click
    browseBtn.addEventListener('click', async () => {
        browsePage = 1; // Reset to page 1
        await loadBrowseResults();
    });

    // Pagination Buttons
    prevPageBtn.addEventListener('click', async () => {
        if (browsePage > 1) {
            browsePage--;
            await loadBrowseResults();
        }
    });

    nextPageBtn.addEventListener('click', async () => {
        if (browsePage < browseTotalPages) {
            browsePage++;
            await loadBrowseResults();
        }
    });

    async function loadBrowseResults() {
        setLoading(browseBtn, true);
        hideError();
        browseResultsList.classList.add('hidden');
        browseResultsList.innerHTML = '';
        paginationControls.classList.add('hidden');
        paginationInfo.classList.add('hidden');

        try {
            const response = await fetch('/api/browse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    language: browseLang,
                    mood: browseMood,
                    style: browseStyle,
                    page: browsePage,
                    page_size: 10,
                    sort: browseSort
                })
            });

            if (!response.ok) throw new Error('Browse failed');
            const data = await response.json();

            if (data.comments && data.comments.length > 0) {
                data.comments.forEach(obj => {
                    // Check if obj is string or object (API might return list of strings or list of objects)
                    // If backend returns list of strings for browsing, we use current filters.
                    // If backend returns objects, we use them.

                    let commentText = '';
                    let itemMood = browseMood;
                    let itemStyle = browseStyle !== 'all' ? browseStyle : 'General';

                    if (typeof obj === 'string') {
                        commentText = obj;
                    } else {
                        commentText = obj.comment;
                        if (obj.mood) itemMood = obj.mood;
                        if (obj.style) itemStyle = obj.style;
                    }

                    const item = {
                        comment: commentText,
                        mood: itemMood,
                        style: itemStyle,
                        source: 'Browse'
                    };
                    const card = createResultCard(item);
                    browseResultsList.appendChild(card);
                });
                browseResultsList.classList.remove('hidden');

                // Update pagination
                browseTotalPages = data.total_pages;
                pageIndicator.textContent = `Page ${data.page} of ${data.total_pages}`;
                paginationInfo.textContent = `Showing ${data.comments.length} of ${data.total} results`;
                paginationInfo.classList.remove('hidden');
                paginationControls.classList.remove('hidden');

                // Enable/disable pagination buttons
                prevPageBtn.disabled = browsePage <= 1;
                nextPageBtn.disabled = browsePage >= browseTotalPages;
            } else {
                showError('No comments found for this combination.');
            }

        } catch (error) {
            showError('Failed to browse comments. Please try again.');
        } finally {
            setLoading(browseBtn, false);
        }
    }

    // --- Helpers ---

    // --- Favorites Logic ---

    function loadFavorites() {
        try {
            const stored = localStorage.getItem('starmaker_favorites');
            if (stored) {
                const parsed = JSON.parse(stored);
                // Migrate legacy data (strings) to objects
                favorites = parsed.map(item => {
                    if (typeof item === 'string') {
                        return {
                            comment: item,
                            mood: 'Saved',
                            style: 'General',
                            source: 'Legacy',
                            id: Date.now().toString() + Math.random()
                        };
                    }
                    return item;
                });
                console.log('Loaded favorites:', favorites);
            }
        } catch (e) {
            console.error('Error loading favorites:', e);
            favorites = [];
        }
    }

    function saveFavorites() {
        localStorage.setItem('starmaker_favorites', JSON.stringify(favorites));
        console.log('Saved favorites:', favorites);
    }

    function toggleFavorite(item, btnElement) {
        console.log('Toggling favorite for:', item);
        const index = favorites.findIndex(f => f.comment === item.comment);

        if (index === -1) {
            // Add to favorites
            // Ensure we copy the object to avoid reference issues
            const newItem = {
                comment: item.comment,
                mood: item.mood || 'Saved',
                style: item.style || 'General',
                source: item.source || 'Unknown',
                id: item.id || Date.now().toString()
            };
            favorites.push(newItem);
            btnElement.classList.add('active');
            const svg = btnElement.querySelector('svg');
            if (svg) svg.style.fill = '#e91e63';
        } else {
            // Remove from favorites
            favorites.splice(index, 1);
            btnElement.classList.remove('active');
            const svg = btnElement.querySelector('svg');
            if (svg) svg.style.fill = 'none';

            // If we are currently ON the favorites tab, re-render immediately
            if (currentTab === 'favorites') {
                renderFavorites();
            }
        }
        saveFavorites();
    }

    function updateFavoriteBtnState(btnElement, commentText) {
        const isFav = favorites.some(f => f.comment === commentText);
        const svg = btnElement.querySelector('svg');
        if (isFav) {
            btnElement.classList.add('active');
            if (svg) svg.style.fill = '#e91e63';
        } else {
            btnElement.classList.remove('active');
            if (svg) svg.style.fill = 'none';
        }
    }

    function renderFavorites() {
        favoritesList.innerHTML = '';
        if (favorites.length === 0) {
            favoritesList.innerHTML = '<p class="description">No favorites yet. Start exploring and save some comments!</p>';
            return;
        }

        favorites.forEach(item => {
            const card = createResultCard(item);
            favoritesList.appendChild(card);
        });
    }

    // --- Helpers ---

    function createResultCard(item) {
        // item can be an object {comment, mood, style, source}
        const text = item.comment || item;
        const mood = item.mood || '';
        const style = item.style || '';

        const div = document.createElement('div');
        div.className = 'result-card';

        // Tags HTML
        let tagsHtml = '';
        if (mood || style) {
            tagsHtml = '<div class="tags-container" style="flex-basis: 100%; margin-bottom: 0.5rem;">';
            if (mood) tagsHtml += `<span class="tag tag-mood">${mood}</span>`;
            if (style) tagsHtml += `<span class="tag tag-style">${style}</span>`;
            tagsHtml += '</div>';
        }

        div.innerHTML = `
            ${tagsHtml}
            <p class="comment-text">"${text}"</p>
            <div style="display: flex; gap: 0.5rem; flex-shrink: 0;">
                <button class="icon-btn favorite-btn" title="Toggle Favorite">
                     <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </button>
                <button class="icon-btn copy-btn" title="Copy to clipboard">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                </button>
            </div>
        `;

        // Copy Event
        const copyBtn = div.querySelector('.copy-btn');
        copyBtn.addEventListener('click', () => copyToClipboard(text, copyBtn));

        // Favorite Event
        const favBtn = div.querySelector('.favorite-btn');
        const dataItem = typeof item === 'string' ? { comment: item } : item;

        updateFavoriteBtnState(favBtn, text);

        favBtn.addEventListener('click', () => {
            toggleFavorite(dataItem, favBtn);
        });

        return div;
    }

    function copyToClipboard(text, btnElement) {
        navigator.clipboard.writeText(text).then(() => {
            const originalHTML = btnElement.innerHTML;
            btnElement.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-success"><polyline points="20 6 9 17 4 12"></polyline></svg>';
            btnElement.classList.add('text-success');
            setTimeout(() => {
                btnElement.innerHTML = originalHTML;
                btnElement.classList.remove('text-success');
            }, 2000);
        });
    }

    function setLoading(btn, isLoading) {
        btn.disabled = isLoading;
        btn.classList.toggle('loading', isLoading);
    }

    function showError(msg) {
        globalErrorMessage.textContent = msg;
        globalErrorMessage.classList.remove('hidden');
    }

    function hideError() {
        globalErrorMessage.classList.add('hidden');
    }

    // ====== Usage Stats ======
    const usageText = document.getElementById('usageText');
    const usageBar = document.getElementById('usageBar');
    const usageUsed = document.getElementById('usageUsed');
    const usageRemaining = document.getElementById('usageRemaining');

    async function fetchUsageStats() {
        try {
            const response = await fetch('/api/usage');
            const data = await response.json();

            const remaining = data.remaining;
            const total = data.total;
            const used = data.used;
            const percentage = ((remaining / total) * 100);

            // Update badge text
            usageText.textContent = `${remaining}/${total}`;

            // Update tooltip details
            usageUsed.textContent = used;
            usageRemaining.textContent = remaining;

            // Update progress bar
            usageBar.style.width = percentage + '%';
            usageBar.className = 'usage-bar';

            if (percentage <= 20) {
                usageBar.classList.add('low');
            } else if (percentage <= 50) {
                usageBar.classList.add('medium');
            }
        } catch (error) {
            console.error('Failed to fetch usage stats:', error);
        }
    }

    // Fetch usage stats on page load
    fetchUsageStats();
    loadFavorites(); // Load favorites on startup

    // Usage Badge Toggle (Tap System)
    const usageBadge = document.getElementById('usageBadge');
    if (usageBadge) {
        usageBadge.addEventListener('click', () => {
            usageBadge.classList.toggle('active');
        });
    }
});
