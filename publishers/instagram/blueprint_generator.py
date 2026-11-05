import os
from typing import Dict, Any, List

def generate_production_blueprint(topic: str, target_audience: str = "General Curators & Curious Minds", goal: str = "SAVE / SHARE") -> str:
    """
    Generates an end-to-end production blueprint for a high-retention Instagram Reel,
    structured into Hook Concepts, 4-Column Timeline Shot List, AI Asset Prompts,
    and Instagram Platform Packaging.
    """
    clean_topic = topic.strip().rstrip("?")
    
    blueprint = f"""# 🎬 MASTER INSTAGRAM REEL PRODUCTION BLUEPRINT
**Topic:** {clean_topic}
**Target Audience:** {target_audience}
**Primary Algorithmic Goal:** {goal} (Optimized for 3s Hold Rate > 55% and DM Shares)

---

## 1. THE HOOK CONCEPTS (Triple Hook Layering)

* **Angle A (Contrarian / Pattern Interrupt):**
  * *On-Screen Text:* "STOP BELIEVING THIS LIE."
  * *Spoken Line:* "Everything society told you about {clean_topic.lower()} is completely backwards."
  * *Visual Hook:* Fast push-in zoom (1.15x), subject looking directly into camera with intense focus.

* **Angle B (Negative Stakes / Cost of Inaction / FOMO):**
  * *On-Screen Text:* "WHAT THIS IS SECRETLY COSTING YOU."
  * *Spoken Line:* "You are actively losing hours every week by not knowing the truth about {clean_topic.lower()}."
  * *Visual Hook:* Dramatic high-contrast B-roll, sudden visual glitch effect on frame one.

* **Angle C (Mid-Action / Incomplete Loop):**
  * *On-Screen Text:* "THEY DIDN'T WANT THIS OUT."
  * *Spoken Line:* "Researchers weren't supposed to release this data on {clean_topic.lower()}, but look at this."
  * *Visual Hook:* Close-up macro detail or document reveal right in the middle of physical motion.

---

## 2. FULL PRODUCTION SCRIPT & SHOT LIST (9:16 Vertical Safe Zones)

| Timestamp | Visual / Camera Action (9:16 Safe Zone) | On-Screen Dynamic Text (3-5 Words Max) | Spoken Audio / VO & Sound Design |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:03**<br>*(Hook Phase)* | Fast dynamic push-in; high kinetic movement; visual interrupt centered between 220px top & 400px bottom safe margins. | `STOP BELIEVING THIS` *(Electric Yellow Pop)* | *(Whoosh SFX)* "Did you know the real truth behind {clean_topic.lower()}?" *(Music Ducked to -18dB)* |
| **0:03 - 0:07**<br>*(Pattern Interrupt)* | Micro-cut B-roll (2s reset); macro footage; camera dollies rapidly towards key subject; right margin 140px clear of UI buttons. | `MOST PEOPLE MISS THIS` *(White bold on dark shadow)* | "Most people go through life completely unaware of how this actually operates." |
| **0:07 - 0:14**<br>*(Pacing / Mechanism)* | Visual switch to high-contrast technical or cinematic B-roll; 1.15x zoom punch-in at 0:10 to reset viewer attention. | `HERE IS THE MECHANISM` *(Neon Cyan Accent)* | "When experts investigated the underlying data, the mechanism became crystal clear." |
| **0:14 - 0:22**<br>*(Payoff / Proof)* | Close-up proof demonstration / transformation reveal; subject or data centered in the 1080x1320 safe display zone. | `THE DATA DOESN'T LIE` *(High-contrast bold)* | "The reality is that your brain and physical biology operate on completely different rules." |
| **0:22 - 0:27**<br>*(Master Takeaway)* | Cinematic wide angle closing into tight medium shot; smooth camera motion; high-retention aesthetic. | `THE BOTTOM LINE` *(Electric Gold Highlight)* | "Once you understand this principle, you can never look at reality the same way again." |
| **0:27 - 0:30**<br>*(Seamless Loop Stitch)* | Dynamic match-cut; camera moves in direction of frame 0:00; rhythmic audio tail matches opening frequency. | `WHICH EXPLAINS WHY...` *(Active Bounce)* | *(Riser SFX)* "And that is the exact reason why..." *(Stitches seamlessly into 0:00!)* |

---

## 3. AI ASSET GENERATION PROMPTS

* **Scene 1 (Hook B-Roll):**
  `Cinematic vertical video, dynamic camera rapid dolly-in towards {clean_topic.lower()}, dramatic chiaroscuro rim lighting, high-contrast atmospheric smoke, 8k resolution, photorealistic, Unreal Engine 5 render style, 9:16 aspect ratio --ar 9:16`

* **Scene 2 (Mechanism / Science B-Roll):**
  `Macro close-up shot illustrating the internal mechanics of {clean_topic.lower()}, glowing neon fiber optics, high-tech laboratory aesthetic, shallow depth of field, slow pan, cinematic color grade --ar 9:16`

* **Scene 3 (Transformation / Payoff):**
  `Awe-inspiring wide cinematic perspective depicting mastery of {clean_topic.lower()}, golden hour volumetric lighting, deep atmospheric depth, smooth camera orbit, premium documentary aesthetic --ar 9:16`

* **Recommended ElevenLabs Voice Profile:**
  * *Voice Actor:* Christopher or Andrew (Energetic, confident, crisp articulation, conversational cadence without formal stiffness).
  * *Pacing:* +6% speed (approx. 145–160 words per minute), natural breath pauses every 4–6 words.

---

## 4. INSTAGRAM PLATFORM PACKAGING

* **Safe Zone Layout Rules:**
  * **Top Margin:** Keep top 220–250px completely clear of captions (accommodates top search, audio status, camera UI).
  * **Bottom Margin:** Keep bottom 380–420px clear of hardcoded text (accommodates username handle, audio ticker, caption overlay).
  * **Right Margin:** Keep right 120–140px clear of wide text (prevents collision with Heart, Comment, Share, and Save icons).

* **Instagram Caption Copy:**
  🤯 The untold reality about {clean_topic}.
  
  Most people get this completely backwards. When you look at the actual data and biological mechanisms, the conclusion is impossible to ignore.
  
  👇 Have you experienced this yourself? Drop your perspective in the comments!
  
  🔔 Follow for daily mind-opening revelations and high-leverage insights.
  📲 Share this with someone who needs to see this today.
  
  #reels #viral #didyouknow #psychology #science #mindset #fyp #explorepage

* **Audio & Retention Recommendation:**
  * Use a trending low-frequency electronic/ambient track ducked to -18dB under speech.
  * Tactile intro whoosh impact at 0.00s to anchor 3-second hold rate.
"""
    return blueprint

