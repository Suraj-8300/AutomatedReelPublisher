const { useState, useEffect, useRef } = React;

// ── Icons Helper Component using Lucide ──────────────────────────────────
function Icon({ name, className = "w-5 h-5", size = 20 }) {
    useEffect(() => {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }, [name]);
    return <i data-lucide={name} className={className} style={{ width: size, height: size }}></i>;
}

// ── Main App Component ──────────────────────────────────────────────────
function App() {
    const [activeTab, setActiveTab] = useState("ready"); // 'create', 'upload', 'ready', 'instagram', 'youtube', 'settings'
    const [status, setStatus] = useState(null);
    const [readyVideos, setReadyVideos] = useState([]);
    const [publishedVideos, setPublishedVideos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    // Generation state
    const [genState, setGenState] = useState(null);
    const [pillar, setPillar] = useState("animal_story");
    const [prompt, setPrompt] = useState("");
    const [voice, setVoice] = useState("female");
    const [music, setMusic] = useState("heartwarming_story");
    const [visuals, setVisuals] = useState("broll");
    const [isGenerating, setIsGenerating] = useState(false);

    // Video preview modal
    const [previewVideo, setPreviewVideo] = useState(null);

    // Fetch initial data
    const refreshData = async () => {
        try {
            const [statusRes, readyRes, pubRes] = await Promise.all([
                fetch("/api/status").then(r => r.json()),
                fetch("/api/videos/ready").then(r => r.json()),
                fetch("/api/videos/published").then(r => r.json()),
            ]);
            setStatus(statusRes);
            setReadyVideos(readyRes.videos || []);
            setPublishedVideos(pubRes.published || []);
        } catch (e) {
            console.error("Error refreshing data:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshData();
        const interval = setInterval(refreshData, 8000);
        return () => clearInterval(interval);
    }, []);

    // Poll generation status
    useEffect(() => {
        const pollGen = async () => {
            try {
                const res = await fetch("/api/generate/status");
                const data = await res.json();
                setGenState(data);
                setIsGenerating(data.is_generating);
                if (data.is_generating) {
                    refreshData();
                }
            } catch (e) {}
        };
        const intv = setInterval(pollGen, 2500);
        return () => clearInterval(intv);
    }, []);

    const showToast = (message, type = "success") => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    };

    // Publish action
    const handlePublish = async (filename, platform = "all") => {
        showToast(`Publishing ${filename} to ${platform.toUpperCase()}...`, "info");
        try {
            const res = await fetch("/api/publish", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filename,
                    platforms: platform === "all" ? ["all"] : [platform],
                    dry_run: false
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`🎉 Successfully published ${filename}! Moved to published/`, "success");
                refreshData();
            } else {
                showToast(`❌ Publish failed: ${data.error || "Unknown error"}`, "error");
            }
        } catch (e) {
            showToast(`❌ Network error: ${e.message}`, "error");
        }
    };

    // Trigger generation
    const handleStartGenerate = async () => {
        setIsGenerating(true);
        showToast("Started video synthesis. AI brain is generating script & sourcing visuals...", "info");
        try {
            const res = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pillar,
                    prompt: prompt.trim() || "auto",
                    voice,
                    music,
                    visuals
                })
            });
            const data = await res.json();
            if (data.status === "started") {
                setActiveTab("ready");
            } else {
                showToast(data.error || "Generation error", "error");
            }
        } catch (e) {
            showToast(e.message, "error");
        }
    };

    return (
        <div className="flex h-screen overflow-hidden bg-dark-900">
            {/* ── Sidebar ── */}
            <aside className="w-72 glass-panel border-r border-white/5 flex flex-col justify-between z-20">
                <div>
                    {/* Brand */}
                    <div className="p-6 border-b border-white/5">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
                                <span className="text-xl">🎬</span>
                            </div>
                            <div>
                                <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-blue-400 bg-clip-text text-transparent">
                                    AutoReelStudio
                                </h1>
                                <p className="text-xs text-gray-400 font-mono">Modern AI Studio v2.5</p>
                            </div>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="p-4 space-y-1.5">
                        <NavItem
                            icon="film"
                            label="Ready Videos"
                            active={activeTab === "ready"}
                            badge={readyVideos.length}
                            badgeColor="bg-blue-600/30 text-blue-400 border border-blue-500/30"
                            onClick={() => setActiveTab("ready")}
                        />
                        <NavItem
                            icon="sparkles"
                            label="Create & Generate"
                            active={activeTab === "create"}
                            onClick={() => setActiveTab("create")}
                        />
                        <NavItem
                            icon="upload-cloud"
                            label="Upload Video"
                            active={activeTab === "upload"}
                            onClick={() => setActiveTab("upload")}
                        />
                        <div className="pt-4 pb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono">
                            Distribution Hub
                        </div>
                        <NavItem
                            icon="instagram"
                            label="Instagram Reels"
                            active={activeTab === "instagram"}
                            badge={publishedVideos.filter(v => v.instagram_url || v.instagram_id).length}
                            badgeColor="bg-pink-500/20 text-pink-400 border border-pink-500/30"
                            onClick={() => setActiveTab("instagram")}
                        />
                        <NavItem
                            icon="youtube"
                            label="YouTube Shorts"
                            active={activeTab === "youtube"}
                            badge={publishedVideos.filter(v => v.youtube_url).length}
                            badgeColor="bg-red-500/20 text-red-400 border border-red-500/30"
                            onClick={() => setActiveTab("youtube")}
                        />
                        <div className="pt-4 pb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono">
                            Configuration
                        </div>
                        <NavItem
                            icon="settings"
                            label="System & Credentials"
                            active={activeTab === "settings"}
                            onClick={() => setActiveTab("settings")}
                        />
                    </nav>
                </div>

                {/* Footer Live Channels */}
                <div className="p-4 border-t border-white/5 space-y-2 bg-dark-800/40">
                    <div className="flex items-center justify-between text-xs text-gray-400 px-1 font-mono">
                        <span>Connected Channels</span>
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    </div>
                    {status && (
                        <div className="space-y-1.5">
                            <div className="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 text-xs">
                                <div className="flex items-center space-x-2">
                                    <span>📸</span>
                                    <span className="font-medium text-gray-300">{status.instagram.username || "@sun_27417"}</span>
                                </div>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">Live</span>
                            </div>
                            <div className="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 text-xs">
                                <div className="flex items-center space-x-2">
                                    <span>▶️</span>
                                    <span className="font-medium text-gray-300">{status.youtube.channel_title || "EGO X"}</span>
                                </div>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">Ready</span>
                            </div>
                        </div>
                    )}
                </div>
            </aside>

            {/* ── Main Content Area ── */}
            <main className="flex-1 flex flex-col overflow-hidden bg-dark-900">
                {/* Header Bar */}
                <header className="h-16 glass-panel border-b border-white/5 flex items-center justify-between px-8 z-10">
                    <div>
                        <h2 className="text-base font-semibold capitalize flex items-center space-x-2">
                            <span>{getTabTitle(activeTab)}</span>
                        </h2>
                    </div>
                    <div className="flex items-center space-x-4">
                        {isGenerating && (
                            <div className="flex items-center space-x-2.5 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs text-blue-400 font-mono animate-pulse">
                                <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                                <span>{genState?.status_message || "Generating Reel..."}</span>
                            </div>
                        )}
                        <button
                            onClick={refreshData}
                            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 border border-white/5 transition"
                            title="Refresh Data"
                        >
                            <Icon name="refresh-cw" className="w-4 h-4" />
                        </button>
                    </div>
                </header>

                {/* Tab Body */}
                <div className="flex-1 overflow-y-auto p-8">
                    {activeTab === "ready" && (
                        <ReadyVideosTab
                            videos={readyVideos}
                            onPublish={handlePublish}
                            onPreview={setPreviewVideo}
                            onGoToCreate={() => setActiveTab("create")}
                        />
                    )}
                    {activeTab === "create" && (
                        <CreateTab
                            pillar={pillar} setPillar={setPillar}
                            prompt={prompt} setPrompt={setPrompt}
                            voice={voice} setVoice={setVoice}
                            music={music} setMusic={setMusic}
                            visuals={visuals} setVisuals={setVisuals}
                            onGenerate={handleStartGenerate}
                            isGenerating={isGenerating}
                            genState={genState}
                        />
                    )}
                    {activeTab === "upload" && (
                        <UploadTab
                            onUploadSuccess={() => {
                                refreshData();
                                setActiveTab("ready");
                                showToast("Video uploaded and optimized! Ready to publish.", "success");
                            }}
                        />
                    )}
                    {activeTab === "instagram" && (
                        <InstagramTab
                            published={publishedVideos}
                            onPreview={setPreviewVideo}
                        />
                    )}
                    {activeTab === "youtube" && (
                        <YouTubeTab
                            published={publishedVideos}
                            onPreview={setPreviewVideo}
                        />
                    )}
                    {activeTab === "settings" && (
                        <SettingsTab status={status} />
                    )}
                </div>
            </main>

            {/* ── Toast Notification ── */}
            {toast && (
                <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-3 px-4 py-3 rounded-xl shadow-2xl glass-panel border border-white/10 text-sm animate-bounce">
                    <span>{toast.type === "error" ? "❌" : toast.type === "info" ? "⚡" : "✅"}</span>
                    <span>{toast.message}</span>
                </div>
            )}

            {/* ── Video Preview Modal ── */}
            {previewVideo && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md" onClick={() => setPreviewVideo(null)}>
                    <div className="relative glass-card rounded-2xl max-w-sm w-full p-4 overflow-hidden border border-white/20" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between pb-3 border-b border-white/10">
                            <h3 className="text-sm font-semibold truncate pr-4">{previewVideo.title}</h3>
                            <button onClick={() => setPreviewVideo(null)} className="p-1 rounded-lg hover:bg-white/10 text-gray-400">
                                <Icon name="x" className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="mt-3 aspect-[9/16] bg-black rounded-xl overflow-hidden shadow-2xl">
                            <video
                                src={previewVideo.stream_url}
                                controls
                                autoPlay
                                className="w-full h-full object-contain"
                            ></video>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ── Navigation Item ──────────────────────────────────────────────────────
function NavItem({ icon, label, active, badge, badgeColor, onClick }) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                active
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm"
                    : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
            }`}
        >
            <div className="flex items-center space-x-3">
                <Icon name={icon} className={`w-4 h-4 ${active ? "text-blue-400" : "text-gray-400"}`} />
                <span>{label}</span>
            </div>
            {badge !== undefined && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${badgeColor || "bg-white/10 text-gray-300"}`}>
                    {badge}
                </span>
            )}
        </button>
    );
}

function getTabTitle(tab) {
    switch (tab) {
        case "ready": return "🎬 Ready Videos in output/ (Awaiting Publication)";
        case "create": return "🪄 AI Video Studio (Generate Blockbuster Reels)";
        case "upload": return "📤 Upload & Package Custom Reel";
        case "instagram": return "📸 Instagram Reels Published Hub";
        case "youtube": return "▶️ YouTube Shorts Published Hub";
        case "settings": return "🔐 Credentials, Quotas & Storage Audit";
        default: return "";
    }
}

// ── Tab: Ready Videos ────────────────────────────────────────────────────
function ReadyVideosTab({ videos, onPublish, onPreview, onGoToCreate }) {
    if (videos.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-96 glass-card rounded-2xl p-8 text-center border-dashed border-white/10">
                <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center text-3xl mb-4">
                    🎬
                </div>
                <h3 className="text-lg font-bold text-gray-200">No Videos in output/</h3>
                <p className="text-sm text-gray-400 max-w-sm mt-1 mb-6">
                    All generated reels have been published and safely archived into published/!
                </p>
                <button
                    onClick={onGoToCreate}
                    className="glow-button px-5 py-2.5 rounded-xl font-semibold text-sm text-white flex items-center space-x-2"
                >
                    <Icon name="sparkles" className="w-4 h-4" />
                    <span>Generate New 9:16 Reel</span>
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">
                    Found <span className="font-semibold text-white">{videos.length}</span> video(s) ready in <code className="text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded font-mono">output/</code>.
                    Publishing moves them automatically to <code className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-mono">published/</code>.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {videos.map(v => (
                    <div key={v.filename} className="glass-card rounded-2xl overflow-hidden flex flex-col justify-between group">
                        {/* Video thumbnail / player preview */}
                        <div
                            onClick={() => onPreview(v)}
                            className="relative aspect-[9/16] max-h-72 bg-dark-800 cursor-pointer overflow-hidden flex items-center justify-center"
                        >
                            <video
                                src={v.stream_url}
                                className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                                preload="metadata"
                            />
                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                                <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white shadow-xl">
                                    <Icon name="play" className="w-6 h-6 ml-1" />
                                </div>
                            </div>
                            <span className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur text-[11px] font-mono text-gray-300">
                                {v.size_mb} MB
                            </span>
                        </div>

                        {/* Metadata & Actions */}
                        <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                            <div>
                                <h4 className="font-semibold text-sm line-clamp-2 text-gray-100">{v.title}</h4>
                                <p className="text-xs text-gray-400 font-mono mt-1">{v.created_at}</p>
                            </div>

                            <div className="space-y-2 pt-2 border-t border-white/5">
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => onPublish(v.filename, "instagram")}
                                        className="px-3 py-2 rounded-lg bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 border border-pink-500/30 text-xs font-medium flex items-center justify-center space-x-1.5 transition"
                                    >
                                        <Icon name="instagram" className="w-3.5 h-3.5" />
                                        <span>Instagram</span>
                                    </button>
                                    <button
                                        onClick={() => onPublish(v.filename, "youtube")}
                                        className="px-3 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium flex items-center justify-center space-x-1.5 transition"
                                    >
                                        <Icon name="youtube" className="w-3.5 h-3.5" />
                                        <span>YouTube</span>
                                    </button>
                                </div>
                                <button
                                    onClick={() => onPublish(v.filename, "all")}
                                    className="w-full glow-button py-2 rounded-lg text-white text-xs font-semibold flex items-center justify-center space-x-2 shadow-md"
                                >
                                    <Icon name="send" className="w-3.5 h-3.5" />
                                    <span>Publish to Both (IG + YT)</span>
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Tab: Create & Generate ────────────────────────────────────────────────
function CreateTab({
    pillar, setPillar, prompt, setPrompt, voice, setVoice,
    music, setMusic, visuals, setVisuals, onGenerate, isGenerating, genState
}) {
    const pillars = [
        { id: "animal_story", name: "🐾 Animal Story", desc: "The Dodo / GeoBeats style rescue journey with live-action B-Roll" },
        { id: "ugc_lifestyle", name: "🍾 UGC Lifestyle Ad", desc: "Consistent female creator & verified product glass bottle showcase" },
        { id: "anthropomorphic_animal", name: "🐱 Animal with Human Job", desc: "British Cat Waiter, Street Food Cat Chef, Police Cat" },
        { id: "ai_baby_adult", name: "👶 Baby in Adult Role", desc: "Golgappa Stall baby, luxury podcast, CEO infant" },
        { id: "brainrot_meme", name: "🍕 Italian Brainrot", desc: "Ballerina Cappuccina, Tralalero Tralala surreal meme duos" },
        { id: "cinematic", name: "🌌 Cinematic Sci-Fi", desc: "Neutron stars, cosmic voyages, surreal worldbuilding" },
        { id: "science", name: "🔬 Science & News", desc: "Mars water, CRISPR breakthrough, factual discoveries" },
        { id: "mechanical", name: "⚙️ Mechanical Explainer", desc: "Turbocharger, jet engine, transmission kinetic animations" },
    ];

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Generation Progress Indicator */}
            {isGenerating && (
                <div className="glass-card rounded-2xl p-6 border-blue-500/40 bg-blue-950/20 space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <span className="animate-spin text-2xl">⚙️</span>
                            <div>
                                <h4 className="font-bold text-sm text-blue-400">Generation In Progress</h4>
                                <p className="text-xs text-gray-300 font-mono mt-0.5">{genState?.status_message}</p>
                            </div>
                        </div>
                        <span className="font-mono text-xs text-blue-400">{genState?.progress || 30}%</span>
                    </div>
                    <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                        <div
                            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${genState?.progress || 35}%` }}
                        ></div>
                    </div>
                </div>
            )}

            {/* Pillar Selector */}
            <div className="space-y-3">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 font-mono">
                    1. Select Blockbuster Content Pillar
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                    {pillars.map(p => (
                        <div
                            key={p.id}
                            onClick={() => setPillar(p.id)}
                            className={`p-4 rounded-xl cursor-pointer border transition ${
                                pillar === p.id
                                    ? "bg-blue-600/20 border-blue-500 shadow-md shadow-blue-500/10"
                                    : "glass-card hover:border-white/20"
                            }`}
                        >
                            <div className="font-bold text-sm text-gray-100">{p.name}</div>
                            <div className="text-xs text-gray-400 mt-1 line-clamp-2">{p.desc}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Prompt Input */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 font-mono">
                        2. Prompt / Concept Hook (Optional)
                    </label>
                    <span className="text-[11px] text-blue-400 font-mono">Leave blank for 2-Stage Gemini Viral Brainstorm</span>
                </div>
                <textarea
                    rows="3"
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    placeholder="e.g. 'A scared orange kitten huddled in the rain is warmed by gentle hands' or 'Wait… mango soda actually tastes like this?'"
                    className="w-full p-4 rounded-xl glass-card text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 border border-white/10"
                ></textarea>
            </div>

            {/* Customization Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-400 font-mono">Voice Profile</label>
                    <select
                        value={voice}
                        onChange={e => setVoice(e.target.value)}
                        className="w-full p-3 rounded-xl glass-card text-sm text-gray-200 border border-white/10 focus:outline-none"
                    >
                        <option value="female">Ava Multilingual (Warm & Natural)</option>
                        <option value="documentary">Andrew Multilingual (Authoritative)</option>
                        <option value="british">Brian British (Sophisticated)</option>
                        <option value="energetic">Christopher (Dynamic & Fast)</option>
                        <option value="dark_mystery">Guy Neural (Cinematic)</option>
                    </select>
                </div>

                <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-400 font-mono">Music Bed Style</label>
                    <select
                        value={music}
                        onChange={e => setMusic(e.target.value)}
                        className="w-full p-3 rounded-xl glass-card text-sm text-gray-200 border border-white/10 focus:outline-none"
                    >
                        <option value="heartwarming_story">Warm Acoustic (Storytelling)</option>
                        <option value="upbeat_summer">Upbeat Summer Pop (UGC / Product)</option>
                        <option value="cyber_pulse">Cyber Electronic Pulse (Tech)</option>
                        <option value="ambient_glow">Ambient Glow (Science)</option>
                        <option value="curiosity_lofi">Curiosity Lo-Fi (Explainers)</option>
                        <option value="deep_mystery">Deep Mystery (Cosmos / Sci-Fi)</option>
                    </select>
                </div>

                <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-400 font-mono">Visual Motion Engine</label>
                    <select
                        value={visuals}
                        onChange={e => setVisuals(e.target.value)}
                        className="w-full p-3 rounded-xl glass-card text-sm text-gray-200 border border-white/10 focus:outline-none"
                    >
                        <option value="broll">Authentic Live-Action HD Video (B-Roll)</option>
                        <option value="ai">Photorealistic AI Cinematic Frames</option>
                    </select>
                </div>
            </div>

            {/* Submit Button */}
            <button
                disabled={isGenerating}
                onClick={onGenerate}
                className={`w-full glow-button py-4 rounded-xl font-bold text-base text-white flex items-center justify-center space-x-2 ${
                    isGenerating ? "opacity-50 cursor-not-allowed" : ""
                }`}
            >
                <Icon name="sparkles" className="w-5 h-5" />
                <span>{isGenerating ? "Synthesizing Reel..." : "Generate 1080x1920 Viral Reel"}</span>
            </button>
        </div>
    );
}

// ── Tab: Upload Video ─────────────────────────────────────────────────────
function UploadTab({ onUploadSuccess }) {
    const [uploading, setUploading] = useState(false);
    const [file, setFile] = useState(null);
    const fileInputRef = useRef(null);

    const handleUpload = async (selectedFile) => {
        if (!selectedFile) return;
        setUploading(true);
        const formData = new FormData();
        formData.append("video", selectedFile);

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                onUploadSuccess();
            } else {
                alert("Upload failed: " + data.error);
            }
        } catch (e) {
            alert("Upload error: " + e.message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div
                onClick={() => fileInputRef.current.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={e => {
                    e.preventDefault();
                    if (e.dataTransfer.files[0]) {
                        setFile(e.dataTransfer.files[0]);
                        handleUpload(e.dataTransfer.files[0]);
                    }
                }}
                className="flex flex-col items-center justify-center h-80 glass-card rounded-2xl p-8 border-2 border-dashed border-white/10 hover:border-blue-500 cursor-pointer transition text-center"
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/mp4,video/*"
                    className="hidden"
                    onChange={e => {
                        if (e.target.files[0]) {
                            setFile(e.target.files[0]);
                            handleUpload(e.target.files[0]);
                        }
                    }}
                />
                <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center text-3xl mb-4 text-blue-400">
                    <Icon name="upload-cloud" className="w-8 h-8" />
                </div>
                <h3 className="font-bold text-base text-gray-200">
                    {uploading ? "Ingesting & Optimizing Video..." : "Drag & Drop MP4 Video Here"}
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                    Or click to browse from your computer. Video will be placed in <code className="text-blue-400 font-mono">output/</code>.
                </p>
                {uploading && (
                    <div className="w-48 h-1.5 bg-white/10 rounded-full mt-4 overflow-hidden">
                        <div className="h-full bg-blue-500 animate-pulse w-full"></div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ── Tab: Instagram Reels ──────────────────────────────────────────────────
function InstagramTab({ published, onPreview }) {
    const igVideos = published.filter(v => v.instagram_url || v.instagram_id);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">
                    Showing <span className="font-semibold text-white">{igVideos.length}</span> published Instagram Reel(s).
                </p>
            </div>

            {igVideos.length === 0 ? (
                <div className="glass-card rounded-2xl p-12 text-center text-gray-400">
                    <p>No videos published to Instagram yet. Choose any video in Ready Videos to publish!</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {igVideos.map(v => (
                        <div key={v.filename} className="glass-card rounded-2xl overflow-hidden p-5 space-y-4">
                            <div
                                onClick={() => onPreview(v)}
                                className="relative aspect-[9/16] max-h-56 bg-dark-800 rounded-xl overflow-hidden cursor-pointer"
                            >
                                <video src={v.stream_url} className="w-full h-full object-cover" preload="metadata" />
                                <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                                    <Icon name="play" className="w-6 h-6 text-white" />
                                </div>
                            </div>
                            <div>
                                <h4 className="font-semibold text-sm line-clamp-1">{v.title}</h4>
                                <p className="text-xs text-gray-400 font-mono mt-0.5">{v.published_at}</p>
                            </div>
                            <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                                <a
                                    href={v.instagram_url || `https://www.instagram.com/reel/${v.instagram_id}/`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="px-3 py-1.5 rounded-lg bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 border border-pink-500/30 text-xs font-medium flex items-center space-x-1.5 transition"
                                >
                                    <Icon name="external-link" className="w-3.5 h-3.5" />
                                    <span>View on Instagram</span>
                                </a>
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(v.instagram_url || `https://www.instagram.com/reel/${v.instagram_id}/`);
                                        alert("Instagram Link copied to clipboard!");
                                    }}
                                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400"
                                    title="Copy Link"
                                >
                                    <Icon name="copy" className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Tab: YouTube Shorts ───────────────────────────────────────────────────
function YouTubeTab({ published, onPreview }) {
    const ytVideos = published.filter(v => v.youtube_url);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">
                    Showing <span className="font-semibold text-white">{ytVideos.length}</span> published YouTube Short(s).
                </p>
            </div>

            {ytVideos.length === 0 ? (
                <div className="glass-card rounded-2xl p-12 text-center text-gray-400">
                    <p>No videos published to YouTube yet. Choose any video in Ready Videos to publish!</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {ytVideos.map(v => (
                        <div key={v.filename} className="glass-card rounded-2xl overflow-hidden p-5 space-y-4">
                            <div
                                onClick={() => onPreview(v)}
                                className="relative aspect-[9/16] max-h-56 bg-dark-800 rounded-xl overflow-hidden cursor-pointer"
                            >
                                <video src={v.stream_url} className="w-full h-full object-cover" preload="metadata" />
                                <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                                    <Icon name="play" className="w-6 h-6 text-white" />
                                </div>
                            </div>
                            <div>
                                <h4 className="font-semibold text-sm line-clamp-1">{v.title}</h4>
                                <p className="text-xs text-gray-400 font-mono mt-0.5">{v.published_at}</p>
                            </div>
                            <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                                <a
                                    href={v.youtube_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium flex items-center space-x-1.5 transition"
                                >
                                    <Icon name="external-link" className="w-3.5 h-3.5" />
                                    <span>Watch on YouTube</span>
                                </a>
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(v.youtube_url);
                                        alert("YouTube Short Link copied to clipboard!");
                                    }}
                                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400"
                                    title="Copy Link"
                                >
                                    <Icon name="copy" className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Tab: Settings & Credentials ───────────────────────────────────────────
function SettingsTab({ status }) {
    if (!status) return <div>Loading...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Instagram Meta Graph API */}
                <div className="glass-card rounded-2xl p-6 space-y-4 border border-pink-500/20">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-pink-500/10 flex items-center justify-center text-xl">
                            📸
                        </div>
                        <div>
                            <h3 className="font-bold text-sm">Instagram Reels API</h3>
                            <p className="text-xs text-gray-400 font-mono">Meta Graph API v21.0</p>
                        </div>
                    </div>
                    <div className="space-y-2 pt-2 border-t border-white/5 text-xs font-mono">
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Handle</span>
                            <span className="text-white font-medium">{status.instagram.username || "@sun_27417"}</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Account ID</span>
                            <span className="text-gray-300">{status.instagram.id}</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Daily Quota</span>
                            <span className="text-emerald-400">{status.instagram.quota_usage} / {status.instagram.quota_total} Used</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Tunnel Bridge</span>
                            <span className="text-blue-400">Zero-Card OpenSSH HTTPS</span>
                        </div>
                    </div>
                </div>

                {/* YouTube Data API v3 */}
                <div className="glass-card rounded-2xl p-6 space-y-4 border border-red-500/20">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-xl">
                            ▶️
                        </div>
                        <div>
                            <h3 className="font-bold text-sm">YouTube Shorts API</h3>
                            <p className="text-xs text-gray-400 font-mono">Google Data API v3</p>
                        </div>
                    </div>
                    <div className="space-y-2 pt-2 border-t border-white/5 text-xs font-mono">
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Channel Name</span>
                            <span className="text-white font-medium">{status.youtube.channel_title || "EGO X"}</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Channel ID</span>
                            <span className="text-gray-300">{status.youtube.channel_id}</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">Subscribers</span>
                            <span className="text-gray-300">{status.youtube.subscribers}</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span className="text-gray-400">OAuth Credentials</span>
                            <span className="text-emerald-400">youtube_token.json Active</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Folder Storage Lifecycle */}
            <div className="glass-card rounded-2xl p-6 space-y-4">
                <h3 className="font-bold text-sm">📁 Two-Folder Safe Lifecycle</h3>
                <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                        <div className="text-blue-400 font-semibold mb-1">output/ (Ready)</div>
                        <div className="text-2xl font-bold text-white">{status.counts.ready}</div>
                        <div className="text-gray-400 mt-1">Videos awaiting publication</div>
                    </div>
                    <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                        <div className="text-emerald-400 font-semibold mb-1">published/ (Archived)</div>
                        <div className="text-2xl font-bold text-white">{status.counts.published}</div>
                        <div className="text-gray-400 mt-1">Moved here automatically to prevent duplicate posting</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Mount React Root
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
