/**
 * AutoReelStudio — Google Material Design 3 (M3) Frontend Controller
 * 1-Click Publishing, Clean Responsive Architecture & Real-Time Sync
 */

const API_BASE = window.PROJECT_CONFIG ? (window.PROJECT_CONFIG.apiBaseUrl || '') : '';

// State
let queueItems = [];
let nextScheduledTime = null;
let countdownTimerId = null;

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    await Promise.all([
        fetchStatus(),
        fetchYouTubeStatus(),
        fetchQuota(),
        fetchIdeaBuffer(),
        fetchUniverseStatus(),
        fetchPublishingQueue(),
        fetchRecentlyPublished()
    ]);

    // Live sync polling every 10 seconds
    setInterval(() => {
        fetchPublishingQueue();
        fetchRecentlyPublished();
        fetchQuota();
    }, 10000);

    // Live countdown ticker every 1 second
    startCountdownTicker();
}

/**
 * 1-Click Hero Action: Publish Next Reel Now
 */
async function triggerPublishNow() {
    const btn = document.getElementById('btnPublishNowHero');
    const label = document.getElementById('btnPublishLabel');
    if (!btn) return;

    btn.disabled = true;
    const originalLabel = label.innerText;
    label.innerText = 'Publishing Next Reel...';

    try {
        showSnackbar('🚀 Initiating 1-Click Reel Publishing to Instagram & YouTube...', 'info');
        
        // 1. Try modern /api/action/publish-now or /api/publishing-queue/upload-now
        let res = await fetch(`${API_BASE}/api/action/publish-now`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        if (res.status === 404) {
            res = await fetch(`${API_BASE}/api/publishing-queue/upload-now`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
        }

        let data = await res.json();
        
        // If queue was empty on legacy server, synthesize and drop on the fly
        if (!data.success && data.error && data.error.includes('No pending videos')) {
            showSnackbar('💡 Staging fresh reel from Idea Queue...', 'info');
            const genRes = await fetch(`${API_BASE}/api/generate-and-publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dry_run: false })
            });
            data = await genRes.json();
        }

        if (data.success) {
            if (data.partial) {
                const igErr = data.errors?.instagram || 'Meta API access blocked';
                showSnackbar(`⚠️ Published to YouTube, but Instagram failed: ${igErr}`, 'error');
            } else {
                let msg = '🎉 Reel published successfully to Instagram & YouTube!';
                if (data.receipts && data.receipts.youtube && data.receipts.youtube.shorts_url) {
                    msg += ` YouTube Short: ${data.receipts.youtube.shorts_url}`;
                }
                showSnackbar(msg, 'success');
            }
            
            await Promise.all([
                fetchPublishingQueue(),
                fetchRecentlyPublished(),
                fetchQuota()
            ]);
        } else {
            showSnackbar(`⚠️ Publishing error: ${data.error || 'Failed to publish'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`❌ Network error: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        label.innerText = originalLabel;
    }
}

/**
 * Stage Next Reel Ahead in Queue
 */
async function triggerStageNext() {
    const btn = document.getElementById('btnStageNextHero');
    if (!btn) return;

    btn.disabled = true;
    try {
        showSnackbar('⚙️ Staging next reel into publishing queue...', 'info');
        const res = await fetch(`${API_BASE}/api/action/stage-next`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
            showSnackbar('✅ Next reel staged and scheduled for distribution!', 'success');
            await fetchPublishingQueue();
        } else {
            showSnackbar(`⚠️ Could not stage reel: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`❌ Error: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
    }
}

/**
 * Publish Specific Item Now from Queue
 */
async function uploadQueueItemNow(itemId) {
    if (!itemId) return;
    try {
        showSnackbar('⚡ Uploading scheduled reel right now...', 'info');
        const res = await fetch(`${API_BASE}/api/publishing-queue/upload-now`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            if (data.partial) {
                const igErr = data.errors?.instagram || 'Meta API access blocked';
                showSnackbar(`⚠️ Published to YouTube, but Instagram failed: ${igErr}`, 'error');
            } else {
                showSnackbar('🎉 Reel published live to Instagram & YouTube!', 'success');
            }
            await Promise.all([
                fetchPublishingQueue(),
                fetchRecentlyPublished(),
                fetchQuota()
            ]);
        } else {
            showSnackbar(`⚠️ Upload error: ${data.error || 'Failed to upload'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`❌ Error: ${err.message}`, 'error');
    }
}

/**
 * Remove Item from Queue and Disk
 */
async function removeQueueItem(itemId, itemTitle) {
    const titleText = itemTitle ? `"${itemTitle}"` : 'this reel';
    if (!confirm(`Are you sure you want to remove ${titleText} from the publishing queue?\n\nThis will delete the generated video file from disk and clear its scheduled slot.`)) return;

    try {
        showSnackbar(`Removing ${titleText}...`, 'info');
        const res = await fetch(`${API_BASE}/api/publishing-queue/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: itemId, delete_file: true })
        });
        const data = await res.json();
        if (data.success) {
            showSnackbar(`🗑️ Reel removed from queue: ${data.title || ''}`, 'success');
            await fetchPublishingQueue();
        } else {
            showSnackbar(`Failed to remove reel: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`Error: ${err.message}`, 'error');
    }
}

// Backward-compatible alias
async function cancelQueueItem(itemId) {
    const item = allKnownItems.get(itemId);
    return removeQueueItem(itemId, item ? item.title : '');
}

// Global preview item registry
let allKnownItems = new Map();
let currentPreviewItem = null;

function trackItems(items) {
    if (!Array.isArray(items)) return;
    items.forEach(itm => {
        if (itm && itm.id) {
            allKnownItems.set(itm.id, itm);
        }
    });
}

/**
 * Fetch Ready Videos Publishing Queue
 */
async function fetchPublishingQueue() {
    try {
        const res = await fetch(`${API_BASE}/api/publishing-queue`);
        if (!res.ok) return;
        const data = await res.json();

        trackItems(data.queue || []);

        const queue = (data.queue || []).filter(item => item.status === 'scheduled' || item.status === 'pending');
        queueItems = queue;

        // Update counts
        const scheduledCount = queue.length;
        const numElem = document.getElementById('queueScheduledNumber');
        const chipElem = document.getElementById('queueCountChip');
        if (numElem) numElem.innerText = scheduledCount;
        if (chipElem) chipElem.innerText = `${scheduledCount} Scheduled`;

        // Render queue list
        renderQueueList(queue);

        // Update next scheduled time
        if (queue.length > 0) {
            // Sort by scheduled time
            const sorted = [...queue].sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time));
            nextScheduledTime = new Date(sorted[0].scheduled_time);
        } else {
            nextScheduledTime = null;
        }
        updateCountdownDisplay();
    } catch (err) {
        console.warn('Error fetching queue:', err);
    }
}

/**
 * Render Queue List (Interactive Click-to-Play Web Video Preview)
 */
function renderQueueList(items) {
    const list = document.getElementById('queueList');
    const emptyState = document.getElementById('queueEmptyState');
    if (!list) return;

    if (!items || items.length === 0) {
        list.innerHTML = '';
        if (emptyState) emptyState.style.display = 'flex';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    list.innerHTML = items.map((item, index) => {
        const targetDate = item.scheduled_time ? new Date(item.scheduled_time) : null;
        const timeFormatted = targetDate ? targetDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Paced Next';
        const platforms = item.platforms || ['instagram', 'youtube'];
        const hasIg = platforms.includes('instagram');
        const hasYt = platforms.includes('youtube');

        return `
            <div class="md3-item-row" onclick="openVideoPreview('${item.id}')" title="Click to watch '${escapeHtml(item.title)}' preview in player">
                <div class="item-left">
                    <div class="item-play-thumbnail" title="Click to watch preview">
                        <span class="play-icon" style="font-size: 14px;">▶</span>
                        <span class="item-badge-index">${index + 1}</span>
                    </div>
                    <div class="item-info">
                        <span class="item-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</span>
                        <div class="item-meta-row">
                            <span>⏱️ Scheduled: ${timeFormatted}</span>
                            <span>•</span>
                            <span class="meta-preview-hint">
                                <span style="font-size: 13px;">📺</span> Watch Preview
                            </span>
                            <span>•</span>
                            ${hasIg ? '<span class="meta-chip ig">📸 Instagram</span>' : ''}
                            ${hasYt ? '<span class="meta-chip yt">▶️ YouTube</span>' : ''}
                        </div>
                    </div>
                </div>
                <div class="item-actions" onclick="event.stopPropagation()">
                    <button class="btn-item-action btn-preview-watch" onclick="openVideoPreview('${item.id}')" title="Preview video in web player">
                        <span style="font-size: 14px;">▶</span>
                        <span>Watch</span>
                    </button>
                    <button class="btn-item-action btn-upload-now" onclick="uploadQueueItemNow('${item.id}')" title="Publish this reel immediately">
                        <span style="font-size: 14px;">⚡</span>
                        <span>Publish Now</span>
                    </button>
                    <button class="btn-item-action btn-remove-queue" onclick="removeQueueItem('${item.id}', '${escapeHtml(item.title)}')" title="Remove this reel from queue">
                        <span style="font-size: 13px;">🗑️</span>
                        <span>Remove</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Fetch Recently Published Reels (Last 10 Rolling Buffer)
 */
async function fetchRecentlyPublished() {
    try {
        const res = await fetch(`${API_BASE}/api/recently-published`);
        if (!res.ok) return;
        const data = await res.json();

        trackItems(data.items || []);

        const items = data.items || [];
        const chipElem = document.getElementById('recentCountChip');
        if (chipElem) chipElem.innerText = `${items.length} / 10 Active`;

        renderRecentList(items);
    } catch (err) {
        console.warn('Error fetching recently published:', err);
    }
}

/**
 * Render Recently Published List
 */
function renderRecentList(items) {
    const list = document.getElementById('recentList');
    const emptyState = document.getElementById('recentEmptyState');
    if (!list) return;

    if (!items || items.length === 0) {
        list.innerHTML = '';
        if (emptyState) emptyState.style.display = 'flex';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    list.innerHTML = items.map((item, index) => {
        const pubDate = item.published_at ? new Date(item.published_at) : null;
        const timeAgo = pubDate ? formatTimeAgo(pubDate) : 'Recently';

        const igLink = item.instagram_permalink || (item.receipts?.instagram?.permalink);
        const ytLink = item.youtube_shorts_url || (item.receipts?.youtube?.shorts_url) || (item.youtube_video_id ? `https://youtube.com/shorts/${item.youtube_video_id}` : null);
        const platforms = item.platforms || ['instagram', 'youtube'];
        const hasIgTarget = platforms.includes('instagram') || platforms.includes('both');
        const igError = item.errors?.instagram || '';

        return `
            <div class="md3-item-row" onclick="openVideoPreview('${item.id}')" title="Click to watch '${escapeHtml(item.title)}' in player">
                <div class="item-left">
                    <div class="item-play-thumbnail" title="Click to watch">
                        <span class="material-symbols-outlined play-icon">play_arrow</span>
                        <span class="item-badge-index" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b;">${index + 1}</span>
                    </div>
                    <div class="item-info">
                        <span class="item-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</span>
                        <div class="item-meta-row">
                            <span>✨ Published ${timeAgo}</span>
                            <span>•</span>
                            <span class="meta-preview-hint">
                                <span class="material-symbols-outlined" style="font-size: 13px;">smart_display</span> Watch
                            </span>
                            ${igError ? `<span>•</span><span style="color: #f87171; font-size: 11px;">⚠️ IG: ${escapeHtml(igError.slice(0, 45))}...</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="item-actions" onclick="event.stopPropagation()">
                    <button class="btn-item-action btn-preview-watch" onclick="openVideoPreview('${item.id}')" title="Watch reel in web player">
                        <span class="material-symbols-outlined" style="font-size: 16px;">play_circle</span>
                        <span>Watch</span>
                    </button>
                    ${igLink ? `
                        <a href="${igLink}" target="_blank" class="btn-item-action btn-link-ig" title="View reel on Instagram">
                            <span class="material-symbols-outlined" style="font-size: 16px;">photo_camera</span>
                            <span>Instagram</span>
                        </a>
                    ` : (hasIgTarget ? `
                        <button class="btn-item-action btn-error-ig" onclick="retryInstagram('${item.id}')" title="${escapeHtml(igError || 'Instagram upload failed')} (Click to retry now)">
                            <span class="material-symbols-outlined" style="font-size: 16px; color: #f87171;">warning</span>
                            <span style="color: #f87171;">Retry IG</span>
                        </button>
                    ` : '')}
                    ${ytLink ? `
                        <a href="${ytLink}" target="_blank" class="btn-item-action btn-link-yt" title="View short on YouTube">
                            <span class="material-symbols-outlined" style="font-size: 16px;">smart_display</span>
                            <span>YouTube</span>
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Open Video Preview Modal (Watch On Web)
 */
function openVideoPreview(itemId) {
    const item = allKnownItems.get(itemId) || (queueItems || []).find(i => i.id === itemId);
    if (!item) {
        showSnackbar('Reel item details not found', 'error');
        return;
    }

    currentPreviewItem = item;

    const modalBackdrop = document.getElementById('videoModalBackdrop');
    const modalTitle = document.getElementById('modalVideoTitle');
    const modalSubtitle = document.getElementById('modalVideoSubtitle');
    const videoPlayer = document.getElementById('modalVideoPlayer');
    const videoSource = document.getElementById('modalVideoSource');
    const schedulePill = document.getElementById('modalScheduleTime');
    const hookBox = document.getElementById('modalHookText');
    const captionBox = document.getElementById('modalCaptionText');
    const publishBtn = document.getElementById('modalBtnPublishNow');
    const downloadBtn = document.getElementById('modalBtnDownload');
    const chipIg = document.getElementById('modalChipIg');
    const chipYt = document.getElementById('modalChipYt');

    if (!modalBackdrop || !videoPlayer) return;

    // Set title and subtitle
    if (modalTitle) modalTitle.innerText = item.title || 'Untitled Reel';
    
    const isScheduled = item.status === 'scheduled' || item.status === 'pending';
    const isPublished = item.status === 'published';
    
    if (modalSubtitle) {
        if (isScheduled && item.scheduled_time) {
            modalSubtitle.innerText = `Scheduled: ${new Date(item.scheduled_time).toLocaleString()} · 1080x1920 (9:16 Shorts/Reels)`;
        } else if (isPublished && item.published_at) {
            modalSubtitle.innerText = `Published: ${new Date(item.published_at).toLocaleString()} · Live on Social Channels`;
        } else {
            modalSubtitle.innerText = `Status: ${item.status || 'Active'} · 1080x1920 (9:16 Shorts/Reels)`;
        }
    }

    // Set status pill
    if (schedulePill) {
        if (isScheduled) {
            schedulePill.innerText = `Scheduled Drop: ${item.scheduled_time ? new Date(item.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Paced Next'}`;
        } else if (isPublished) {
            schedulePill.innerText = `Live Published Drop`;
        } else {
            schedulePill.innerText = `Status: ${item.status || 'Queued'}`;
        }
    }

    // Set platform chips visibility
    const platforms = item.platforms || ['instagram', 'youtube'];
    if (chipIg) chipIg.style.display = platforms.includes('instagram') ? 'inline-flex' : 'none';
    if (chipYt) chipYt.style.display = platforms.includes('youtube') ? 'inline-flex' : 'none';

    // Set Hook
    const igCap = item.instagram_meta?.caption || '';
    const ytDesc = item.youtube_meta?.description || '';
    const firstLine = igCap.split('\n')[0] || ytDesc.split('\n')[0] || item.title;
    if (hookBox) hookBox.innerText = `"${firstLine}"`;

    // Set Caption
    const fullCaption = igCap || ytDesc || 'Autonomous metadata generated for Instagram & YouTube.';
    if (captionBox) captionBox.innerText = fullCaption;

    // Set Video Stream Source
    const videoUrl = item.filename 
        ? `${API_BASE}/output/${encodeURIComponent(item.filename)}`
        : `${API_BASE}/api/video/stream?id=${encodeURIComponent(item.id)}`;

    videoSource.src = videoUrl;
    videoPlayer.load();
    const playPromise = videoPlayer.play();
    if (playPromise !== undefined) {
        playPromise.catch(err => {
            console.log('Autoplay waiting for user gesture:', err);
        });
    }

    // Download button
    if (downloadBtn) {
        downloadBtn.href = videoUrl;
        downloadBtn.download = item.filename || `${item.id}.mp4`;
    }

    // Publish button state
    if (publishBtn) {
        if (isPublished) {
            publishBtn.style.display = 'none';
        } else {
            publishBtn.style.display = 'inline-flex';
        }
    }

    // Show modal
    modalBackdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Close Video Preview Modal
 */
function closeVideoModal(event) {
    if (event && event.target && event.target.id !== 'videoModalBackdrop' && !event.target.closest('.md3-btn-icon-close') && !event.target.closest('.md3-btn-text-sm')) {
        return;
    }

    const modalBackdrop = document.getElementById('videoModalBackdrop');
    const videoPlayer = document.getElementById('modalVideoPlayer');
    const videoSource = document.getElementById('modalVideoSource');

    if (videoPlayer) {
        videoPlayer.pause();
        if (videoSource) videoSource.src = '';
    }

    if (modalBackdrop) {
        modalBackdrop.classList.remove('active');
    }

    document.body.style.overflow = '';
    currentPreviewItem = null;
}

/**
 * Modal Publish Current Reel Action
 */
async function modalPublishCurrentReel() {
    if (!currentPreviewItem || !currentPreviewItem.id) return;
    const itm = currentPreviewItem;
    closeVideoModal();
    await uploadQueueItemNow(itm.id);
}

/**
 * Modal Discard / Remove Current Reel Action
 */
async function modalRemoveCurrentReel() {
    if (!currentPreviewItem || !currentPreviewItem.id) return;
    const itm = currentPreviewItem;
    closeVideoModal();
    await removeQueueItem(itm.id, itm.title);
}

/**
 * Keyboard shortcuts for preview modal
 */
window.addEventListener('keydown', (e) => {
    const modalBackdrop = document.getElementById('videoModalBackdrop');
    if (!modalBackdrop || !modalBackdrop.classList.contains('active')) return;

    if (e.key === 'Escape') {
        closeVideoModal();
    } else if (e.key === ' ' && document.activeElement && !['input', 'textarea', 'button'].includes(document.activeElement.tagName.toLowerCase())) {
        e.preventDefault();
        const videoPlayer = document.getElementById('modalVideoPlayer');
        if (videoPlayer) {
            if (videoPlayer.paused) videoPlayer.play();
            else videoPlayer.pause();
        }
    }
});

// Global quota state
let currentQuota = {
    auto_publish_stopped: false,
    remaining_manual: 20
};

/**
 * Fetch Daily Quota & Cadence Status
 */
async function fetchQuota() {
    try {
        const res = await fetch(`${API_BASE}/api/quota`);
        if (!res.ok) return;
        const data = await res.json();
        const q = data.quota || {};
        currentQuota = q;

        const autoPublished = q.auto_published_today !== undefined ? q.auto_published_today : (q.generated_today || 0);
        const manualPublished = q.manual_published_today || 0;
        const autoLimit = q.daily_limit || 10;
        const manualLimit = q.manual_limit || 5;
        const remainingAuto = q.remaining_today !== undefined ? q.remaining_today : (autoLimit - autoPublished);
        const remainingManual = q.remaining_manual !== undefined ? q.remaining_manual : 5;
        const isStopped = !!q.auto_publish_stopped;
        const percent = Math.min(100, Math.round((autoPublished / autoLimit) * 100));

        // Metric 1: 10 Daily Reels Target
        const numElem = document.getElementById('quotaPublishedNumber');
        const barElem = document.getElementById('quotaProgressBar');
        const capElem = document.getElementById('quotaCaption');
        const manualBadge = document.getElementById('manualOverrideBadge');

        if (numElem) numElem.innerText = autoPublished;
        if (barElem) barElem.style.width = `${percent}%`;
        if (capElem) {
            capElem.innerText = `${remainingAuto} daily reels remaining for today`;
        }
        if (manualBadge) {
            manualBadge.innerText = `Manual Override: ${manualPublished} / ${manualLimit} Pushed`;
        }

        // Hero Button Sublabel (Remaining manual pushes)
        const subLabel = document.getElementById('btnPublishQuota');
        if (subLabel) {
            subLabel.innerText = `${remainingManual} Manual Pushes Left`;
        }

        // Hero Auto-Cadence Status Badge & Alert Banner
        const heroBadge = document.getElementById('heroStatusBadge');
        const heroPulse = document.getElementById('heroPulseIndicator');
        const statusText = document.getElementById('autonomousStatusText');
        const alertBanner = document.getElementById('overrideAlertBanner');
        const alertText = document.getElementById('overrideAlertText');

        if (isStopped) {
            if (heroBadge) heroBadge.className = 'md3-status-badge stopped';
            if (heroPulse) heroPulse.className = 'pulse-indicator stopped';
            if (statusText) statusText.innerText = 'Auto-Publish Paused for Today · 1-Click Override Active';
            if (alertBanner) alertBanner.style.display = 'flex';
            if (alertText) {
                alertText.innerText = `Auto-publish stopped for today. Manual override: ${remainingManual} of ${manualLimit} reels left.`;
            }
        } else {
            if (heroBadge) heroBadge.className = 'md3-status-badge';
            if (heroPulse) heroPulse.className = 'pulse-indicator';
            if (statusText) statusText.innerText = '5-Hour Publishing Drops · Continuous Pre-Rendering Active';
            if (alertBanner) alertBanner.style.display = 'none';
        }

        updateCountdownDisplay();
    } catch (err) {
        console.warn('Error fetching quota:', err);
    }
}

/**
 * 1-Click Action: Resume Auto-Publish Today
 */
async function triggerResumeAuto() {
    const btn = document.getElementById('btnResumeAuto');
    if (btn) btn.disabled = true;
    try {
        showSnackbar('▶️ Resuming background 5-hour auto-publishing...', 'info');
        const res = await fetch(`${API_BASE}/api/action/resume-auto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
            showSnackbar('✅ Auto-publishing resumed successfully!', 'success');
            await fetchQuota();
        } else {
            showSnackbar(`⚠️ Could not resume: ${data.error || 'Failed'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`❌ Error: ${err.message}`, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

/**
 * Fetch Idea Buffer Count
 */
async function fetchIdeaBuffer() {
    try {
        const res = await fetch(`${API_BASE}/api/queue`);
        if (!res.ok) return;
        const data = await res.json();

        const countElem = document.getElementById('ideaBufferNumber');
        if (countElem) countElem.innerText = data.count || 13;
    } catch (err) {
        console.warn('Error fetching idea buffer:', err);
    }
}

/**
 * Fetch General Status (Instagram & Storage)
 */
async function fetchStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        if (!res.ok) return;
        const data = await res.json();

        const igHandle = document.getElementById('igHandle');
        const igDot = document.getElementById('igStatusDot');
        const chipIg = document.getElementById('chipInstagram');

        if (data.authenticated) {
            if (igHandle) igHandle.innerText = `@${data.account?.username || 'sun_27417'}`;
            if (igDot) igDot.className = 'chip-status-dot online';
            if (chipIg) chipIg.title = 'Meta Instagram Graph API — Connected';
        } else {
            const errReason = data.error || 'Blocked by Meta';
            if (igHandle) igHandle.innerText = `@${data.account?.username || 'sun_27417'} (Meta Blocked)`;
            if (igDot) igDot.className = 'chip-status-dot offline';
            if (chipIg) {
                chipIg.title = `Instagram API Blocked: ${errReason} — Click to update access token`;
                chipIg.style.cursor = 'pointer';
                chipIg.onclick = promptUpdateMetaToken;
            }
        }
    } catch (err) {
        console.warn('Error fetching status:', err);
    }
}

/**
 * 1-Click Retry Instagram Publication for a Specific Reel
 */
async function retryInstagram(itemId) {
    if (!itemId) return;
    try {
        showSnackbar('📸 Retrying Instagram Reels publication...', 'info');
        const res = await fetch(`${API_BASE}/api/action/retry-instagram`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            showSnackbar('🎉 Instagram Reel published successfully!', 'success');
            await fetchRecentlyPublished();
        } else {
            showSnackbar(`❌ Instagram publish error: ${data.error || 'Failed'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`❌ Network error: ${err.message}`, 'error');
    }
}

/**
 * Update Meta Access Token Dialog
 */
async function promptUpdateMetaToken() {
    const token = prompt('Enter your fresh Meta Long-Lived Access Token (or Page Access Token):');
    if (!token || !token.trim()) return;

    try {
        showSnackbar('🔑 Updating and verifying Meta access token...', 'info');
        const res = await fetch(`${API_BASE}/api/instagram/update-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token.trim() })
        });
        const data = await res.json();
        if (data.authenticated) {
            showSnackbar('✅ Meta access token verified & connected to Instagram!', 'success');
            await fetchStatus();
        } else {
            showSnackbar(`⚠️ Meta token rejected: ${data.error || 'Invalid token'}`, 'error');
            await fetchStatus();
        }
    } catch (err) {
        showSnackbar(`❌ Error: ${err.message}`, 'error');
    }
}

/**
 * Fetch YouTube Channel Status
 */
async function fetchYouTubeStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/youtube/status`);
        if (!res.ok) return;
        const data = await res.json();

        const ytHandle = document.getElementById('ytHandle');
        const dot = document.getElementById('ytStatusDot');

        if (data.authenticated) {
            if (ytHandle) ytHandle.innerText = data.title || data.custom_url || 'EGO X';
            if (dot) dot.className = 'chip-status-dot online';
        } else {
            if (ytHandle) ytHandle.innerText = 'YouTube Offline';
            if (dot) dot.className = 'chip-status-dot offline';
        }
    } catch (err) {
        console.warn('Error fetching YouTube status:', err);
    }
}

/**
 * Custom Reel Synthesizer (Optional)
 */
async function triggerCustomReel() {
    const input = document.getElementById('customPromptInput');
    const btn = document.getElementById('btnCustomGenerate');
    const prompt = (input ? input.value : '').trim();

    if (!prompt) {
        showSnackbar('Please enter a topic or concept for your custom reel', 'error');
        return;
    }

    if (btn) btn.disabled = true;
    try {
        showSnackbar('✨ Generating custom reel & adding to publishing queue...', 'info');
        const res = await fetch(`${API_BASE}/api/generate-and-publish`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt, dry_run: false })
        });
        const data = await res.json();
        if (data.success) {
            showSnackbar('🎉 Custom reel created and staged for publication!', 'success');
            if (input) input.value = '';
            await fetchPublishingQueue();
        } else {
            showSnackbar(`⚠️ Generation error: ${data.error || 'Failed'}`, 'error');
        }
    } catch (err) {
        showSnackbar(`❌ Error: ${err.message}`, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

/**
 * Countdown Ticker Loop
 */
function startCountdownTicker() {
    if (countdownTimerId) clearInterval(countdownTimerId);
    countdownTimerId = setInterval(updateCountdownDisplay, 1000);
}

function updateCountdownDisplay() {
    const countdownElem = document.getElementById('nextDropCountdown');
    if (!countdownElem) return;

    if (currentQuota && currentQuota.auto_publish_stopped) {
        countdownElem.innerText = 'Paused for today (Manual override active)';
        return;
    }

    if (!nextScheduledTime) {
        countdownElem.innerText = 'Standby (Ready for 1-Click)';
        return;
    }

    const now = new Date();
    const diffMs = nextScheduledTime - now;

    if (diffMs <= 0) {
        countdownElem.innerText = 'Ready to drop now';
        return;
    }

    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);
    countdownElem.innerText = `${diffMins}m ${diffSecs.toString().padStart(2, '0')}s`;
}

/**
 * Toast / Snackbar Notification Helper
 */
function showSnackbar(message, type = 'info') {
    const container = document.getElementById('snackbarContainer');
    if (!container) return;

    const snackbar = document.createElement('div');
    snackbar.className = `md3-snackbar ${type}`;

    let iconName = 'info';
    if (type === 'success') iconName = 'check_circle';
    if (type === 'error') iconName = 'error';

    snackbar.innerHTML = `
        <span class="material-symbols-outlined snackbar-icon">${iconName}</span>
        <span class="snackbar-msg">${escapeHtml(message)}</span>
    `;

    container.appendChild(snackbar);

    setTimeout(() => {
        snackbar.style.opacity = '0';
        snackbar.style.transform = 'translateY(10px)';
        snackbar.style.transition = 'all 0.3s ease';
        setTimeout(() => snackbar.remove(), 300);
    }, 4500);
}

/**
 * Utility: Format Time Ago
 */
function formatTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

/**
 * 2026 Character Universe & Episodic Continuity Controller
 */
async function fetchUniverseStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/universe/status`);
        if (!res.ok) return;
        const data = await res.json();
        if (!data.success || !data.active) return;

        const active = data.active;
        const catBadge = document.getElementById('universeCategoryBadge');
        const epPill = document.getElementById('universeEpisodePill');
        const titleElem = document.getElementById('universeTitle');
        const descElem = document.getElementById('universeDescription');
        const castContainer = document.getElementById('universeCastChips');

        if (catBadge) catBadge.innerText = (active.category || 'Knowledge Domain').replace('_', ' ').toUpperCase();
        if (epPill) epPill.innerText = `Module ${active.current_season || 1} · Topic ${active.current_episode || 1}`;
        if (titleElem) titleElem.innerText = active.title || 'Knowledge Domain';
        if (descElem) descElem.innerText = active.description || '';

        // Update active tab button
        document.querySelectorAll('.universe-tab').forEach(tab => {
            if (tab.getAttribute('onclick') && tab.getAttribute('onclick').includes(active.universe_id)) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        // Render cast chips
        if (castContainer && active.cast && active.cast.length > 0) {
            const emojiMap = {
                'Kernel Architecture': '⚡',
                'Virtual Topology': '🔄',
                'I/O Multiplexing': '🚀',
                'Probabilistic Sets': '🛡️',
                'Silicon Logic': '💻',
                'Memory Hierarchy': '🧱',
                'MMU Silicon': '🗺️',
                'CPU Micro-Op Scheduler': '⚙️',
                'Complexity Analysis': '📈',
                'LIFO Architecture': '📚',
                'Memory Management': '💾',
                'Compiler Passes': '🛠️',
                'Mantle Mineral': '💎',
                'Ionized Gas': '⚡',
                'Quantum Optics': '🔬',
                'Cosmic Structure': '🌌',
                'Volcanic Material': '🌋',
                'Self-Healing Chemical Matrix': '🧪',
                'Precision Mechanics': '⚙️'
            };
            castContainer.innerHTML = active.cast.map(c => {
                const emoji = emojiMap[c.species] || '⚡';
                return `
                    <div class="cast-chip" title="${escapeHtml(c.traits || '')}">
                        <span class="cast-emoji">${emoji}</span>
                        <div class="cast-details">
                            <span class="cast-name">${escapeHtml(c.name)}</span>
                            <span class="cast-role">${escapeHtml(c.species)}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (err) {
        console.warn('Error fetching universe status:', err);
    }
}

async function selectUniverse(universeId) {
    try {
        showSnackbar(`Switching domain...`, 'info');
        const res = await fetch(`${API_BASE}/api/universe/set-active`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ universe_id: universeId })
        });
        const data = await res.json();
        if (data.success) {
            showSnackbar(`Domain active: ${data.active.title}`, 'success');
            await fetchUniverseStatus();
            await fetchIdeaBuffer();
        }
    } catch (err) {
        showSnackbar('Failed to switch domain: ' + err.message, 'error');
    }
}

/**
 * Utility: HTML Escape
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
