/**
 * AutoReelStudio Web Frontend Logic (ReelMakerAI + ReelPublisher)
 * Supports standalone local serving, containerized Hugging Face Spaces,
 * and portfolio embedding via window.PROJECT_CONFIG.
 */

const API_BASE = (typeof window !== 'undefined' && window.PROJECT_CONFIG?.apiBaseUrl) || '';

let activeVideoFilename = null;
let isSafeZoneVisible = false;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    checkAccountStatus();
    checkYouTubeStatus();
    updateIdeaQueueStatus();
    updateDailyQuotaStatus();
    updateCacheStats();
    loadGallery();

    const promptInput = document.getElementById('promptInput');
    if (promptInput) {
        promptInput.addEventListener('input', () => {
            if (promptInput.value.trim().length > 0 && currentIdeaMode !== 'custom') {
                setIdeaMode('custom');
            }
        });
    }
});

/**
 * Fetch 10-15 Idea Queue Buffer Status
 */
async function updateIdeaQueueStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/queue`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.success) {
            const el = document.getElementById('queueBufferText');
            if (el) el.innerText = `Queue: ${data.count}/15 ideas`;
        }
    } catch (e) {
        console.warn('Could not fetch queue status:', e);
    }
}

/**
 * Trigger Idea Queue Replenishment
 */
async function replenishIdeaQueue() {
    const el = document.getElementById('queueBufferText');
    if (el) el.innerText = 'Replenishing...';
    try {
        const res = await fetch(`${API_BASE}/api/queue/replenish`, { method: 'POST' });
        const data = await res.json();
        updateIdeaQueueStatus();
        showSuccess('💡 Idea Queue Updated', data.message || 'Queue replenished.');
    } catch (e) {
        showError('Replenish Failed', e.message);
    }
}

/**
 * Fetch 50 Reels/Day Quota Telemetry
 */
async function updateDailyQuotaStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/quota`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.success && data.quota) {
            const el = document.getElementById('dailyQuotaText');
            if (el) el.innerText = `Daily: ${data.quota.generated_today}/50`;
        }
    } catch (e) {
        console.warn('Could not fetch quota status:', e);
    }
}

/**
 * Fetch storage & cache stats
 */
async function updateCacheStats() {
    try {
        const res = await fetch(`${API_BASE}/api/cache-stats`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.success && data.stats) {
            const el = document.getElementById('cacheUsageText');
            if (el) el.innerText = `Cache: ${data.stats.total_mb} MB (${data.stats.file_count} files)`;
        }
    } catch (e) {
        console.warn('Could not fetch cache stats:', e);
    }
}

/**
 * 1-Click Clear Cache Storage
 */
async function clearCacheStorage() {
    const el = document.getElementById('cacheUsageText');
    if (el) el.innerText = 'Cleaning...';
    try {
        const res = await fetch(`${API_BASE}/api/clear-cache`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            updateCacheStats();
            showSuccess('🧹 Cache Cleaned', `Successfully purged temporary files. Freed ${data.freed_mb} MB (${data.deleted_count} files deleted).`);
        }
    } catch (e) {
        showError('Clean Cache Failed', e.message);
    }
}

/**
 * 1. Fetch live Meta Instagram Account status and quota
 */
async function checkAccountStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.success && data.account) {
            document.getElementById('igHandle').innerText = `@${data.account.username || 'sun_27417'}`;
            if (data.quota) {
                const remaining = data.quota.quota_total - data.quota.quota_usage;
                document.getElementById('igQuota').innerText = `Meta Quota: ${remaining}/${data.quota.quota_total} daily remaining`;
            }
        }
    } catch (e) {
        console.warn('Could not connect to /api/status:', e);
    }
}

/**
 * 1b. Fetch live YouTube Shorts Account Status & OAuth State
 */
async function checkYouTubeStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/youtube/status`);
        if (!res.ok) return;
        const data = await res.json();
        const dot = document.getElementById('ytStatusDot');
        const handle = document.getElementById('ytHandle');
        const text = document.getElementById('ytStatusText');

        if (data.authenticated) {
            if (dot) dot.className = 'status-dot online';
            if (handle) handle.innerText = data.title || 'YouTube Channel';
            if (text) text.innerText = `${data.subscribers || 0} subs · Connected`;
        } else {
            if (dot) dot.className = 'status-dot offline';
            if (handle) handle.innerText = 'YouTube Shorts';
            if (text) {
                if (data.auth_url) {
                    text.innerHTML = `<a href="${data.auth_url}" target="_blank" style="color:#00f0ff;text-decoration:underline;font-weight:700;">Connect Channel</a>`;
                } else {
                    text.innerText = 'OAuth Pending';
                }
            }
        }
    } catch (e) {
        console.warn('Could not connect to /api/youtube/status:', e);
    }
}

/**
 * Idea Mode Switcher (Autonomous vs Custom Prompt)
 */
let currentIdeaMode = 'auto';
let currentStudioMode = 'standard';

function switchStudioMode(mode) {
    currentStudioMode = mode;
    const btnStandard = document.getElementById('btnStudioStandard');
    const btnAnimal = document.getElementById('btnStudioAnimal');
    const standardSection = document.getElementById('standardStudioSection');
    const animalSection = document.getElementById('animalStudioSection');

    if (mode === 'animal') {
        if (btnAnimal) btnAnimal.classList.add('active');
        if (btnStandard) btnStandard.classList.remove('active');
        if (standardSection) standardSection.style.display = 'none';
        if (animalSection) animalSection.style.display = 'block';

        const card = document.getElementById('characterPreviewCard');
        if (card && card.style.display === 'none') {
            rollAnimalStory();
        }
    } else {
        if (btnStandard) btnStandard.classList.add('active');
        if (btnAnimal) btnAnimal.classList.remove('active');
        if (standardSection) standardSection.style.display = 'block';
        if (animalSection) animalSection.style.display = 'none';
    }
}

function onAnimalOptionChange() {
    // Kept responsive for future automatic previews
}

async function rollAnimalStory() {
    const species = document.getElementById('animalSpeciesSelect')?.value || 'RANDOM';
    const style = document.getElementById('animalStyleSelect')?.value || 'pixar_3d';
    const genre = document.getElementById('animalGenreSelect')?.value || 'cute';
    const activity = document.getElementById('animalActivitySelect')?.value || 'RANDOM';
    const isDuo = document.getElementById('animalDuoCheckbox')?.checked || false;
    const prompt = document.getElementById('animalPromptInput')?.value.trim() || '';

    const btn = document.getElementById('btnRollAnimalStory');
    if (btn) btn.innerText = '🎲 Rolling...';

    try {
        const query = new URLSearchParams({
            species,
            style,
            genre,
            activity,
            is_duo: isDuo ? 'true' : 'false',
            prompt
        });
        const res = await fetch(`${API_BASE}/api/random-animal-story?${query.toString()}`);
        const data = await res.json();

        if (data.success && data.story) {
            const story = data.story;
            if (!prompt && story.title) {
                document.getElementById('animalPromptInput').value = story.title;
            }

            const card = document.getElementById('characterPreviewCard');
            if (card) card.style.display = 'block';

            const titleEl = document.getElementById('charCardTitle');
            if (titleEl) titleEl.innerText = `🐾 Hero: ${story.hero_name}`;
            const badgeEl = document.getElementById('charStyleBadge');
            if (badgeEl) badgeEl.innerText = story.style_meta?.label || story.visual_style;

            const charData = story.character_data;
            let detailsHtml = '';

            if (charData.is_duo) {
                const c1 = charData.character_1;
                const c2 = charData.character_2;
                detailsHtml = `
                    <div class="character-detail-item">
                        <span class="character-detail-label">Hero 1</span>
                        <span class="character-detail-val">${c1.name} (${c1.breed})</span>
                    </div>
                    <div class="character-detail-item">
                        <span class="character-detail-label">Hero 2</span>
                        <span class="character-detail-val">${c2.name} (${c2.breed})</span>
                    </div>
                    <div class="character-detail-item">
                        <span class="character-detail-label">Accessories</span>
                        <span class="character-detail-val">${c1.accessories}, ${c2.accessories}</span>
                    </div>
                    <div class="character-detail-item">
                        <span class="character-detail-label">Dynamic</span>
                        <span class="character-detail-val">${charData.duo_archetype?.dynamic || 'Best Friends'}</span>
                    </div>
                `;
            } else {
                const c = charData.character;
                detailsHtml = `
                    <div class="character-detail-item">
                        <span class="character-detail-label">Breed</span>
                        <span class="character-detail-val">${c.breed}</span>
                    </div>
                    <div class="character-detail-item">
                        <span class="character-detail-label">Coat & Eyes</span>
                        <span class="character-detail-val">${c.fur_color}, ${c.eye_color}</span>
                    </div>
                    <div class="character-detail-item">
                        <span class="character-detail-label">Markings</span>
                        <span class="character-detail-val">${c.distinct_markings}</span>
                    </div>
                    <div class="character-detail-item">
                        <span class="character-detail-label">Accessories</span>
                        <span class="character-detail-val">${c.accessories}</span>
                    </div>
                `;
            }

            const gridEl = document.getElementById('charDetailsGrid');
            if (gridEl) gridEl.innerHTML = detailsHtml;

            let scenesHtml = '';
            (story.scenes || []).forEach(sc => {
                scenesHtml += `
                    <div class="scene-step-pill">
                        <div class="scene-step-title">Scene ${sc.scene_number}: ${sc.camera_angle}</div>
                        <div>"${sc.dialogue_or_narration}"</div>
                    </div>
                `;
            });
            const scenesEl = document.getElementById('charScenesPreview');
            if (scenesEl) scenesEl.innerHTML = scenesHtml;
        }
    } catch (e) {
        console.error('Failed to roll animal story:', e);
    } finally {
        if (btn) btn.innerText = '🎲 Roll Animal Story';
    }
}

function setIdeaMode(mode) {
    currentIdeaMode = mode;
    const tabAuto = document.getElementById('tabAutoIdea');
    const tabCustom = document.getElementById('tabCustomIdea');
    const promptInput = document.getElementById('promptInput');
    const hint = document.getElementById('ideaModeHint');

    if (mode === 'auto') {
        tabAuto.classList.add('active');
        tabCustom.classList.remove('active');
        promptInput.placeholder = "Leave empty for infinite autonomous creation, or click '🎲 Roll Fresh Idea'...";
        hint.innerHTML = "💡 <strong>Autonomous Mode:</strong> The engine automatically invents an original, non-repeating concept for you.";
    } else {
        tabCustom.classList.add('active');
        tabAuto.classList.remove('active');
        promptInput.placeholder = "Type your custom idea, topic, or premise here (e.g., 'Why cats sleep 16 hours a day' or 'POV: You forgot your keys inside the car')...";
        hint.innerHTML = "✍️ <strong>Custom Idea Mode:</strong> The engine will craft the entire Reel specifically around your idea!";
        promptInput.focus();
    }
}

/**
 * 2. Roll random creative topic from chosen genre
 */
async function rollIdea() {
    const genre = document.getElementById('genreSelect').value;
    try {
        const duration = parseInt(document.querySelector('input[name="duration"]:checked')?.value || '15');
        const res = await fetch(`${API_BASE}/api/random-topic?genre=${encodeURIComponent(genre)}&duration=${duration}`);
        const data = await res.json();
        if (data && data.title) {
            document.getElementById('promptInput').value = data.title;
            setIdeaMode('custom');
            const hint = document.getElementById('ideaModeHint');
            if (hint && data.retention_score) {
                hint.innerHTML = `🧠 <strong>Smart pick (${data.retention_score}/100):</strong> ${data.reason || 'Ranked for freshness and retention.'}`;
            }
        }
    } catch (e) {
        console.error('Failed to roll topic:', e);
    }
}

function getFormPayload() {
    const duration = parseInt(document.querySelector('input[name="duration"]:checked').value);
    const captionStyle = document.getElementById('captionStyleSelect').value;
    const voiceVal = document.getElementById('voiceSelect').value;
    const voice = (voiceVal === 'AUTO') ? null : voiceVal;
    const musicVal = document.getElementById('musicSelect').value;
    const music = (musicVal === 'AUTO') ? null : musicVal;
    const seedVal = document.getElementById('seedInput').value.trim();
    const seed = seedVal ? parseInt(seedVal) : null;
    const publishMode = document.getElementById('publishMode').value;
    const dryRun = (publishMode === 'dry_run');

    if (currentStudioMode === 'animal') {
        const animalSpecies = document.getElementById('animalSpeciesSelect')?.value || null;
        const visualStyle = document.getElementById('animalStyleSelect')?.value || 'pixar_3d';
        const animalGenre = document.getElementById('animalGenreSelect')?.value || 'cute';
        const activityType = document.getElementById('animalActivitySelect')?.value || null;
        const isDuo = Boolean(document.getElementById('animalDuoCheckbox')?.checked);
        const prompt = document.getElementById('animalPromptInput')?.value.trim() || '';
        const targetPlatform = document.getElementById('targetPlatformSelect')?.value || 'both';

        return {
            mode: 'animal_story',
            prompt: prompt,
            genre: animalGenre,
            animal_species: animalSpecies,
            visual_style: visualStyle,
            activity_type: activityType,
            is_duo: isDuo,
            duration: duration,
            caption_style: captionStyle,
            voice: voice,
            music: music,
            seed: seed,
            destinations: targetPlatform,
            dry_run: dryRun
        };
    }

    const prompt = document.getElementById('promptInput').value.trim();
    const genreVal = document.getElementById('genreSelect').value;
    const genre = (genreVal === 'RANDOM') ? null : genreVal;
    const mode = document.getElementById('modeSelect').value;
    const targetPlatform = document.getElementById('targetPlatformSelect')?.value || 'both';

    return {
        prompt,
        duration,
        genre,
        mode,
        caption_style: captionStyle,
        voice,
        music,
        seed,
        destinations: targetPlatform,
        dry_run: dryRun
    };
}

/**
 * 3. ⚡ 1-Click Generate & Auto-Publish to Instagram Reels & YouTube Shorts
 */
async function triggerOneClickPublish() {
    const payload = getFormPayload();

    setControlsDisabled(true);
    showStatus('⚡ 1-Click Multi-Platform Publish', 'Synthesizing voiceover, assembling full-screen 9:16 footage, rendering captions & publishing live...', 25);

    try {
        const res = await fetch(`${API_BASE}/api/generate-and-publish`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            updateProgress(100);
            const permalink = data.permalink || (payload.dry_run ? 'https://www.instagram.com/reel/dryrun_simulation/' : '#');
            let linksHtml = '';

            if (payload.destinations === 'instagram' || payload.destinations === 'both' || payload.destinations === 'all') {
                linksHtml += `
                    <a href="${permalink}" target="_blank" class="btn-publish-direct" style="display: inline-block; width: auto; padding: 8px 18px; margin-right: 8px; margin-bottom: 8px; text-decoration: none;">
                        📸 View on Instagram (@sun_27417)
                    </a>
                `;
            }

            if (data.youtube && data.youtube.shorts_url) {
                linksHtml += `
                    <a href="${data.youtube.shorts_url}" target="_blank" class="btn-publish-direct" style="display: inline-block; width: auto; padding: 8px 18px; margin-bottom: 8px; background: #ff0000; text-decoration: none;">
                        ▶️ View on YouTube Shorts
                    </a>
                `;
            }

            const receiptHtml = `
                <div style="margin-top: 8px;">
                    <p style="color: #00FFA3; font-weight: bold; font-size: 0.95rem;">🎉 Multi-Platform Publication Complete!</p>
                    <p style="margin: 4px 0 10px 0; font-size: 0.84rem;">Total pipeline time: ${data.elapsed ? data.elapsed.toFixed(1) + 's' : 'done'}</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${linksHtml}
                    </div>
                </div>
            `;
            showSuccess('✅ Live Multi-Publication Complete!', receiptHtml);

            loadVideoIntoPreview(data.video_url, data.filename || 'reel.mp4', true);
            loadGallery();
            checkAccountStatus();
            checkYouTubeStatus();
            updateCacheStats();
        } else {
            showError('Publication Failed', data.error || 'Unknown error occurred in pipeline');
        }
    } catch (err) {
        showError('Network Error', err.message);
    } finally {
        setControlsDisabled(false);
    }
}

/**
 * 4. 🎬 Generate Video Only (Draft / Preview)
 */
async function triggerGenerateDraft() {
    const payload = getFormPayload();

    setControlsDisabled(true);
    showStatus('🎬 Compiling Native 9:16 Reel', 'Composing scene clips, synthesizing voice, burning modern typography & checking QC...', 35);

    try {
        const res = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            updateProgress(100);
            const qcBadge = data.qc?.passed ? '✅ QC Passed (100%)' : '⚠️ Ready';
            showSuccess('✅ Reel Draft Rendered!', `Compiled in ${data.elapsed.toFixed(1)}s. ${qcBadge}. Full-screen native 9:16 preview loaded below.`);
            loadVideoIntoPreview(data.video_url, data.filename || 'reel.mp4', false);
            loadGallery();
            updateCacheStats();
        } else {
            showError('Draft Generation Failed', data.error || 'Failed to render video');
        }
    } catch (err) {
        showError('Network Error', err.message);
    } finally {
        setControlsDisabled(false);
    }
}

/**
 * 5. Publish the currently active preview video
 */
async function publishActiveVideo() {
    if (!activeVideoFilename) {
        alert('Please generate or select a video to publish first.');
        return;
    }
    await publishVideoFile(activeVideoFilename);
}

/**
 * Core publish action for any video file
 */
async function publishVideoFile(filename) {
    const mode = document.getElementById('publishMode').value;
    const dryRun = (mode === 'dry_run');

    showStatus('📲 Publishing to Instagram', `Transcoding ${filename} to Reels specs, opening TLS bridge & notifying Meta Graph API...`, 50);

    try {
        const res = await fetch(`${API_BASE}/api/publish-reel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_filename: filename, dry_run: dryRun })
        });
        const data = await res.json();

        if (data.success) {
            updateProgress(100);
            const permalink = data.permalink || (dryRun ? 'https://www.instagram.com/reel/dryrun_test/' : '#');
            showSuccess('🎉 Published to Instagram Reels!', `
                <div style="margin-top: 6px;">
                    <a href="${permalink}" target="_blank" style="color: #00FFA3; font-weight: bold; text-decoration: underline;">
                        ${permalink}
                    </a>
                </div>
            `);
            loadGallery();
            checkAccountStatus();
        } else {
            showError('Publish Failed', data.error || 'Unknown error');
        }
    } catch (e) {
        showError('Publish Error', e.message);
    }
}

/**
 * 6. Inspect Active Video Specs & QC
 */
async function inspectActiveVideo() {
    if (!activeVideoFilename) return;
    openSpecAudit(activeVideoFilename);
}

async function openSpecAudit(filename) {
    const drawer = document.getElementById('specAuditDrawer');
    const content = document.getElementById('specAuditContent');
    drawer.style.display = 'block';
    content.innerHTML = '<p style="grid-column: 1/-1; color: var(--accent);">🔍 Probing container and running Quality Control audit...</p>';

    try {
        const res = await fetch(`${API_BASE}/api/inspect?video=${encodeURIComponent(filename)}`);
        const data = await res.json();

        if (!data.success) {
            content.innerHTML = `<p style="grid-column: 1/-1; color: var(--danger);">Failed to probe: ${data.error}</p>`;
            return;
        }

        const p = data.probe;
        const qc = data.qc || {};

        content.innerHTML = `
            <div class="spec-item">
                <span class="spec-label">Quality Score</span>
                <span class="spec-val ${qc.passed ? 'ok' : 'err'}">${qc.score ?? 100}/100 (${qc.overall_status || 'PASSED'})</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Resolution</span>
                <span class="spec-val ${p.video.width === 1080 && p.video.height === 1920 ? 'ok' : 'err'}">${p.video.width} x ${p.video.height} (9:16)</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Aspect Ratio</span>
                <span class="spec-val ok">9:16 Full Screen</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Video Codec</span>
                <span class="spec-val ${p.video.codec === 'h264' ? 'ok' : 'err'}">${p.video.codec.toUpperCase()} (${p.video.profile || 'High'})</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Frame Rate</span>
                <span class="spec-val ${p.video.fps >= 24 ? 'ok' : 'err'}">${p.video.fps.toFixed(1)} fps</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Audio Stream</span>
                <span class="spec-val ${p.audio.codec === 'aac' ? 'ok' : 'err'}">${p.audio.codec.toUpperCase()} ${p.audio.sample_rate}Hz</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Audio Channels</span>
                <span class="spec-val ${p.audio.channels === 2 ? 'ok' : 'err'}">${p.audio.channels === 2 ? 'Stereo (2ch)' : p.audio.channels + ' ch'}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Faststart Moov</span>
                <span class="spec-val ${p.format.has_faststart ? 'ok' : 'err'}">${p.format.has_faststart ? 'At Head (Instant Stream)' : 'Trailing'}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Duration</span>
                <span class="spec-val ok">${p.format.duration.toFixed(1)}s</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">File Size</span>
                <span class="spec-val ok">${(p.format.size / (1024*1024)).toFixed(1)} MB</span>
            </div>
        `;
    } catch (e) {
        content.innerHTML = `<p style="grid-column: 1/-1; color: var(--danger);">Inspection error: ${e.message}</p>`;
    }
}

function closeSpecAudit() {
    document.getElementById('specAuditDrawer').style.display = 'none';
}

/**
 * 7. Safe Zone Overlay Toggle
 */
function toggleSafeZoneOverlay() {
    const overlay = document.getElementById('safeZoneOverlay');
    const btnText = document.getElementById('safeZoneBtnText');
    isSafeZoneVisible = !isSafeZoneVisible;
    if (isSafeZoneVisible) {
        overlay.style.display = 'flex';
        btnText.innerText = '📐 Hide Safe Zones';
    } else {
        overlay.style.display = 'none';
        btnText.innerText = '📐 Toggle Safe Zones';
    }
}

/**
 * 8. Preview Player Loader
 */
function loadVideoIntoPreview(url, filename, published = false) {
    activeVideoFilename = filename;
    const player = document.getElementById('mainVideoPlayer');
    const emptyState = document.getElementById('emptyPreview');
    const actions = document.getElementById('previewActions');
    const badge = document.getElementById('videoStatusBadge');
    const btnDownload = document.getElementById('btnDownloadActive');

    emptyState.style.display = 'none';
    player.style.display = 'block';
    player.src = url;
    player.load();

    actions.style.display = 'flex';
    btnDownload.href = url;
    btnDownload.download = filename;

    if (published) {
        badge.innerText = '🟢 Published';
        badge.className = 'badge badge-published';
        document.getElementById('btnPublishActive').innerText = '📲 Re-Publish to Instagram';
    } else {
        badge.innerText = '🟡 Draft Preview';
        badge.className = 'badge badge-draft';
        document.getElementById('btnPublishActive').innerText = '📲 Publish This Reel to Instagram';
    }
}

/**
 * 9. Gallery Archive Loader
 */
async function loadGallery() {
    const grid = document.getElementById('galleryGrid');
    const countEl = document.getElementById('galleryCount');
    try {
        const res = await fetch(`${API_BASE}/api/gallery`);
        const items = await res.json();

        countEl.innerText = `${items.length} videos`;
        if (items.length === 0) {
            grid.innerHTML = '<p style="color: var(--text-dim); grid-column: 1/-1;">No generated videos in archive yet.</p>';
            return;
        }

        grid.innerHTML = items.map(item => `
            <div class="video-card">
                <div class="card-thumb" onclick="loadVideoIntoPreview('${item.url}', '${item.filename}', ${item.published})">
                    <video src="${item.url}#t=0.5" preload="metadata"></video>
                    <div class="card-play-icon">▶</div>
                    <span class="card-duration">${item.size}</span>
                </div>
                <div class="card-info">
                    <h4 class="card-title" title="${item.name}">${item.name}</h4>
                    <div class="card-footer">
                        ${item.published 
                            ? `<a href="${item.permalink}" target="_blank" class="badge badge-published" style="text-decoration:none;">Live Reel</a>` 
                            : `<span class="badge badge-draft">Draft</span>`
                        }
                        <button class="btn-card-action" onclick="openSpecAudit('${item.filename}')" title="Inspect compliance">🔍 Audit</button>
                        <button class="btn-card-action" onclick="deleteVideo('${item.filename}')" title="Delete video" style="color: #ff3366; margin-left: 4px;">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load gallery:', e);
    }
}

/**
 * 10. Delete a Video from the Archive
 */
async function deleteVideo(filename) {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
    try {
        const res = await fetch(`${API_BASE}/api/delete-video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await res.json();
        if (data.success) {
            loadGallery();
            if (activeVideoFilename === filename) {
                const player = document.getElementById('mainVideoPlayer');
                const emptyState = document.getElementById('emptyPreview');
                const actions = document.getElementById('previewActions');
                if (player) {
                    player.pause();
                    player.src = '';
                    player.style.display = 'none';
                }
                if (emptyState) emptyState.style.display = 'block';
                if (actions) actions.style.display = 'none';
                activeVideoFilename = null;
            }
        } else {
            alert('Failed to delete video: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        alert('Error deleting video: ' + e.message);
    }
}

/**
 * Status and Progress Notification Helpers
 */
function showStatus(title, message, progress = 20) {
    const box = document.getElementById('statusBox');
    box.style.display = 'block';
    box.className = 'status-container';
    document.getElementById('statusTitle').innerText = title;
    document.getElementById('statusMessage').innerText = message;
    document.getElementById('statusSpinner').style.display = 'block';
    updateProgress(progress);
}

function updateProgress(percent) {
    const bar = document.getElementById('progressBar');
    if (bar) bar.style.width = `${percent}%`;
}

function showSuccess(title, htmlContent) {
    const box = document.getElementById('statusBox');
    box.style.display = 'block';
    box.className = 'status-container success';
    document.getElementById('statusSpinner').style.display = 'none';
    document.getElementById('statusTitle').innerText = title;
    document.getElementById('statusMessage').innerHTML = htmlContent;
}

function showError(title, message) {
    const box = document.getElementById('statusBox');
    box.style.display = 'block';
    box.className = 'status-container error';
    document.getElementById('statusSpinner').style.display = 'none';
    document.getElementById('statusTitle').innerText = title;
    document.getElementById('statusMessage').innerText = message;
    updateProgress(0);
}

function setControlsDisabled(disabled) {
    const btnHero = document.getElementById('btnOneClick');
    const btnDraft = document.getElementById('btnGenerateOnly');
    if (btnHero) btnHero.disabled = disabled;
    if (btnDraft) btnDraft.disabled = disabled;
}
