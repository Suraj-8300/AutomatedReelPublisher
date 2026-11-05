"""
Metadata Packaging Engine for AutoReelStudio.
Tailors titles, descriptions, hashtags, and call-to-actions specifically
for Instagram Reels and YouTube Shorts distribution.
"""

from typing import Dict, Any, List

class MetadataPackager:
    """Packages metadata for targeted social media distribution."""

    @classmethod
    def package_for_instagram(
        cls,
        title: str,
        genre: str,
        hook: str,
        facts: str = "",
        payoff: str = ""
    ) -> Dict[str, Any]:
        """
        Creates an Instagram-optimized caption with narrative spacing, emojis, and hashtags.
        """
        genre_tags = {
            "science_paradoxes": ["#science", "#physics", "#mindblown", "#didyouknow", "#cosmos"],
            "dark_psychology": ["#psychology", "#humanmind", "#brainfacts", "#psychologyfacts", "#mindset"],
            "ancient_mysteries": ["#ancienthistory", "#archaeology", "#mysteries", "#ancientcivilization", "#historyfacts"],
            "nature_and_animals": ["#wildlife", "#naturelovers", "#animals", "#oceanlife", "#earth"],
            "deep_tech": ["#technology", "#futuretech", "#ai", "#innovation", "#quantum"],
            "ocean_and_cosmos": ["#space", "#universe", "#astronomy", "#deepsea", "#ocean"]
        }

        tags = genre_tags.get(genre, ["#curiosity", "#facts", "#viral", "#interesting"])
        common_tags = ["#reels", "#explore", "#trending", "#instareels", "#fyp"]
        full_tags = " ".join(tags + common_tags)

        caption = f"""{hook} 🤯

Did you know this? {facts}

{payoff}

Drop your thoughts in the comments! 👇 Save this reel for later 📌

.
.
{full_tags}
"""
        return {
            "caption": caption.strip(),
            "hashtags": tags + common_tags,
            "title": title
        }

    @classmethod
    def package_for_youtube(
        cls,
        title: str,
        genre: str,
        hook: str,
        facts: str = "",
        payoff: str = ""
    ) -> Dict[str, Any]:
        """
        Creates a YouTube Shorts package: <100 char title with #Shorts,
        rich description, and 15-20 viral tags.
        """
        # Ensure #Shorts is in the title
        clean_title = title.strip()
        if "#shorts" not in clean_title.lower() and len(clean_title) + 8 <= 100:
            yt_title = f"{clean_title} #Shorts"
        else:
            yt_title = clean_title[:100]

        category_map = {
            "science_paradoxes": "28",  # Science & Tech
            "deep_tech": "28",
            "dark_psychology": "27",    # Education
            "ancient_mysteries": "24",  # Entertainment
            "nature_and_animals": "15", # Pets & Animals
            "ocean_and_cosmos": "28"
        }
        category_id = category_map.get(genre, "24")

        yt_tags = [
            "Shorts",
            "YouTubeShorts",
            "Viral",
            "Trending",
            "DidYouKnow",
            "Facts",
            "MindBlowing",
            "Science",
            "Curiosity",
            "Mystery",
            "LearnOnYouTube",
            "AmazingFacts"
        ]

        description = f"""{hook}

{facts}

{payoff}

Subscribe for daily mind-blowing facts & stories! 🔔

#Shorts #Viral #Facts #{genre.replace('_', '').capitalize()} #Curiosity #Trending
"""

        return {
            "title": yt_title,
            "description": description.strip(),
            "tags": yt_tags,
            "category_id": category_id,
            "privacy_status": "public"
        }

