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
            "system_design": ["#systemdesign", "#softwareengineering", "#distributedsystems", "#coding", "#backend", "#kafka", "#redis", "#softwaredevelopment"],
            "computer_engineering": ["#computerengineering", "#hardware", "#silicon", "#cpu", "#microprocessor", "#lowlevel", "#assembly"],
            "study_shorts": ["#computerscience", "#algorithms", "#codinginterview", "#bigo", "#programming", "#softwaredeveloper", "#csstudents"],
            "science_paradoxes": ["#science", "#physics", "#mindblown", "#didyouknow", "#cosmos", "#scientificfacts"],
            "ancient_mysteries": ["#ancienthistory", "#archaeology", "#mysteries", "#ancientcivilization", "#historyfacts", "#engineering"],
            "deep_tech": ["#technology", "#futuretech", "#ai", "#innovation", "#quantum"],
            "ocean_and_cosmos": ["#space", "#universe", "#astronomy", "#deepsea", "#ocean"]
        }

        tags = genre_tags.get(genre, ["#viral", "#trending", "#engineering", "#reels"])
        common_tags = ["#reels", "#explore", "#trending", "#instareels", "#fyp"]
        full_tags = " ".join(tags + common_tags)

        # Dynamic call-to-action tailored to genre
        if genre == "animal_universe":
            cta = "Drop a ❤️ for the crew! Which character are you? Share with someone who needs a laugh today! 🐾"
        elif genre == "baby_comedy":
            cta = "Who let this toddler run the boardroom? 😂 Tag your coworker who needs this negotiation strategy!"
        elif genre == "emotional_animal":
            cta = "Real loyalty never wavers. ❤️ Double-tap if this made your day better. Save to remember to be kind."
        elif genre == "asmr_satisfying":
            cta = "Listen with headphones on 🎧 Pure satisfaction loop. Save this for your nighttime unwind session ✨"
        else:
            cta = "Drop your thoughts in the comments! 👇 Save this reel for later 📌"

        body = f"{facts}\n\n{payoff}".strip()
        caption = f"{hook}\n\n{body}\n\n{cta}\n\n.\n.\n{full_tags}" if body else f"{hook}\n\n{cta}\n\n.\n.\n{full_tags}"
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
            "system_design": "28",        # Science & Technology
            "computer_engineering": "28", # Science & Technology
            "study_shorts": "27",         # Education
            "science_paradoxes": "28",    # Science & Tech
            "ancient_mysteries": "27",    # Education / History
            "deep_tech": "28",
            "dark_psychology": "27",
            "ocean_and_cosmos": "28"
        }
        category_id = category_map.get(genre, "28")

        tags_map = {
            "system_design": ["Shorts", "YouTubeShorts", "SystemDesign", "SoftwareEngineering", "DistributedSystems", "Kafka", "Backend", "Coding", "CloudArchitecture"],
            "computer_engineering": ["Shorts", "YouTubeShorts", "ComputerEngineering", "Hardware", "CPU", "Microprocessor", "Assembly", "LowLevel", "Silicon"],
            "study_shorts": ["Shorts", "YouTubeShorts", "ComputerScience", "BigO", "Algorithms", "CodingInterview", "DataStructures", "SoftwareEngineer"],
            "science_paradoxes": ["Shorts", "YouTubeShorts", "ScienceFacts", "Physics", "Cosmos", "MindBlowing", "ScientificFacts"],
            "ancient_mysteries": ["Shorts", "YouTubeShorts", "AncientTech", "History", "Archaeology", "EngineeringMarvels", "Antikythera"]
        }
        yt_tags = list(dict.fromkeys(tags_map.get(genre, [
            "Shorts",
            "YouTubeShorts",
            "Viral",
            "Trending",
            "SoftwareEngineering",
            "Science"
        ])))

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

