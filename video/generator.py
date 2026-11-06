"""
Master Video Generation Orchestrator for AutoReelStudio.

Ties together all free modules into a single generate() call:
  Topic/News Source → Gemini Script → Voice → Visuals/Manim → Audio Mix → Composite → CDN-ready MP4

Supports all 4 content pillars:
  - cinematic:  Surreal sci-fi / cosmic storytelling (Pollinations.ai images + Ken Burns)
  - science:    Scientific breakthroughs & news (images + voice narration)
  - mechanical: How engines, machines work (Manim animated diagrams)
  - explainer:  Physics, math, CS explained visually (Manim animated infographics)
"""

import uuid
import datetime
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from video.config import (
    OUTPUT_DIR, CACHE_DIR,
    PILLAR_VOICE, PILLAR_MUSIC,
    GEMINI_API_KEY,
)
from video.sources.topic_rotator import TopicRotator, DAILY_SCHEDULE
from video.sources.wikipedia_feed import WikipediaFeed
from video.brain.pillar_router import PillarRouter
from video.brain.script_writer import ScriptWriter
from video.brain.idea_generator import IdeaGenerator
from video.brain.ugc_director import UGCDirector
from video.visuals.cinematic import CinematicEngine
from video.visuals.animator import ManimAnimator
from video.visuals.broll import BRollEngine
from video.visuals.consistent_story import ConsistentStoryEngine
from video.audio.voice_engine import VoiceEngine
from video.audio.music_engine import MusicEngine
from video.compose.ken_burns import KenBurnsEngine
from video.compose.subtitle_engine import SubtitleEngine, PILLAR_SUBTITLE_STYLE
from video.compose.compositor import Compositor


class ReelGenerator:
    """
    End-to-end free video generator.
    One call produces a fully rendered, CDN-optimized 1080x1920 MP4.
    """

    @classmethod
    def generate(
        cls,
        topic: str,
        pillar: Optional[str] = None,
        enrich_with_wikipedia: bool = True,
        output_filename: Optional[str] = None,
        voice_override: Optional[str] = None,
        music_override: Optional[str] = None,
        visuals_override: Optional[str] = "auto",
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Generates a complete high-quality vertical Reel for the given topic.

        Args:
            topic:                 The subject/theme for the reel
            pillar:                Content pillar override (cinematic/science/mechanical/explainer)
            enrich_with_wikipedia: Fetch background context from Wikipedia before scripting
            output_filename:       Filename for the output MP4 (auto-generated if None)
            voice_override:        Override voice style (documentary/energetic/british/female/dark_mystery)
            music_override:        Override music style (cyber_pulse/deep_mystery/etc.)

        Returns:
            (output_mp4_path, metadata_dict)
        """
        start_time = datetime.datetime.now()
        run_id = uuid.uuid4().hex[:8]
        metadata = {
            "topic": topic,
            "run_id": run_id,
            "pillar": None,
            "narration": "",
            "voice_style": "",
            "music_style": "",
            "output": None,
            "duration": 0.0,
            "error": None,
        }

        print(f"\n{'='*60}")
        print(f"🎬 AutoReelStudio Generator  [{run_id}]")
        print(f"📌 Topic: {topic}")
        print(f"{'='*60}")

        try:
            # ── Step 1: Detect Pillar ──────────────────────────────────
            detected_pillar = PillarRouter.route(topic, pillar_override=pillar)
            metadata["pillar"] = detected_pillar
            print(f"🎯 Pillar: {detected_pillar.upper()}")

            # ── Step 2: Enrich topic with Wikipedia ───────────────────
            article_summary = ""
            if enrich_with_wikipedia:
                print("📰 Fetching Wikipedia context...")
                try:
                    wiki_data = WikipediaFeed.get_article_summary(topic)
                    if wiki_data:
                        article_summary = wiki_data.get("summary", "")[:800]
                        print(f"   ✅ Wikipedia: {wiki_data['title']}")
                except Exception:
                    pass

            # ── Step 3: Generate Script via Gemini / UGC Director ───
            is_auto_idea = not topic or topic.strip().lower() in ("auto", "none", "")

            if detected_pillar == "ugc_lifestyle":
                print("🎬 UGC Director: Building master UGC lifestyle ad & consistency blueprint...")
                blueprint = UGCDirector.create_solpopa_blueprint(concept_hook=topic if not is_auto_idea else "Wait… mango soda actually tastes like this?")
                UGCDirector.export_blueprint_files(blueprint)
                script_data = blueprint
                topic = blueprint.get("title", topic)
                metadata["topic"] = topic
                metadata["ugc_blueprint"] = blueprint
                print(f"   ✅ UGC Blueprint generated & exported to output/ for '{topic}'")
            elif is_auto_idea and GEMINI_API_KEY:
                print("🧠 Auto-generating high-retention reel via 2-stage Gemini flow...")
                script_data = IdeaGenerator.generate_synchronized_reel_idea(pillar=detected_pillar)
                topic = script_data.get("topic", "An Extraordinary Story")
                metadata["topic"] = topic
                print(f"   ✅ Auto-Generated Topic: '{topic}'")
            elif not GEMINI_API_KEY:
                print("⚠️  No GEMINI_API_KEY — formulating narration from topic & research.")
                topic = topic or "An Extraordinary Story"
                script_data = cls._fallback_script(topic, detected_pillar, article_summary)
            else:
                print("🧠 Generating script with Gemini 2.5 Flash...")
                script_data = ScriptWriter.write_script(topic, pillar=detected_pillar, article_summary=article_summary)

            # Robustly resolve narration from script_data across all generation modes
            narration = script_data.get("narration", "").strip()
            if not narration:
                scenes = script_data.get("scenes", [])
                scene_texts = [s.get("text", "").strip() for s in scenes if s.get("text")]
                if scene_texts:
                    narration = " ".join(scene_texts)
                else:
                    narration = f"{script_data.get('hook','')} {script_data.get('escalation','')} {script_data.get('payoff','')}".strip()
            if not narration:
                narration = f"Discover the extraordinary story of {topic}."
            script_data["narration"] = narration
            print(f"   ✅ Script ready ({len(narration.split())} words)")

            # Resolve voice & music styles
            voice_style  = voice_override or script_data.get("voice_style") or PILLAR_VOICE.get(detected_pillar, "documentary")
            music_style  = music_override or script_data.get("music_style") or PILLAR_MUSIC.get(detected_pillar, "ambient_glow")
            metadata["narration"]   = narration
            metadata["voice_style"] = voice_style
            metadata["music_style"] = music_style

            # ── Step 4: Synthesize Voiceover ─────────────────────────
            print(f"🎙️  Synthesizing voice ({voice_style})...")
            audio_path, word_timings, total_duration = VoiceEngine.synthesize_sync(
                text=narration,
                voice_style=voice_style,
                rate="+5%",
            )
            metadata["duration"] = total_duration
            print(f"   ✅ Audio: {total_duration:.1f}s")

            # ── Step 5: Generate Visuals ──────────────────────────────
            scenes = script_data.get("scenes", [])
            if not scenes:
                scenes = cls._default_scenes(topic, total_duration, detected_pillar)

            # Synchronize scene transitions precisely to spoken narration words
            durations = cls._calculate_scene_durations(scenes, word_timings, total_duration)

            use_manim = (
                detected_pillar in ("mechanical", "explainer")
                and ManimAnimator.is_available()
                and bool(script_data.get("manim_code"))
            )

            is_narrative_pillar = detected_pillar in (
                "animal_story", "storytelling", "cute_animals",
                "anthropomorphic_animal", "ai_baby_adult", "ugc_lifestyle", "cinematic"
            )

            if use_manim and visuals_override not in ("broll", "consistent", "ai"):
                # 5a. Render Manim animated diagram
                print("⚙️  Rendering Manim animation...")
                manim_code  = script_data.get("manim_code", "")
                scene_class = script_data.get("scene_class", "AutoReelScene")
                anim_clip   = ManimAnimator.render(manim_code, scene_class=scene_class)
                scene_clips = [anim_clip]

            elif visuals_override in ("consistent", "character", "story") or (
                visuals_override in (None, "auto") and is_narrative_pillar
            ):
                # 5b. Character & Narrative Consistency Engine (Zero disconnected stock video clips)
                print(f"🐾 Consistent Character Engine: Sourcing continuous visual narrative ({detected_pillar})...")
                character_token = script_data.get("character_token", "")
                seed = script_data.get("seed", 42)
                scene_clips = ConsistentStoryEngine.generate_scenes(
                    scenes=scenes,
                    durations=durations,
                    character_token=character_token,
                    seed=seed,
                    run_id=run_id
                )

            elif visuals_override == "broll" or (visuals_override in (None, "auto") and not is_narrative_pillar):
                # 5c. Authentic Live-Action HD Video Footage (Coverr & Mixkit B-Roll) for Documentary Science
                print(f"🎬 Sourcing real live-action HD video clips ({detected_pillar})...")
                try:
                    scene_clips = BRollEngine.fetch_and_process_scenes(
                        scenes=scenes,
                        durations=durations,
                        run_id=run_id
                    )
                except Exception as e:
                    print(f"  ⚠️  Live stock video sourcing fallback ({e}) — applying consistent story motion...")
                    character_token = script_data.get("character_token", "")
                    scene_clips = ConsistentStoryEngine.generate_scenes(
                        scenes=scenes,
                        durations=durations,
                        character_token=character_token,
                        seed=42,
                        run_id=run_id
                    )

            else:
                # 5d. AI Visual Scenes with Cinematic Motion
                print(f"🎨 Generating AI visual scenes ({detected_pillar})...")
                character_token = script_data.get("character_token", "")
                seed = script_data.get("seed", 42)
                scene_clips = ConsistentStoryEngine.generate_scenes(
                    scenes=scenes,
                    durations=durations,
                    character_token=character_token,
                    seed=seed,
                    run_id=run_id
                )

            # ── Step 6: Generate Music Bed ────────────────────────────
            print(f"🎵 Generating music bed ({music_style})...")
            music_path = MusicEngine.generate(
                style=music_style,
                duration_sec=total_duration + 3.0,
            )

            # ── Step 7: Mix Voice + Music ─────────────────────────────
            print("🔊 Mixing audio (voice + ducked music)...")
            mixed_audio_path = CACHE_DIR / f"mixed_{run_id}.wav"
            mixed_audio = MusicEngine.get_ducked_mix(
                music_path=music_path,
                voice_path=audio_path,
                output_path=mixed_audio_path,
                music_volume_db=-18.0,
            )

            # ── Step 8: Generate Subtitles ────────────────────────────
            print("✍️  Generating karaoke subtitles...")
            sub_style = PILLAR_SUBTITLE_STYLE.get(detected_pillar, "karaoke")
            if word_timings:
                subtitles_path = SubtitleEngine.generate(word_timings, style=sub_style)
            else:
                subtitles_path = SubtitleEngine.generate_simple(narration, total_duration, style=sub_style)

            # ── Step 9: Composite Final Video ─────────────────────────
            print("⚡ Compositing final 1080x1920 MP4...")
            if output_filename is None:
                safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:40])
                output_filename = f"{safe_topic}_{run_id}.mp4"

            final_mp4 = Compositor.assemble(
                scene_clips=scene_clips,
                audio_path=mixed_audio,
                subtitles_path=subtitles_path,
                output_filename=output_filename,
                total_duration=total_duration,
                apply_faststart=True,
            )

            metadata["output"] = str(final_mp4)
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            size_mb = final_mp4.stat().st_size / (1024 * 1024) if final_mp4.exists() else 0

            print(f"\n{'='*60}")
            print(f"✅ REEL GENERATED SUCCESSFULLY")
            print(f"   📁 File:     {final_mp4.name}")
            print(f"   ⏱️  Duration: {total_duration:.1f}s")
            print(f"   📦 Size:     {size_mb:.1f} MB")
            print(f"   ⏰ Render:   {elapsed:.0f}s")
            print(f"{'='*60}\n")

            return final_mp4, metadata

        except Exception as e:
            metadata["error"] = str(e)
            print(f"\n❌ Generation failed: {e}")
            traceback.print_exc()
            raise

    @staticmethod
    def _calculate_scene_durations(scenes: list, word_timings: list, total_duration: float) -> list:
        """
        Computes scene durations perfectly synchronized with spoken narration words.
        When the sentence for scene 1 finishes being spoken, the camera cuts to scene 2!
        """
        if not scenes:
            return [total_duration]

        num_scenes = len(scenes)
        scene_word_counts = [len(s.get("text", "").split()) for s in scenes]
        total_words = sum(scene_word_counts)

        # If no word timings or scene texts, split proportionally or equally
        if not word_timings or total_words == 0:
            if total_words > 0:
                return [max(2.5, (cnt / total_words) * total_duration) for cnt in scene_word_counts]
            return [total_duration / num_scenes] * num_scenes

        durations = []
        current_word_idx = 0
        total_timing_words = len(word_timings)
        last_end_time = 0.0

        for i, scene in enumerate(scenes):
            if i == num_scenes - 1:
                # Last scene takes the remaining time
                rem = max(2.5, total_duration - last_end_time)
                durations.append(rem)
                break

            cnt = len(scene.get("text", "").split())
            if cnt == 0:
                cnt = total_timing_words // num_scenes

            target_idx = min(current_word_idx + cnt - 1, total_timing_words - 1)
            if 0 <= target_idx < total_timing_words:
                end_ms = word_timings[target_idx].get("end_ms", 0)
                end_sec = end_ms / 1000.0
                dur = max(2.5, end_sec - last_end_time)
                durations.append(dur)
                last_end_time = end_sec
                current_word_idx += cnt
            else:
                dur = total_duration / num_scenes
                durations.append(dur)
                last_end_time += dur

        # Normalize so sum equals total_duration
        dur_sum = sum(durations)
        if dur_sum > 0:
            scale = total_duration / dur_sum
            durations = [d * scale for d in durations]

        return durations

    @staticmethod
    def _fallback_script(topic: str, pillar: str, article_summary: str = "") -> Dict[str, Any]:
        """Builds a rich factual script when Gemini API key is not configured."""
        from video.config import PILLAR_VOICE, PILLAR_MUSIC

        if pillar in ("animal_story", "storytelling", "cute_animals"):
            scenes = ReelGenerator._default_scenes(topic, 15.0, pillar)
            narration = " ".join([s["text"] for s in scenes])
            return {
                "narration":   narration,
                "hook":        scenes[0]["text"],
                "voice_style": "female",
                "music_style": "heartwarming_story",
                "scenes":      scenes,
            }

        if article_summary and len(article_summary) > 80:
            sentences = [s.strip() for s in article_summary.split(".") if len(s.strip()) > 15]
            hook = sentences[0] + "." if sentences else f"Here is what makes {topic} extraordinary."
            narration = " ".join(sentences[:3]) + "." if len(sentences) >= 2 else article_summary[:250]
        else:
            hook = f"The mechanics behind {topic} are astonishing."
            narration = (
                f"Ever wondered how {topic} actually works? "
                f"Behind this phenomenon lies an incredible scientific and engineering principle. "
                f"From fundamental forces to intricate internal components, "
                f"every single part operates in precise harmony."
            )

        return {
            "narration":   narration,
            "hook":        hook,
            "voice_style": PILLAR_VOICE.get(pillar, "documentary"),
            "music_style": PILLAR_MUSIC.get(pillar, "cyber_pulse" if pillar == "mechanical" else "ambient_glow"),
            "scenes": ReelGenerator._default_scenes(topic, 15.0, pillar),
            "scene_class": "AutoReelScene",
        }

    @staticmethod
    def _default_scenes(topic: str, total_duration: float, pillar: str = "science") -> list:
        """Generates tailored scene descriptors per pillar."""
        dur = total_duration / 3

        if pillar in ("animal_story", "storytelling", "cute_animals"):
            return [
                {
                    "scene_num": 1,
                    "text": f"A tiny, vulnerable animal was discovered facing the harsh cold all alone.",
                    "prompt": f"A tiny adorable shivering kitten or puppy looking up with big expressive eyes in rainy outdoor setting, 9:16 vertical, photorealistic, 8k emotional lighting",
                    "search_fallback": "cute kitten rain",
                    "duration": dur,
                },
                {
                    "scene_num": 2,
                    "text": f"A kind gentle rescuer stopped, wrapped them in a warm soft towel, and gave them comfort.",
                    "prompt": f"A gentle human holding and comforting the rescued tiny baby animal wrapped in a warm blanket, drinking milk, warm indoor lighting, 9:16 vertical, photorealistic",
                    "search_fallback": "rescued kitten blanket",
                    "duration": dur,
                },
                {
                    "scene_num": 3,
                    "text": f"Today, they are healthy, playful, and deeply loved in their forever home.",
                    "prompt": f"A joyful healthy fluffy cute cat or dog smiling happily in a sunlit cozy living room, warm golden hour, 9:16 vertical, photorealistic",
                    "search_fallback": "happy cat home",
                    "duration": dur,
                },
            ]
        elif pillar == "mechanical":
            return [
                {"scene_num": 1, "text": f"Here is the engineering intake mechanism behind {topic}.", "prompt": f"Technical engineering blueprint cutaway schematic of {topic}, labeled components and pressure vectors, 9:16 vertical CAD", "search_fallback": f"{topic} engine", "duration": dur},
                {"scene_num": 2, "text": "Inside, massive mechanical forces generate high-pressure compression.", "prompt": f"Internal cross-section schematic of {topic}, glowing thermal flow and mechanical gears, 9:16 vertical", "search_fallback": f"{topic} mechanism", "duration": dur},
                {"scene_num": 3, "text": "This delivers continuous rotational kinetic power.", "prompt": f"Exploded 3D engineering assembly diagram of {topic}, precision machined titanium parts, 9:16 vertical", "search_fallback": f"{topic} schematic", "duration": dur},
            ]
        elif pillar == "explainer":
            return [
                {"scene_num": 1, "text": f"Why does {topic} behave this way?", "prompt": f"Scientific conceptual diagram of {topic}, dark-mode minimalist vector infographic, glowing lines, 9:16 vertical", "search_fallback": f"{topic} diagram", "duration": dur},
                {"scene_num": 2, "text": "The underlying mathematical equations reveal a surprising symmetry.", "prompt": f"Step-by-step mathematical diagram explaining {topic}, clean labeled visual flow, 9:16 vertical", "search_fallback": f"{topic} math", "duration": dur},
                {"scene_num": 3, "text": "This principle shapes modern technology and physics.", "prompt": f"Abstract geometric infographic of {topic}, 3Blue1Brown aesthetic, dark background, 9:16 vertical", "search_fallback": f"{topic} science", "duration": dur},
            ]
        elif pillar == "cinematic":
            return [
                {"scene_num": 1, "text": f"In the furthest depths of space lies {topic}.", "prompt": f"Epic cinematic visualization of {topic}, photorealistic, dramatic volumetric lighting, 9:16 vertical", "search_fallback": f"{topic} cosmos", "duration": dur},
                {"scene_num": 2, "text": "Intense cosmic forces tear across the fabric of spacetime.", "prompt": f"Macro cosmic close-up detail of {topic}, glowing energy, 8k Unreal Engine 5 aesthetic, 9:16 vertical", "search_fallback": f"{topic} space", "duration": dur},
                {"scene_num": 3, "text": "A breathtaking spectacle stretching across light years.", "prompt": f"Panoramic wide view relating to {topic}, awe-inspiring scale, golden hour lighting, 9:16 vertical", "search_fallback": f"{topic} astronomy", "duration": dur},
            ]
        else:
            return [
                {"scene_num": 1, "text": f"Scientists have announced a breakthrough in {topic}.", "prompt": f"Scientific laboratory documentary visual of {topic}, photorealistic, ultra-detailed, 9:16 vertical", "search_fallback": f"{topic} research", "duration": dur},
                {"scene_num": 2, "text": "Observations confirm unexpected microscopic behavior under testing.", "prompt": f"Microscopic or telescopic visualization of {topic}, high-tech scientific imagery, 9:16 vertical", "search_fallback": f"{topic} microscope", "duration": dur},
                {"scene_num": 3, "text": "This discovery opens new frontiers for human innovation.", "prompt": f"World-changing scientific impact of {topic}, dramatic lighting, 8k resolution, 9:16 vertical", "search_fallback": f"{topic} technology", "duration": dur},
            ]


class BatchGenerator:
    """
    Runs a full day's batch of reels using the daily schedule.
    """

    @classmethod
    def run_batch(
        cls,
        count: int = 10,
        use_wikipedia: bool = True,
        auto_publish: bool = False,
        platform: str = "all",
    ) -> list:
        """
        Generates `count` reels using the daily schedule.
        Returns list of (mp4_path, metadata) tuples.

        Args:
            count:         Number of reels to generate (default 10)
            use_wikipedia: Enrich topics from Wikipedia trending feeds
            auto_publish:  Whether to publish each reel immediately after generation
            platform:      Publishing platform (all/instagram/youtube)
        """
        schedule = TopicRotator.get_daily_schedule(count)
        results = []

        # Optionally override some schedule topics with fresh Wikipedia topics
        if use_wikipedia:
            try:
                fresh = WikipediaFeed.get_fresh_topics(limit=count // 3)
                for i, topic_data in enumerate(fresh[:count // 3]):
                    wiki_topic = topic_data.get("title", "")
                    if wiki_topic:
                        # Insert into schedule with auto-detected pillar
                        pillar = TopicRotator.detect_pillar(wiki_topic)
                        schedule[i] = (pillar, wiki_topic)
            except Exception:
                pass

        print(f"\n{'='*60}")
        print(f"🚀 BATCH GENERATION — {count} REELS")
        print(f"{'='*60}")
        for i, (pillar, topic) in enumerate(schedule):
            print(f"   {i+1:2d}. [{pillar.upper():10s}] {topic}")
        print(f"{'='*60}\n")

        for i, (pillar, topic) in enumerate(schedule):
            print(f"\n[{i+1}/{count}] Generating reel...")
            try:
                mp4_path, meta = ReelGenerator.generate(
                    topic=topic,
                    pillar=pillar,
                    enrich_with_wikipedia=use_wikipedia,
                )
                results.append((mp4_path, meta))

                if auto_publish and mp4_path.exists():
                    cls._publish(mp4_path, topic, platform)

            except Exception as e:
                print(f"⚠️  Reel {i+1} failed: {e}")
                results.append((None, {"topic": topic, "error": str(e)}))

        successful = sum(1 for r, _ in results if r is not None)
        print(f"\n{'='*60}")
        print(f"✅ BATCH COMPLETE: {successful}/{count} reels generated")
        print(f"📁 Output directory: {OUTPUT_DIR}")
        print(f"{'='*60}\n")
        return results

    @staticmethod
    def _publish(mp4_path: Path, topic: str, platform: str = "all") -> None:
        """Triggers direct publishing and moves video to published/ to avoid multiple publish."""
        try:
            import sys
            import shutil
            import datetime
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from instagram.publisher import MetaGraphPublisher
            from instagram.cloud_bridge import CloudBridge
            from youtube.publisher import YouTubePublisher
            from video.config import PUBLISHED_DIR

            platforms = ["instagram", "youtube"] if platform == "all" else [platform]
            safe_title = topic[:95] + " #Shorts" if len(topic) < 92 else topic[:91] + "... #Shorts"
            published_any = False

            if "instagram" in platforms:
                try:
                    ig = MetaGraphPublisher()
                    if ig.is_configured():
                        bridge = CloudBridge()
                        public_url = bridge.upload(mp4_path)
                        container_id = ig.create_container(video_url=public_url, caption=topic)
                        ig.poll_status(container_id)
                        media_id = ig.publish_media(container_id)
                        print(f"   📸 Instagram published: {media_id}")
                        published_any = True
                except Exception as e:
                    print(f"   ⚠️  Instagram failed: {e}")

            if "youtube" in platforms:
                try:
                    yt = YouTubePublisher()
                    res = yt.upload_short(video_path=mp4_path, title=safe_title, description=topic)
                    if res.get("success"):
                        print(f"   ▶️  YouTube published: {res.get('shorts_url')}")
                        published_any = True
                except Exception as e:
                    print(f"   ⚠️  YouTube failed: {e}")

            if published_any and mp4_path.exists() and mp4_path.parent.resolve() != PUBLISHED_DIR.resolve():
                PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
                dest = PUBLISHED_DIR / mp4_path.name
                if dest.exists():
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest = PUBLISHED_DIR / f"{mp4_path.stem}_{ts}{mp4_path.suffix}"
                shutil.move(str(mp4_path), str(dest))
                print(f"   📦 Moved to published/{dest.name} (preventing multiple publish)")

        except Exception as e:
            print(f"   ⚠️  Publishing error: {e}")
