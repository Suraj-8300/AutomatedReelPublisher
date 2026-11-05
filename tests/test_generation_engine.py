#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.creative_randomizer import CreativeRandomizer, GENRE_TAXONOMY, GENERATION_MODES
from core.content_history import ContentHistory
from core.hooks_engine import HooksEngine
from core.subtitle_engine import SubtitleEngine
from core.quality_control import QualityControlEngine
from core.idea_generator import IdeaGenerator
from generate import run_pipeline

def test_creative_randomizer():
    print("Testing CreativeRandomizer...")
    # Test reproducibility
    cfg1 = CreativeRandomizer.generate_creative_config(seed=12345)
    cfg2 = CreativeRandomizer.generate_creative_config(seed=12345)
    assert cfg1 == cfg2, "Seeded generation must be 100% deterministic"

    # Test all modes
    for mode in GENERATION_MODES.keys():
        cfg = CreativeRandomizer.generate_creative_config(mode=mode)
        assert cfg["genre"] in GENRE_TAXONOMY, f"Invalid genre for mode {mode}"
        assert cfg["duration"] in [10, 15, 30, 60]
        assert cfg["caption_style"] in ["karaoke", "high_impact", "clean_minimal", "cinematic", "dynamic_phrase", "meme"]
    print("  ✅ CreativeRandomizer passed all tests.")

def test_content_history():
    print("Testing ContentHistory anti-repetition...")
    # Clean test
    cand_title = "The Quantum Superposition Reality"
    cand_hook = "Did you know that particles can exist in two states simultaneously?"
    
    # Record entry
    entry = ContentHistory.record_generation(
        title=cand_title,
        genre="science",
        subgenre="quantum_physics",
        hook=cand_hook,
        script="Particles exist in superposition until measured.",
        seed=99999,
        caption_style="karaoke",
        music_style="cyber_pulse"
    )
    assert entry["id"]

    # Check similarity detection on similar concept
    is_rep = ContentHistory.is_concept_repetitive(
        title="The Quantum Superposition Truth",
        hook="Particles exist in two places at once.",
        threshold=0.35
    )
    assert is_rep, "Similarity check should flag near-duplicate concepts"

    # Check non-repetition on different concept
    is_diff = ContentHistory.is_concept_repetitive(
        title="Why Cats Purr",
        hook="The biological frequency of feline purring accelerates bone healing."
    )
    assert not is_diff, "Different concept should not be flagged as repetitive"
    print("  ✅ ContentHistory passed all tests.")

def test_hooks_engine():
    print("Testing HooksEngine...")
    for genre in GENRE_TAXONOMY.keys():
        hook = HooksEngine.generate_hook(topic_title="Black Holes", genre=genre)
        assert hook["text"], "Hook must generate valid text"
        assert hook["family"], "Hook must report valid family"
    print("  ✅ HooksEngine passed all tests.")

def test_smart_idea_candidates():
    print("Testing ranked smart idea candidates...")
    ideas = IdeaGenerator.generate_idea_candidates(
        genre="science", duration=15, count=4, seed=123
    )
    assert len(ideas) == 4
    assert all(idea["genre"] == "science" for idea in ideas)
    assert all(0 <= idea["retention_score"] <= 100 for idea in ideas)
    assert len({idea["title"] for idea in ideas}) == len(ideas)
    assert ideas == IdeaGenerator.generate_idea_candidates(
        genre="science", duration=15, count=4, seed=123
    )
    print("  ✅ Smart idea ranking passed all tests.")

def test_subtitle_engine():
    print("Testing SubtitleEngine...")
    dummy_words = [
        {"word": "Scientists", "start": 0.0, "end": 0.4, "duration": 0.4},
        {"word": "just", "start": 0.4, "end": 0.7, "duration": 0.3},
        {"word": "discovered", "start": 0.7, "end": 1.2, "duration": 0.5},
        {"word": "something", "start": 1.2, "end": 1.6, "duration": 0.4},
        {"word": "fascinating.", "start": 1.6, "end": 2.2, "duration": 0.6}
    ]
    styles = ["karaoke", "high_impact", "clean_minimal", "cinematic", "dynamic_phrase", "meme"]
    for s in styles:
        out_ass = SubtitleEngine.generate_ass(dummy_words, style=s)
        p = Path(out_ass)
        assert p.exists() and p.stat().st_size > 100, f"Subtitle file for style {s} failed"
        p.unlink(missing_ok=True)
    print("  ✅ SubtitleEngine passed all tests.")

async def test_sample_generation():
    print("\n" + "=" * 65)
    print("🎬 GENERATING 8 SAMPLE REELS ACROSS DIVERSE GENRES")
    print("=" * 65)

    test_genres = [
        ("comedy", 10, "high_impact", "comedy_bounce"),
        ("meme", 15, "meme", "cyber_pulse"),
        ("science", 15, "karaoke", "cyber_pulse"),
        ("emotional", 15, "cinematic", "emotional_piano"),
        ("mysteries", 15, "dynamic_phrase", "deep_mystery"),
        ("animation", 10, "meme", "comedy_bounce"),
        ("cinematic", 15, "high_impact", "action_hybrid"),
        ("informative", 15, "clean_minimal", "curiosity_lofi")
    ]

    results = []
    for genre, duration, caption_style, music_style in test_genres:
        print(f"\n▶ Testing Genre: {genre.upper()} (duration={duration}s, caption={caption_style}, music={music_style})...")
        out_mp4, storyboard, qc = await run_pipeline(
            duration=duration,
            genre=genre,
            caption_style=caption_style,
            music_style=music_style,
            seed=42 + len(results),
            run_qc=True
        )
        assert Path(out_mp4).exists(), f"Failed to render video for genre {genre}"
        assert qc.get("passed"), f"QC failed for genre {genre}: {qc.get('errors')}"
        results.append({
            "genre": genre,
            "file": out_mp4,
            "title": storyboard["title"],
            "qc_score": qc.get("score"),
            "duration": qc.get("duration"),
            "size_mb": qc.get("size_mb")
        })

    print("\n" + "=" * 65)
    print("🎉 ALL 8 SAMPLE REELS GENERATED AND QC VERIFIED SUCCESSFULLY!")
    print("=" * 65)
    for r in results:
        print(f"  • [{r['genre'].upper():12s}] {r['title'][:32]:32s} | QC: {r['qc_score']}/100 | {r['duration']}s | {r['size_mb']}MB")
        print(f"    File: {r['file']}")

def main():
    test_creative_randomizer()
    test_content_history()
    test_hooks_engine()
    test_smart_idea_candidates()
    test_subtitle_engine()
    asyncio.run(test_sample_generation())

if __name__ == "__main__":
    main()
