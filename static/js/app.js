/**
 * AutoReelStudio — Modern Video Upload, AI Reading & Social Publishing Studio.
 * Clean, reactive, zero-lag standard JavaScript frontend.
 */

// ── Application State ────────────────────────────────────────────────────────
const state = {
    activeTab: 'studio', // 'studio', 'ready', 'published', 'insights'
    status: null,
    readyVideos: [],
    publishedVideos: [],
    selectedVideo: null, // Active video in Studio Editor
    uploading: false,
    uploadProgress: 0,
    analyzing: false,
    statusMessage: '',
    previewModalVideo: null,
    publishedFilter: 'all', // 'all', 'instagram', 'youtube'
    searchQuery: '',
    toast: null,
};

// ── Toast Notification Helper ────────────────────────────────────────────────
function showToast(message, type = 'success') {
    state.toast = { message, type };
    render();
    setTimeout(() => {
        if (state.toast && state.toast.message === message) {
            state.toast = null;
            render();
        }
    }, 4500);
}

// ── API Fetchers ─────────────────────────────────────────────────────────────
async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        state.status = await res.json();
    } catch (e) {
        console.error('Error fetching status:', e);
    }
}

async function fetchReadyVideos() {
    try {
        const res = await fetch('/api/videos/ready');
        const data = await res.json();
        state.readyVideos = data.videos || [];
        // If no video is selected in studio and ready videos exist, select the latest one
        if (!state.selectedVideo && state.readyVideos.length > 0) {
            state.selectedVideo = state.readyVideos[0];
        }
    } catch (e) {
        console.error('Error fetching ready videos:', e);
    }
}

async function fetchPublishedVideos() {
    try {
        const res = await fetch('/api/videos/published');
        const data = await res.json();
        state.publishedVideos = data.published || [];
    } catch (e) {
        console.error('Error fetching published videos:', e);
    }
}

async function refreshAll() {
    await Promise.all([fetchStatus(), fetchReadyVideos(), fetchPublishedVideos()]);
    render();
}

// ── Video Upload Handler ─────────────────────────────────────────────────────
function uploadVideoFile(file) {
    if (!file) return;

    if (!file.name.match(/\.(mp4|mov|webm|mkv)$/i)) {
        showToast('Please upload an MP4, MOV, or WebM video file.', 'error');
        return;
    }

    state.uploading = true;
    state.uploadProgress = 10;
    state.statusMessage = 'Uploading video file to studio...';
    render();

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload', true);

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 75);
            state.uploadProgress = Math.max(10, percent);
            if (percent >= 75) {
                state.statusMessage = 'Upload complete! Gemini AI is watching and reading video...';
            }
            render();
        }
    };

    xhr.onload = () => {
        state.uploading = false;
        state.uploadProgress = 100;
        if (xhr.status >= 200 && xhr.status < 300) {
            try {
                const data = JSON.parse(xhr.responseText);
                state.selectedVideo = data.metadata;
                state.activeTab = 'studio';
                showToast(`🎉 Video uploaded and analyzed: "${data.metadata.title}"`, 'success');
                refreshAll();
            } catch (err) {
                showToast('Upload finished, but error parsing response.', 'error');
                refreshAll();
            }
        } else {
            showToast(`Upload failed (Status ${xhr.status}).`, 'error');
            render();
        }
    };

    xhr.onerror = () => {
        state.uploading = false;
        showToast('Network error during video upload.', 'error');
        render();
    };

    xhr.send(formData);
}

// ── Re-Analyze with Custom Prompt ────────────────────────────────────────────
async function reanalyzeVideo(customInstruction) {
    if (!state.selectedVideo) return;
    state.analyzing = true;
    state.statusMessage = 'Gemini AI is re-reading video with custom direction...';
    render();

    try {
        const res = await fetch('/api/video/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: state.selectedVideo.filename,
                instruction: customInstruction
            })
        });
        const data = await res.json();
        if (data.success && data.metadata) {
            state.selectedVideo = data.metadata;
            showToast('✨ Video re-analyzed with fresh viral captions!', 'success');
            refreshAll();
        } else {
            showToast(data.error || 'Failed to re-analyze video.', 'error');
        }
    } catch (e) {
        showToast('Error during video analysis.', 'error');
    } finally {
        state.analyzing = false;
        render();
    }
}

// ── Save Metadata Changes ────────────────────────────────────────────────────
async function saveMetadataChanges() {
    if (!state.selectedVideo) return;
    try {
        const res = await fetch('/api/video/update-metadata', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.selectedVideo)
        });
        const data = await res.json();
        if (data.success) {
            state.selectedVideo = data.metadata;
            showToast('💾 Metadata changes saved successfully!', 'success');
            refreshAll();
        } else {
            showToast('Failed to save changes.', 'error');
        }
    } catch (e) {
        showToast('Error saving metadata.', 'error');
    }
}

// ── Publish Action ───────────────────────────────────────────────────────────
async function publishVideo(filename, platform = 'all') {
    const targetLabel = platform === 'all' ? 'Instagram & YouTube' : platform.toUpperCase();
    showToast(`Publishing ${filename} to ${targetLabel}...`, 'info');

    // First save any unsaved metadata if this is the selected video
    if (state.selectedVideo && state.selectedVideo.filename === filename) {
        await saveMetadataChanges();
    }

    try {
        const res = await fetch('/api/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename,
                platforms: platform === 'all' ? ['all'] : [platform],
                dry_run: false
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`🎉 Published successfully to ${targetLabel}! Moved to Published Archive.`, 'success');
            // If the currently selected video was published, reset selected
            if (state.selectedVideo && state.selectedVideo.filename === filename) {
                state.selectedVideo = null;
            }
            state.activeTab = 'published';
            refreshAll();
        } else {
            showToast(`Publish failed: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (e) {
        showToast('Error publishing video.', 'error');
    }
}

// ── Batch Publish All ────────────────────────────────────────────────────────
async function publishAllReadyVideos() {
    if (!confirm('Are you sure you want to publish all ready videos in output/ to YouTube and Instagram?')) {
        return;
    }
    showToast('Publishing all ready videos to YouTube and Instagram in sequence...', 'info');
    try {
        const res = await fetch('/api/publish-all', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast('🎉 All videos published successfully!', 'success');
            state.selectedVideo = null;
            state.activeTab = 'published';
            refreshAll();
        } else {
            showToast(`Publish all failed: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (e) {
        showToast('Error during batch publishing.', 'error');
    }
}

// ── Delete Ready Video ───────────────────────────────────────────────────────
async function deleteReadyVideo(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}" from ready videos?`)) {
        return;
    }
    try {
        const res = await fetch('/api/video/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`🗑️ Deleted ${filename}`, 'info');
            if (state.selectedVideo && state.selectedVideo.filename === filename) {
                state.selectedVideo = null;
            }
            refreshAll();
        }
    } catch (e) {
        showToast('Error deleting video.', 'error');
    }
}

// ── UI View Renderers ────────────────────────────────────────────────────────

function renderHeader() {
    const igConfigured = state.status?.instagram?.configured;
    const igUsername = state.status?.instagram?.username || '@sun_27417';
    const igQuota = `${state.status?.instagram?.quota_usage ?? 15}/${state.status?.instagram?.quota_total ?? 100}`;

    const ytAuth = state.status?.youtube?.authenticated;
    const ytChannel = state.status?.youtube?.channel_title || 'EGO X';

    const readyCount = state.readyVideos?.length || 0;
    const publishedCount = state.publishedVideos?.length || 0;

    return `
    <header class="border-b border-white/10 bg-dark-900/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl glow-button flex items-center justify-center font-black text-xl text-white shadow-lg shadow-blue-500/30">
                ⚡
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <h1 class="text-xl font-bold tracking-tight text-white">AutoReelStudio</h1>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 font-semibold">
                        AI Social Studio
                    </span>
                </div>
                <p class="text-xs text-gray-400">Upload, AI Video Understanding & Instant Social Publishing</p>
            </div>
        </div>

        <!-- Real-time Connected Account Badges -->
        <div class="flex items-center space-x-3 text-xs">
            <!-- Instagram Status -->
            <div class="flex items-center space-x-2 px-3 py-1.5 rounded-xl glass-card border border-white/5">
                <span class="w-2.5 h-2.5 rounded-full ${igConfigured ? 'bg-pink-500 animate-pulse' : 'bg-gray-500'}"></span>
                <span class="text-gray-300 font-medium">Instagram:</span>
                <span class="text-white font-semibold font-mono">${igUsername}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-pink-500/10 text-pink-300 font-mono">Quota: ${igQuota}</span>
            </div>

            <!-- YouTube Status -->
            <div class="flex items-center space-x-2 px-3 py-1.5 rounded-xl glass-card border border-white/5">
                <span class="w-2.5 h-2.5 rounded-full ${ytAuth ? 'bg-red-500' : 'bg-gray-500'}"></span>
                <span class="text-gray-300 font-medium">YouTube:</span>
                <span class="text-white font-semibold font-mono">${ytChannel}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-300 font-mono">#Shorts</span>
            </div>

            <!-- Counts -->
            <div class="flex items-center space-x-1.5 font-mono text-xs">
                <span class="px-2.5 py-1.5 rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    Ready: <strong>${readyCount}</strong>
                </span>
                <span class="px-2.5 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Published: <strong>${publishedCount}</strong>
                </span>
            </div>
        </div>
    </header>
    `;
}

function renderSidebar() {
    const tabs = [
        { id: 'studio', label: 'Upload & AI Studio', icon: 'sparkles', badge: state.uploading ? 'Processing' : null },
        { id: 'ready', label: 'Ready Videos', icon: 'film', badge: state.readyVideos.length || null },
        { id: 'published', label: 'Published Archive', icon: 'check-circle-2', badge: state.publishedVideos.length || null },
        { id: 'insights', label: 'Channel Insights', icon: 'bar-chart-3', badge: null }
    ];

    return `
    <aside class="w-64 border-r border-white/10 bg-dark-900/40 p-4 space-y-2 hidden md:block shrink-0">
        <div class="text-[11px] font-semibold tracking-wider text-gray-500 uppercase px-3 py-2 font-mono">
            Navigation
        </div>
        ${tabs.map(tab => {
            const active = state.activeTab === tab.id;
            return `
            <button
                onclick="setTab('${tab.id}')"
                class="w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all ${
                    active
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20 font-semibold'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                }"
            >
                <div class="flex items-center space-x-3">
                    <i data-lucide="${tab.icon}" class="w-4 h-4"></i>
                    <span>${tab.label}</span>
                </div>
                ${tab.badge !== null ? `
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full ${
                        active ? 'bg-white/20 text-white font-bold' : 'bg-white/10 text-gray-300'
                    }">
                        ${tab.badge}
                    </span>
                ` : ''}
            </button>
            `;
        }).join('')}

        <!-- Dropzone Quick CTA -->
        <div class="pt-6">
            <div class="p-4 rounded-2xl glass-card border border-blue-500/20 bg-blue-500/5 text-center space-y-2">
                <i data-lucide="upload-cloud" class="w-6 h-6 text-blue-400 mx-auto"></i>
                <p class="text-xs font-semibold text-white">Instant Video Upload</p>
                <p class="text-[11px] text-gray-400">Gemini automatically reads scenes & writes viral captions.</p>
                <label class="block cursor-pointer">
                    <input type="file" accept="video/mp4,video/quicktime,video/webm" class="hidden" onchange="handleFileSelect(event)" />
                    <span class="block py-2 px-3 rounded-xl glow-button text-xs font-bold text-white shadow-md">
                        Select Video File
                    </span>
                </label>
            </div>
        </div>
    </aside>
    `;
}

// ── Tab 1: Upload & AI Studio ────────────────────────────────────────────────
function renderStudioTab() {
    const video = state.selectedVideo;

    return `
    <div class="space-y-6">
        <!-- Upload Banner / Dropzone -->
        <div
            id="dropzone"
            ondragover="handleDragOver(event)"
            ondragleave="handleDragLeave(event)"
            ondrop="handleDrop(event)"
            class="p-8 rounded-3xl glass-card border-2 border-dashed ${
                state.uploading ? 'border-blue-500 bg-blue-500/10' : 'border-white/15 hover:border-blue-500/50 hover:bg-white/5'
            } transition-all text-center space-y-3 cursor-pointer"
            onclick="document.getElementById('hiddenFileInput').click()"
        >
            <input type="file" id="hiddenFileInput" accept="video/mp4,video/quicktime,video/webm" class="hidden" onchange="handleFileSelect(event)" />
            <div class="w-16 h-16 rounded-2xl bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center mx-auto shadow-inner">
                <i data-lucide="${state.uploading ? 'loader' : 'upload-cloud'}" class="w-8 h-8 ${state.uploading ? 'animate-spin' : ''}"></i>
            </div>
            <div>
                <h3 class="text-lg font-bold text-white">
                    ${state.uploading ? 'Processing Video...' : 'Drag & Drop Video Here, or Click to Browse'}
                </h3>
                <p class="text-xs text-gray-400 max-w-md mx-auto mt-1">
                    Upload 9:16 vertical MP4, MOV, or WebM. Our AI engine instantly reads the visuals, speech, and hook to craft viral captions.
                </p>
            </div>

            ${state.uploading ? `
                <div class="max-w-md mx-auto space-y-2 pt-2">
                    <div class="w-full h-2 bg-dark-800 rounded-full overflow-hidden border border-white/10">
                        <div class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-300" style="width: ${state.uploadProgress}%"></div>
                    </div>
                    <p class="text-[11px] font-mono text-blue-300">${state.statusMessage} (${state.uploadProgress}%)</p>
                </div>
            ` : ''}
        </div>

        ${video ? renderVideoStudioEditor(video) : `
            <div class="p-12 text-center rounded-3xl glass-card border border-white/5 space-y-3">
                <i data-lucide="video" class="w-12 h-12 text-gray-600 mx-auto"></i>
                <h4 class="text-base font-semibold text-gray-300">No Video Selected</h4>
                <p class="text-xs text-gray-500 max-w-sm mx-auto">
                    Upload a new video above, or select any existing video from the <button onclick="setTab('ready')" class="text-blue-400 underline font-semibold">Ready Videos</button> gallery to review and publish.
                </p>
            </div>
        `}
    </div>
    `;
}

function renderVideoStudioEditor(video) {
    const hashtags = video.hashtags || [];
    const streamUrl = `/media/output/${encodeURIComponent(video.filename)}`;

    return `
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <!-- Left: 9:16 Vertical Video Player Mockup -->
        <div class="lg:col-span-5 space-y-4">
            <div class="relative rounded-3xl p-3 bg-gradient-to-b from-white/10 via-white/5 to-white/10 shadow-2xl border border-white/10">
                <div class="rounded-2xl overflow-hidden bg-black aspect-[9/16] relative flex items-center justify-center group">
                    <video
                        id="studioVideoPlayer"
                        src="${streamUrl}"
                        controls
                        playsinline
                        loop
                        poster="${video.thumbnail || ''}"
                        class="w-full h-full object-cover"
                    ></video>
                </div>
            </div>

            <!-- Technical Meta Pills -->
            <div class="p-4 rounded-2xl glass-card border border-white/5 space-y-2.5">
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">File Name:</span>
                    <span class="font-mono text-white font-medium truncate max-w-[220px]" title="${video.filename}">
                        ${video.filename}
                    </span>
                </div>
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">Resolution & Ratio:</span>
                    <span class="font-mono text-emerald-400 font-semibold">
                        ${video.width || 1080} x ${video.height || 1920} (9:16 Vertical)
                    </span>
                </div>
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">Duration & Size:</span>
                    <span class="font-mono text-blue-300 font-semibold">
                        ${(video.duration || 0).toFixed(1)}s • ${video.size_mb || 0} MB
                    </span>
                </div>
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">Faststart Atom:</span>
                    <span class="text-emerald-400 flex items-center space-x-1 font-semibold">
                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                        <span>CDN Streaming Ready</span>
                    </span>
                </div>
            </div>
        </div>

        <!-- Right: AI Reading & Metadata Publishing Studio -->
        <div class="lg:col-span-7 space-y-6">
            <!-- AI Reading Comprehension Card -->
            <div class="p-5 rounded-2xl glass-card border border-blue-500/20 bg-blue-500/5 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="text-base">🧠</span>
                        <h4 class="text-sm font-bold text-white">AI Video Reading & Scene Understanding</h4>
                    </div>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                        Gemini 2.5 Multimodal
                    </span>
                </div>
                <p class="text-xs text-gray-300 leading-relaxed">
                    <strong>Scene Actions:</strong> ${video.summary || 'Analyzing video scenes...'}
                </p>
                ${video.detected_audio ? `
                    <p class="text-xs text-indigo-300 leading-relaxed border-t border-white/5 pt-2">
                        <strong>Audio & Speech:</strong> ${video.detected_audio}
                    </p>
                ` : ''}
            </div>

            <!-- Title & Hook Editor -->
            <div class="p-5 rounded-2xl glass-card border border-white/10 space-y-4">
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between">
                        <label class="text-xs font-semibold text-gray-300 uppercase tracking-wider font-mono">
                            Video Title
                        </label>
                        <span class="text-[10px] text-gray-500 font-mono" id="titleCharCount">
                            ${(video.title || '').length} chars
                        </span>
                    </div>
                    <input
                        type="text"
                        id="videoTitleInput"
                        value="${escapeHtml(video.title || '')}"
                        oninput="updateTitle(this.value)"
                        placeholder="Catchy, viral title..."
                        class="w-full px-4 py-3 rounded-xl glass-card text-sm text-white font-semibold border border-white/10 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                </div>

                <!-- Instagram Caption Editor -->
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between">
                        <label class="text-xs font-semibold text-gray-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                            <span class="w-2 h-2 rounded-full bg-pink-500"></span>
                            <span>Instagram Reel Caption</span>
                        </label>
                        <button onclick="copyToClipboard(document.getElementById('igCaptionInput').value)" class="text-[11px] text-blue-400 hover:text-blue-300 font-mono">
                            Copy Caption
                        </button>
                    </div>
                    <textarea
                        id="igCaptionInput"
                        rows="6"
                        oninput="updateCaption(this.value)"
                        placeholder="Engaging caption with emojis and CTA..."
                        class="w-full p-4 rounded-xl glass-card text-xs text-gray-200 border border-white/10 focus:border-pink-500 focus:outline-none focus:ring-1 focus:ring-pink-500 leading-relaxed"
                    >${escapeHtml(video.instagram_caption || '')}</textarea>
                </div>

                <!-- YouTube Shorts Title & Description -->
                <div class="space-y-3 pt-2 border-t border-white/5">
                    <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-gray-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                            <span class="w-2 h-2 rounded-full bg-red-500"></span>
                            <span>YouTube Shorts Title</span>
                        </label>
                        <input
                            type="text"
                            id="ytTitleInput"
                            value="${escapeHtml(video.youtube_title || `${video.title || ''} #Shorts`)}"
                            oninput="updateYTTitle(this.value)"
                            placeholder="Title for YouTube Shorts..."
                            class="w-full px-4 py-2.5 rounded-xl glass-card text-xs text-white border border-white/10 focus:border-red-500 focus:outline-none"
                        />
                    </div>
                </div>

                <!-- Hashtags Cloud -->
                <div class="space-y-2 pt-2 border-t border-white/5">
                    <div class="flex items-center justify-between">
                        <label class="text-xs font-semibold text-gray-300 uppercase tracking-wider font-mono">
                            Targeted Hashtags (${hashtags.length})
                        </label>
                        <button onclick="copyToClipboard('${hashtags.join(' ')}')" class="text-[11px] text-blue-400 hover:text-blue-300 font-mono">
                            Copy All Tags
                        </button>
                    </div>
                    <div class="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-2 rounded-xl bg-dark-900 border border-white/5">
                        ${hashtags.map((tag, idx) => `
                            <span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20 group">
                                <span>${tag}</span>
                                <button onclick="removeHashtag(${idx})" class="text-blue-400 hover:text-red-400 transition-colors ml-1">
                                    ×
                                </button>
                            </span>
                        `).join('')}
                    </div>
                    <div class="flex items-center space-x-2">
                        <input
                            type="text"
                            id="newTagInput"
                            placeholder="Add tag (e.g. #Viral)..."
                            class="flex-1 px-3 py-1.5 rounded-lg glass-card text-xs text-white border border-white/10 focus:outline-none"
                            onkeydown="if(event.key==='Enter') addHashtag(this)"
                        />
                        <button onclick="addHashtag(document.getElementById('newTagInput'))" class="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-medium text-white">
                            Add Tag
                        </button>
                    </div>
                </div>

                <!-- Regenerate with Custom Instruction -->
                <div class="pt-3 border-t border-white/5 space-y-2">
                    <label class="text-[11px] text-gray-400 font-mono">Regenerate AI Captions with Custom Direction</label>
                    <div class="flex items-center space-x-2">
                        <input
                            type="text"
                            id="customInstructionInput"
                            placeholder="e.g. 'Make it funnier', 'Focus on emotions', 'Dramatic tone'..."
                            class="flex-1 px-3 py-2 rounded-xl glass-card text-xs text-white border border-white/10 focus:outline-none"
                            onkeydown="if(event.key==='Enter') reanalyzeVideo(this.value)"
                        />
                        <button
                            onclick="reanalyzeVideo(document.getElementById('customInstructionInput').value)"
                            class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white flex items-center space-x-1.5 shadow-md shadow-indigo-500/30 shrink-0"
                            ${state.analyzing ? 'disabled' : ''}
                        >
                            <i data-lucide="${state.analyzing ? 'loader' : 'sparkles'}" class="w-3.5 h-3.5 ${state.analyzing ? 'animate-spin' : ''}"></i>
                            <span>${state.analyzing ? 'Thinking...' : 'Regenerate'}</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Publishing Action Buttons -->
            <div class="p-5 rounded-2xl glass-card border border-white/10 space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-gray-300 font-mono uppercase tracking-wider">
                        Publish to Platforms
                    </span>
                    <button onclick="saveMetadataChanges()" class="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center space-x-1">
                        <i data-lucide="save" class="w-3.5 h-3.5"></i>
                        <span>Save Edits</span>
                    </button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <button
                        onclick="publishVideo('${video.filename}', 'instagram')"
                        class="ig-gradient-btn py-3.5 px-4 rounded-xl text-xs font-bold text-white flex items-center justify-center space-x-2 shadow-lg"
                    >
                        <i data-lucide="instagram" class="w-4 h-4"></i>
                        <span>Publish Instagram</span>
                    </button>

                    <button
                        onclick="publishVideo('${video.filename}', 'youtube')"
                        class="yt-gradient-btn py-3.5 px-4 rounded-xl text-xs font-bold text-white flex items-center justify-center space-x-2 shadow-lg"
                    >
                        <i data-lucide="youtube" class="w-4 h-4"></i>
                        <span>Publish YouTube</span>
                    </button>

                    <button
                        onclick="publishVideo('${video.filename}', 'all')"
                        class="glow-button py-3.5 px-4 rounded-xl text-xs font-bold text-white flex items-center justify-center space-x-2 shadow-lg"
                    >
                        <i data-lucide="rocket" class="w-4 h-4"></i>
                        <span>Publish to Both</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
}

// ── Tab 2: Ready Videos ──────────────────────────────────────────────────────
function renderReadyTab() {
    const videos = state.readyVideos;

    return `
    <div class="space-y-6">
        <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
                <h2 class="text-xl font-bold text-white">Ready Videos (${videos.length})</h2>
                <p class="text-xs text-gray-400">Uploaded videos with generated captions waiting in output/ to be published.</p>
            </div>
            <div class="flex items-center space-x-3">
                <button
                    onclick="document.getElementById('hiddenFileInput').click()"
                    class="py-2.5 px-4 rounded-xl glass-card hover:bg-white/10 text-xs font-semibold text-white flex items-center space-x-2"
                >
                    <i data-lucide="plus" class="w-4 h-4"></i>
                    <span>Upload Video</span>
                </button>
                ${videos.length > 0 ? `
                    <button
                        onclick="publishAllReadyVideos()"
                        class="glow-button py-2.5 px-4 rounded-xl text-xs font-bold text-white flex items-center space-x-2 shadow-lg"
                    >
                        <i data-lucide="send" class="w-4 h-4"></i>
                        <span>Publish All Ready (${videos.length})</span>
                    </button>
                ` : ''}
            </div>
        </div>

        ${videos.length === 0 ? `
            <div class="p-16 rounded-3xl glass-card border border-white/5 text-center space-y-3">
                <i data-lucide="film" class="w-12 h-12 text-gray-600 mx-auto"></i>
                <h4 class="text-base font-semibold text-gray-300">No Videos Waiting in output/</h4>
                <p class="text-xs text-gray-500 max-w-sm mx-auto">
                    Upload a video to analyze it with AI and prepare it for Instagram Reels and YouTube Shorts.
                </p>
                <button
                    onclick="setTab('studio')"
                    class="mt-2 inline-flex items-center space-x-2 py-2 px-4 rounded-xl glow-button text-xs font-bold text-white"
                >
                    <i data-lucide="sparkles" class="w-4 h-4"></i>
                    <span>Open Upload Studio</span>
                </button>
            </div>
        ` : `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                ${videos.map(v => renderReadyVideoCard(v)).join('')}
            </div>
        `}
    </div>
    `;
}

function renderReadyVideoCard(video) {
    const streamUrl = `/media/output/${encodeURIComponent(video.filename)}`;
    const thumbUrl = video.thumbnail || '';

    return `
    <div class="glass-card glass-card-hover rounded-2xl overflow-hidden border border-white/10 flex flex-col justify-between">
        <!-- Thumbnail & Duration Badge -->
        <div class="relative aspect-video bg-dark-900 overflow-hidden cursor-pointer group" onclick="selectVideo('${video.filename}')">
            ${thumbUrl ? `
                <img src="${thumbUrl}" alt="${video.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            ` : `
                <div class="w-full h-full flex items-center justify-center text-gray-600">
                    <i data-lucide="video" class="w-10 h-10"></i>
                </div>
            `}
            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div class="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white shadow-xl">
                    <i data-lucide="play" class="w-5 h-5 ml-0.5"></i>
                </div>
            </div>
            <span class="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-sm text-[10px] font-mono text-white font-semibold">
                ${(video.duration || 0).toFixed(1)}s
            </span>
            <span class="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-blue-600/80 backdrop-blur-sm text-[10px] font-mono text-white font-semibold">
                ${video.size_mb || 0} MB
            </span>
        </div>

        <!-- Content Details -->
        <div class="p-4 space-y-2.5 flex-1 flex flex-col justify-between">
            <div class="space-y-1.5">
                <h4 class="text-sm font-bold text-white line-clamp-1" title="${video.title}">
                    ${video.title || video.filename}
                </h4>
                <p class="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                    ${video.instagram_caption || video.summary || 'Ready for social publishing.'}
                </p>
            </div>

            <!-- Action Buttons -->
            <div class="pt-3 border-t border-white/5 space-y-2">
                <div class="grid grid-cols-2 gap-2">
                    <button
                        onclick="selectVideo('${video.filename}')"
                        class="py-2 px-3 rounded-xl bg-white/10 hover:bg-white/15 text-xs font-semibold text-white flex items-center justify-center space-x-1.5 transition-colors"
                    >
                        <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                        <span>Edit Studio</span>
                    </button>
                    <button
                        onclick="deleteReadyVideo('${video.filename}')"
                        class="py-2 px-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-xs font-semibold text-red-300 flex items-center justify-center space-x-1.5 transition-colors"
                    >
                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        <span>Delete</span>
                    </button>
                </div>

                <div class="grid grid-cols-2 gap-2">
                    <button
                        onclick="publishVideo('${video.filename}', 'instagram')"
                        class="ig-gradient-btn py-2 px-3 rounded-xl text-xs font-bold text-white flex items-center justify-center space-x-1 shadow-md"
                    >
                        <i data-lucide="instagram" class="w-3.5 h-3.5"></i>
                        <span>Instagram</span>
                    </button>
                    <button
                        onclick="publishVideo('${video.filename}', 'youtube')"
                        class="yt-gradient-btn py-2 px-3 rounded-xl text-xs font-bold text-white flex items-center justify-center space-x-1 shadow-md"
                    >
                        <i data-lucide="youtube" class="w-3.5 h-3.5"></i>
                        <span>YouTube</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
}

// ── Tab 3: Published Archive ─────────────────────────────────────────────────
function renderPublishedTab() {
    let list = state.publishedVideos;

    if (state.publishedFilter === 'instagram') {
        list = list.filter(v => Boolean(v.instagram_url || v.instagram_id));
    } else if (state.publishedFilter === 'youtube') {
        list = list.filter(v => Boolean(v.youtube_url));
    }

    return `
    <div class="space-y-6">
        <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
                <h2 class="text-xl font-bold text-white">Published Videos Archive (${state.publishedVideos.length})</h2>
                <p class="text-xs text-gray-400">All live Instagram Reels & YouTube Shorts with direct links.</p>
            </div>

            <!-- Filter Pills -->
            <div class="flex items-center space-x-1.5 p-1 rounded-xl glass-card border border-white/5 text-xs font-mono">
                <button
                    onclick="setPublishedFilter('all')"
                    class="px-3 py-1.5 rounded-lg transition-all ${state.publishedFilter === 'all' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-white'}"
                >
                    All (${state.publishedVideos.length})
                </button>
                <button
                    onclick="setPublishedFilter('instagram')"
                    class="px-3 py-1.5 rounded-lg transition-all ${state.publishedFilter === 'instagram' ? 'bg-pink-600 text-white font-bold' : 'text-gray-400 hover:text-white'}"
                >
                    Instagram (${state.publishedVideos.filter(v => v.instagram_url).length})
                </button>
                <button
                    onclick="setPublishedFilter('youtube')"
                    class="px-3 py-1.5 rounded-lg transition-all ${state.publishedFilter === 'youtube' ? 'bg-red-600 text-white font-bold' : 'text-gray-400 hover:text-white'}"
                >
                    YouTube (${state.publishedVideos.filter(v => v.youtube_url).length})
                </button>
            </div>
        </div>

        ${list.length === 0 ? `
            <div class="p-16 rounded-3xl glass-card border border-white/5 text-center space-y-3">
                <i data-lucide="check-circle-2" class="w-12 h-12 text-gray-600 mx-auto"></i>
                <h4 class="text-base font-semibold text-gray-300">No Published Videos in this view</h4>
                <p class="text-xs text-gray-500 max-w-sm mx-auto">
                    Publish your ready videos to see live links, timestamps, and platform performance.
                </p>
            </div>
        ` : `
            <div class="space-y-3">
                ${list.map(v => renderPublishedRow(v)).join('')}
            </div>
        `}
    </div>
    `;
}

function renderPublishedRow(v) {
    const streamUrl = `/media/published/${encodeURIComponent(v.filename)}`;
    const pubDate = v.published_at ? new Date(v.published_at).toLocaleString() : 'Recently';

    return `
    <div class="p-4 rounded-2xl glass-card border border-white/10 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center space-x-4 min-w-[280px] flex-1">
            <div class="w-14 h-20 rounded-xl bg-dark-900 border border-white/10 overflow-hidden relative shrink-0">
                ${v.thumbnail ? `
                    <img src="${v.thumbnail}" class="w-full h-full object-cover" />
                ` : `
                    <div class="w-full h-full flex items-center justify-center text-gray-600 text-xs font-mono">9:16</div>
                `}
            </div>
            <div class="space-y-1 flex-1">
                <h4 class="text-sm font-bold text-white line-clamp-1">${v.title || v.filename}</h4>
                <p class="text-xs text-gray-400 line-clamp-1 font-mono">${v.filename}</p>
                <div class="flex items-center space-x-2 text-[11px] text-gray-500 font-mono">
                    <i data-lucide="clock" class="w-3 h-3"></i>
                    <span>Published: ${pubDate}</span>
                </div>
            </div>
        </div>

        <!-- Live Direct Links -->
        <div class="flex items-center space-x-3">
            ${v.instagram_url ? `
                <a
                    href="${v.instagram_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="py-2 px-3.5 rounded-xl ig-gradient-btn text-xs font-bold text-white flex items-center space-x-1.5 shadow-md"
                >
                    <i data-lucide="instagram" class="w-4 h-4"></i>
                    <span>View Reel</span>
                    <i data-lucide="external-link" class="w-3 h-3"></i>
                </a>
            ` : `
                <span class="text-xs font-mono text-gray-600 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
                    Not on Instagram
                </span>
            `}

            ${v.youtube_url ? `
                <a
                    href="${v.youtube_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="py-2 px-3.5 rounded-xl yt-gradient-btn text-xs font-bold text-white flex items-center space-x-1.5 shadow-md"
                >
                    <i data-lucide="youtube" class="w-4 h-4"></i>
                    <span>View Short</span>
                    <i data-lucide="external-link" class="w-3 h-3"></i>
                </a>
            ` : `
                <span class="text-xs font-mono text-gray-600 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
                    Not on YouTube
                </span>
            `}

            <a
                href="${streamUrl}"
                target="_blank"
                class="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                title="Watch MP4 file"
            >
                <i data-lucide="play" class="w-4 h-4"></i>
            </a>
        </div>
    </div>
    `;
}

// ── Tab 4: Channel Insights ──────────────────────────────────────────────────
function renderInsightsTab() {
    const ig = state.status?.instagram || {};
    const yt = state.status?.youtube || {};

    return `
    <div class="space-y-6">
        <div>
            <h2 class="text-xl font-bold text-white">Connected Platforms & Channel Insights</h2>
            <p class="text-xs text-gray-400">Live API credentials and publishing limits.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Instagram Card -->
            <div class="p-6 rounded-3xl glass-card border border-pink-500/20 bg-pink-500/5 space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 rounded-2xl ig-gradient-btn flex items-center justify-center text-white">
                            <i data-lucide="instagram" class="w-5 h-5"></i>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-white">Instagram Reels</h3>
                            <p class="text-xs text-gray-400 font-mono">Meta Graph API v21.0</p>
                        </div>
                    </div>
                    <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${
                        ig.configured ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/20 text-red-300'
                    }">
                        ${ig.configured ? 'Connected' : 'Missing Config'}
                    </span>
                </div>

                <div class="space-y-2 text-xs">
                    <div class="flex items-center justify-between py-1.5 border-b border-white/5">
                        <span class="text-gray-400">Username:</span>
                        <span class="font-mono text-white font-semibold">${ig.username || '@sun_27417'}</span>
                    </div>
                    <div class="flex items-center justify-between py-1.5 border-b border-white/5">
                        <span class="text-gray-400">Account ID:</span>
                        <span class="font-mono text-white font-semibold">${ig.id || '17841476861770479'}</span>
                    </div>
                    <div class="flex items-center justify-between py-1.5 border-b border-white/5">
                        <span class="text-gray-400">Daily Upload Quota:</span>
                        <span class="font-mono text-pink-300 font-semibold">${ig.quota_usage || 15} / ${ig.quota_total || 100} reels</span>
                    </div>
                    <div class="flex items-center justify-between py-1.5">
                        <span class="text-gray-400">Ingestion Method:</span>
                        <span class="font-mono text-emerald-300">Direct Binary Resumable (No Tunnels)</span>
                    </div>
                </div>
            </div>

            <!-- YouTube Card -->
            <div class="p-6 rounded-3xl glass-card border border-red-500/20 bg-red-500/5 space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 rounded-2xl yt-gradient-btn flex items-center justify-center text-white">
                            <i data-lucide="youtube" class="w-5 h-5"></i>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-white">YouTube Shorts</h3>
                            <p class="text-xs text-gray-400 font-mono">Google Data API v3</p>
                        </div>
                    </div>
                    <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${
                        yt.authenticated ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/20 text-red-300'
                    }">
                        ${yt.authenticated ? 'Authenticated' : 'OAuth Pending'}
                    </span>
                </div>

                <div class="space-y-2 text-xs">
                    <div class="flex items-center justify-between py-1.5 border-b border-white/5">
                        <span class="text-gray-400">Channel Name:</span>
                        <span class="font-mono text-white font-semibold">${yt.channel_title || 'EGO X'}</span>
                    </div>
                    <div class="flex items-center justify-between py-1.5 border-b border-white/5">
                        <span class="text-gray-400">Channel ID:</span>
                        <span class="font-mono text-white font-semibold">${yt.channel_id || 'UCf_xwFloctn-uTqgSc9p8Ew'}</span>
                    </div>
                    <div class="flex items-center justify-between py-1.5 border-b border-white/5">
                        <span class="text-gray-400">Subscribers:</span>
                        <span class="font-mono text-red-300 font-semibold">${yt.subscribers || '1'}</span>
                    </div>
                    <div class="flex items-center justify-between py-1.5">
                        <span class="text-gray-400">Default Category:</span>
                        <span class="font-mono text-emerald-300">Entertainment (24) #Shorts</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
}

// ── Toast Renderer ───────────────────────────────────────────────────────────
function renderToast() {
    if (!state.toast) return '';
    const isError = state.toast.type === 'error';
    const isInfo = state.toast.type === 'info';

    return `
    <div class="fixed bottom-6 right-6 z-50 animate-bounce duration-200">
        <div class="px-5 py-3 rounded-2xl glass-card border ${
            isError ? 'border-red-500/50 bg-red-950/90 text-red-200' :
            isInfo ? 'border-blue-500/50 bg-blue-950/90 text-blue-200' :
            'border-emerald-500/50 bg-emerald-950/90 text-emerald-200'
        } shadow-2xl flex items-center space-x-3 text-xs font-semibold">
            <span>${isError ? '⚠️' : isInfo ? 'ℹ️' : '✅'}</span>
            <span>${state.toast.message}</span>
        </div>
    </div>
    `;
}

// ── Master Render Loop ───────────────────────────────────────────────────────
function render() {
    const root = document.getElementById('app');
    if (!root) return;

    let content = '';
    if (state.activeTab === 'studio') {
        content = renderStudioTab();
    } else if (state.activeTab === 'ready') {
        content = renderReadyTab();
    } else if (state.activeTab === 'published') {
        content = renderPublishedTab();
    } else if (state.activeTab === 'insights') {
        content = renderInsightsTab();
    }

    root.innerHTML = `
        ${renderHeader()}
        <div class="flex-1 flex overflow-hidden">
            ${renderSidebar()}
            <main class="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
                ${content}
            </main>
        </div>
        ${renderToast()}
    `;

    // Refresh Lucide Icons
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// ── Global Helper Functions ──────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function setTab(tabId) {
    state.activeTab = tabId;
    render();
}

function setPublishedFilter(f) {
    state.publishedFilter = f;
    render();
}

function selectVideo(filename) {
    const match = state.readyVideos.find(v => v.filename === filename);
    if (match) {
        state.selectedVideo = match;
        state.activeTab = 'studio';
        render();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function updateTitle(val) {
    if (state.selectedVideo) {
        state.selectedVideo.title = val;
        const el = document.getElementById('titleCharCount');
        if (el) el.innerText = `${val.length} chars`;
    }
}

function updateCaption(val) {
    if (state.selectedVideo) {
        state.selectedVideo.instagram_caption = val;
    }
}

function updateYTTitle(val) {
    if (state.selectedVideo) {
        state.selectedVideo.youtube_title = val;
    }
}

function removeHashtag(idx) {
    if (state.selectedVideo && state.selectedVideo.hashtags) {
        state.selectedVideo.hashtags.splice(idx, 1);
        render();
    }
}

function addHashtag(inputEl) {
    if (!inputEl || !inputEl.value.trim() || !state.selectedVideo) return;
    let tag = inputEl.value.trim();
    if (!tag.startsWith('#')) tag = '#' + tag;
    state.selectedVideo.hashtags = state.selectedVideo.hashtags || [];
    if (!state.selectedVideo.hashtags.includes(tag)) {
        state.selectedVideo.hashtags.push(tag);
        inputEl.value = '';
        render();
    }
}

function copyToClipboard(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast('📋 Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy.', 'error');
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropzone = document.getElementById('dropzone');
    if (dropzone) dropzone.classList.add('border-blue-500', 'bg-blue-500/10');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropzone = document.getElementById('dropzone');
    if (dropzone) dropzone.classList.remove('border-blue-500', 'bg-blue-500/10');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropzone = document.getElementById('dropzone');
    if (dropzone) dropzone.classList.remove('border-blue-500', 'bg-blue-500/10');

    if (e.dataTransfer && e.dataTransfer.files.length > 0) {
        uploadVideoFile(e.dataTransfer.files[0]);
    }
}

function handleFileSelect(e) {
    if (e.target && e.target.files.length > 0) {
        uploadVideoFile(e.target.files[0]);
    }
}

// ── Startup ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    refreshAll();
    // Poll every 8s for live quota & status
    setInterval(refreshAll, 8000);
});
