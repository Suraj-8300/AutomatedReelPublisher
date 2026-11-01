/**
 * ReelPublisher Web Studio Frontend Logic
 * Supports standalone local serving, containerized Hugging Face Spaces,
 * and portfolio embedding via window.PROJECT_CONFIG.
 */

// Dynamically determine API base URL (falls back to local relative paths)
const API_BASE = (typeof window !== 'undefined' && window.PROJECT_CONFIG?.apiBaseUrl) || '';

let activeVideoFilename = null;
let isSafeZoneVisible = false;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    checkAccountStatus();
    loadGallery();
});

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
 * 2. Roll random viral topic from chosen niche
 */
async function rollIdea() {
    const niche = document.getElementById('nicheSelect').value;
    try {
        const res = await fetch(`${API_BASE}/api/random-topic?niche=${encodeURIComponent(niche)}`);
        const data = await res.json();
        if (data && data.title) {
            document.getElementById('promptInput').value = data.title;
        }
    } catch (e) {
        console.error('Failed to roll idea:', e);
    }
}

/**
 * 3. ⚡ 1-Click Generate & Auto-Publish to Instagram Reels
 */
async function triggerOneClickPublish() {
    const btnHero = document.getElementById('btnOneClick');
    const btnDraft = document.getElementById('btnGenerateOnly');
    const prompt = document.getElementById('promptInput').value.trim();
    const duration = parseInt(document.querySelector('input[name="duration"]:checked').value);
    const voice = document.getElementById('voiceSelect').value;
    const music = document.getElementById('musicSelect').value;
    const mode = document.getElementById('publishMode').value;
    const dryRun = (mode === 'dry_run');

    setControlsDisabled(true);
    showStatus('⚡ 1-Click Pipeline Engaged', 'Synthesizing neural voiceover, compiling 9:16 footage & formatting captions...', 25);

    try {
        const payload = { prompt, duration, voice, music, dry_run: dryRun };
        const res = await fetch(`${API_BASE}/api/generate-and-publish`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            updateProgress(100);
            const permalink = data.permalink || (dryRun ? 'https://www.instagram.com/reel/dryrun_simulation/' : '#');
            const receiptHtml = `
                <div style="margin-top: 8px;">
                    <p style="color: #00FFA3; font-weight: bold; font-size: 0.95rem;">🎉 Reel Published Successfully to Instagram!</p>
                    <p style="margin: 4px 0 10px 0; font-size: 0.84rem;">Total pipeline time: ${data.elapsed ? data.elapsed.toFixed(1) + 's' : 'done'}</p>
                    <a href="${permalink}" target="_blank" class="btn-publish-direct" style="display: inline-block; width: auto; padding: 8px 18px; text-decoration: none;">
                        🔗 View Reel on Instagram (@sun_27417)
                    </a>
                </div>
            `;
            showSuccess('✅ Live Publication Complete!', receiptHtml);

            // Load into preview player
            loadVideoIntoPreview(data.video_url, data.filename || 'reel.mp4', true);
            loadGallery();
            checkAccountStatus();
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
    const prompt = document.getElementById('promptInput').value.trim();
    const duration = parseInt(document.querySelector('input[name="duration"]:checked').value);
    const voice = document.getElementById('voiceSelect').value;
    const music = document.getElementById('musicSelect').value;

    setControlsDisabled(true);
    showStatus('🎬 Compiling Video Draft', 'Concurrently pulling B-roll, synthesizing TTS & rendering vertical 1080x1920 MP4...', 35);

    try {
        const payload = { prompt, duration, voice, music };
        const res = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            updateProgress(100);
            showSuccess('✅ Video Draft Rendered!', `Reel compiled in ${data.elapsed.toFixed(1)}s. Preview loaded below. You can inspect specs or publish whenever ready.`);
            loadVideoIntoPreview(data.video_url, data.filename || 'reel.mp4', false);
            loadGallery();
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
 * 6. Inspect Active Video Specs
 */
async function inspectActiveVideo() {
    if (!activeVideoFilename) return;
    openSpecAudit(activeVideoFilename);
}

async function openSpecAudit(filename) {
    const drawer = document.getElementById('specAuditDrawer');
    const content = document.getElementById('specAuditContent');
    drawer.style.display = 'block';
    content.innerHTML = '<p style="grid-column: 1/-1; color: var(--accent);">🔍 Probing container streams with ffprobe...</p>';

    try {
        const res = await fetch(`${API_BASE}/api/inspect?video=${encodeURIComponent(filename)}`);
        const data = await res.json();

        if (!data.success) {
            content.innerHTML = `<p style="grid-column: 1/-1; color: var(--danger);">Failed to probe: ${data.error}</p>`;
            return;
        }

        const p = data.probe;
        const c = data.compliance;

        content.innerHTML = `
            <div class="spec-item">
                <span class="spec-label">Resolution</span>
                <span class="spec-val ${p.video.width === 1080 && p.video.height === 1920 ? 'ok' : 'err'}">${p.video.width} x ${p.video.height} (9:16)</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Frame Rate</span>
                <span class="spec-val ${p.video.fps >= 23 && p.video.fps <= 60 ? 'ok' : 'warn'}">${p.video.fps} FPS</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Video Codec</span>
                <span class="spec-val ok">${p.video.codec_name} (${p.video.profile || 'High'})</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Faststart Moov</span>
                <span class="spec-val ${p.faststart ? 'ok' : 'warn'}">${p.faststart ? 'YES (+faststart)' : 'Added on Publish'}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Audio Channels</span>
                <span class="spec-val ${p.audio.channels === 2 ? 'ok' : 'warn'}">${p.audio.channels === 2 ? 'Stereo (2)' : p.audio.channels + ' (Normalized on Publish)'}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Audio Sample Rate</span>
                <span class="spec-val ${p.audio.sample_rate === 48000 ? 'ok' : 'warn'}">${p.audio.sample_rate} Hz</span>
            </div>
            <div class="spec-item" style="grid-column: 1/-1;">
                <span class="spec-label">Compliance Verdict:</span>
                <span class="spec-val ${c.is_compliant ? 'ok' : 'warn'}">${c.is_compliant ? '✅ 100% Ready for Instagram Reels' : '⚠️ Pipeline will auto-transcode to 1080x1920 & stereo AAC on publish'}</span>
            </div>
        `;
    } catch (err) {
        content.innerHTML = `<p style="grid-column: 1/-1; color: var(--danger);">Inspection failed: ${err.message}</p>`;
    }
}

function closeSpecAudit() {
    document.getElementById('specAuditDrawer').style.display = 'none';
}

/**
 * 7. Safe Zone Danger Overlay Toggle
 */
function toggleSafeZoneOverlay() {
    const overlay = document.getElementById('safeZoneOverlay');
    const btnText = document.getElementById('safeZoneBtnText');
    isSafeZoneVisible = !isSafeZoneVisible;
    overlay.style.display = isSafeZoneVisible ? 'flex' : 'none';
    btnText.innerText = isSafeZoneVisible ? '📐 Hide Safe Zones' : '📐 Toggle Safe Zones';
}

/**
 * 8. Load a video into the main vertical preview player
 */
function loadVideoIntoPreview(url, filename, published = false) {
    activeVideoFilename = filename;
    const player = document.getElementById('mainVideoPlayer');
    const emptyState = document.getElementById('emptyPreview');
    const previewActions = document.getElementById('previewActions');
    const badge = document.getElementById('videoStatusBadge');
    const downloadBtn = document.getElementById('btnDownloadActive');

    emptyState.style.display = 'none';
    player.style.display = 'block';
    player.src = `${API_BASE}${url}`;
    player.play().catch(() => {});

    previewActions.style.display = 'flex';
    downloadBtn.href = `${API_BASE}${url}`;
    downloadBtn.download = filename;

    if (published) {
        badge.className = 'badge badge-success';
        badge.innerText = 'Published to Instagram';
    } else {
        badge.className = 'badge badge-accent';
        badge.innerText = 'Draft Ready';
    }
}

/**
 * 9. Gallery Archive Loader
 */
async function loadGallery() {
    const grid = document.getElementById('galleryGrid');
    const countBadge = document.getElementById('galleryCount');

    try {
        const res = await fetch(`${API_BASE}/api/gallery`);
        const videos = await res.json();

        grid.innerHTML = '';
        if (!videos || videos.length === 0) {
            countBadge.innerText = '0 videos';
            grid.innerHTML = '<p style="color: var(--text-secondary); grid-column: 1/-1; padding: 24px; text-align: center;">No reels generated yet. Hit 1-Click Generate above to start!</p>';
            return;
        }

        countBadge.innerText = `${videos.length} videos`;
        videos.forEach(v => {
            const card = document.createElement('div');
            card.className = 'gallery-card';
            const isPub = v.published;

            card.innerHTML = `
                <div class="gallery-video-wrapper">
                    <video src="${API_BASE}${v.url}" controls preload="metadata"></video>
                </div>
                <div class="gallery-info">
                    <div class="gallery-item-title">${v.name}</div>
                    <div class="gallery-badge-row">
                        <span>📦 ${v.size}</span>
                        ${isPub ? '<span style="color: var(--success); font-weight: bold;">• ✅ Published</span>' : '<span style="color: var(--accent);">• 📝 Draft</span>'}
                    </div>
                    <div class="gallery-card-actions">
                        ${isPub && v.permalink 
                            ? `<a href="${v.permalink}" target="_blank" class="btn-gallery-pub" style="text-align: center; text-decoration: none;">🔗 View on Instagram</a>`
                            : `<button class="btn-gallery-pub" onclick="publishVideoFile('${v.filename}')">📲 Publish to Instagram</button>`
                        }
                        <div class="gallery-sub-actions">
                            <button class="btn-gallery-tool" onclick="openGalleryInspect('${v.filename}', '${v.name}')">🔍 Audit</button>
                            <a href="${API_BASE}${v.url}" download="${v.filename}" class="btn-gallery-tool">⬇️ Save</a>
                        </div>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error('Gallery load error:', e);
    }
}

/**
 * Gallery Inspection Modal
 */
async function openGalleryInspect(filename, title) {
    const modal = document.getElementById('inspectModal');
    const titleEl = document.getElementById('modalVideoTitle');
    const bodyEl = document.getElementById('modalAuditBody');

    titleEl.innerText = `Reel Audit: ${title}`;
    bodyEl.innerHTML = '<p style="color: var(--accent);">Probing video streams...</p>';
    modal.style.display = 'flex';

    try {
        const res = await fetch(`${API_BASE}/api/inspect?video=${encodeURIComponent(filename)}`);
        const data = await res.json();

        if (data.success) {
            const p = data.probe;
            const c = data.compliance;
            bodyEl.innerHTML = `
                <div class="spec-audit-grid" style="margin-bottom: 12px;">
                    <div class="spec-item"><span class="spec-label">Resolution</span><span class="spec-val ok">${p.video.width} x ${p.video.height}</span></div>
                    <div class="spec-item"><span class="spec-label">Duration</span><span class="spec-val ok">${p.duration.toFixed(1)}s</span></div>
                    <div class="spec-item"><span class="spec-label">Framerate</span><span class="spec-val ok">${p.video.fps} FPS</span></div>
                    <div class="spec-item"><span class="spec-label">Audio</span><span class="spec-val ok">${p.audio.channels === 2 ? 'Stereo' : 'Mono'} (${p.audio.sample_rate}Hz)</span></div>
                </div>
                <div style="background: #080c14; padding: 12px; border-radius: 8px; border: 1px solid var(--card-border);">
                    <p style="font-weight: bold; margin-bottom: 6px;">Compliance Status: ${c.is_compliant ? '<span style="color:#00FFA3">Compliant</span>' : '<span style="color:#FFB800">Normalization needed</span>'}</p>
                    <p style="font-size: 0.8rem; color: var(--text-secondary);">${c.issues && c.issues.length ? c.issues.join('<br>') : 'All Instagram Reels technical criteria met perfectly.'}</p>
                </div>
            `;
        } else {
            bodyEl.innerHTML = `<p style="color: var(--danger);">${data.error}</p>`;
        }
    } catch (e) {
        bodyEl.innerHTML = `<p style="color: var(--danger);">${e.message}</p>`;
    }
}

function closeInspectModal() {
    document.getElementById('inspectModal').style.display = 'none';
}

/**
 * Helpers for UI States
 */
function setControlsDisabled(disabled) {
    document.getElementById('btnOneClick').disabled = disabled;
    document.getElementById('btnGenerateOnly').disabled = disabled;
    const pubActive = document.getElementById('btnPublishActive');
    if (pubActive) pubActive.disabled = disabled;
}

function showStatus(title, message, progress = 20) {
    const box = document.getElementById('statusBox');
    const titleEl = document.getElementById('statusTitle');
    const msgEl = document.getElementById('statusMessage');
    const bar = document.getElementById('progressBar');
    box.style.display = 'block';
    box.style.borderColor = 'var(--accent)';
    titleEl.innerText = title;
    msgEl.innerHTML = message;
    bar.style.width = `${progress}%`;
}

function updateProgress(progress) {
    const bar = document.getElementById('progressBar');
    if (bar) bar.style.width = `${progress}%`;
}

function showSuccess(title, htmlMessage) {
    const box = document.getElementById('statusBox');
    const titleEl = document.getElementById('statusTitle');
    const msgEl = document.getElementById('statusMessage');
    const spinner = document.getElementById('statusSpinner');
    box.style.display = 'block';
    box.style.borderColor = 'var(--success)';
    if (spinner) spinner.style.display = 'none';
    titleEl.innerText = title;
    titleEl.style.color = 'var(--success)';
    msgEl.innerHTML = htmlMessage;
}

function showError(title, message) {
    const box = document.getElementById('statusBox');
    const titleEl = document.getElementById('statusTitle');
    const msgEl = document.getElementById('statusMessage');
    const spinner = document.getElementById('statusSpinner');
    box.style.display = 'block';
    box.style.borderColor = 'var(--danger)';
    if (spinner) spinner.style.display = 'none';
    titleEl.innerText = title;
    titleEl.style.color = 'var(--danger)';
    msgEl.innerHTML = `<span style="color: var(--danger);">${message}</span>`;
}
