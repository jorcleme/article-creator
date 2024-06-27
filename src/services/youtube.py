from googleapiclient.discovery import build
import pandas as pd
import json
from typing import List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders.youtube import YoutubeLoader


class SeriesCatalogToTags:
    SERIES_TAGS = {
        "Cisco Catalyst 1200 Series Switches": ["c1200", "cat1200"],
        "Cisco Catalyst 1300 Series Switches": ["c1300", "cat1300"],
        "Cisco Business 110 Series Unmanaged Switches": ["cbs110"],
        "Cisco Business 220 Series Smart Switches": ["cbs220"],
        "Cisco Business 250 Series Smart Switches": ["cbs250"],
        "Cisco Business 350 Series Managed Switches": ["cbs350"],
        "Cisco 350 Series Managed Switches": ["sf350", "sg350", "sg 350 series"],
        "Cisco 350X Series Stackable Managed Switches": [
            "sf350",
            "sg350x",
            "sg 350x series",
            "sg350x",
            "sg350xg",
            "sf",
            "sg",
        ],
        "Cisco 550X Series Stackable Managed Switches": [
            "550x",
            "sf550x",
            "sg550x",
            "sg 550x series",
            "sg500",
            "sg500x",
            "sg550",
            "sg550 series small business switches",
            "sg550 seriesz",
            "sg550x",
            "sg550xg",
        ],
        "RV100 Product Family": [
            "how to create a secure tunnel between two rv130w routers",
            "rv120w",
            "rv130",
            "rv130w",
            "rv130w router",
            "rv180",
            "rv180w",
        ],
        "Cisco RV160 VPN Router": [
            "rv160",
            "rv160 rv260 rv series routers",
            "cisco rv160",
            "cisco rv160 router",
            "smb-routers-rv160-series",
            "what is rv160 router",
        ],
        "Cisco RV260 VPN Router": [
            "cisco rv260",
            "cisco rv260 router",
            "cisco rv260w",
            "cisco rv260w router",
            "how to configure rv260w router",
            "rv160 rv260 rv series routers",
            "rv260",
            "rv260 series",
            "rv260p",
            "rv260w",
            "rv260w router",
            "rv260w router set up",
            "rv260w router setup",
            "rv260w set up",
            "rv260w setup",
            "set up rv260w",
            "set up rv260w router",
            "setup rv260w router",
        ],
        "RV320 Product Family": ["rv320", "smb-routers-rv320-series"],
        "RV340 Product Family": [
            "rv340",
            "smb-routers-rv340-series",
            "cisc rv340 router",
            "cisco business rv340",
            "cisco rv340",
            "cisco rv340 router",
            "cisco rv340 router policy",
            "cisco rv340 series",
            "cisco rv340 series router",
            "cisco rv340 series routers",
            "cisco rv340w",
            "ciscorv340",
            "rv340 router",
            "rv340 series",
            "rv340 series router",
            "rv340w",
        ],
        "Cisco Business Wireless AC": [
            "cbw140",
            "cbw140ac",
            "cbw141",
            "cbw141acm",
            "cbw142",
            "cbw142acm",
            "cbw143acm",
            "cbw144ac",
            "cbw145",
            "cbw145ac",
            "cisco mesh",
            "cbw240",
            "cbw240ac",
        ],
        "Cisco Business Wireless AX": [
            "cbw150",
            "cbw150ax",
            "cbw151",
            "cbw151ax",
            "cbw151axm",
        ],
        "Cisco Small Business 100 Series Wireless Access Points": [
            "cisco wap125",
            "ciscowap150",
            "configuring wap",
            "wap125",
            "wap150",
            "wap150_indoor_wall_mounting",
        ],
        "Cisco Small Business 300 Series Wireless Access Points": [
            "how to manage channels on wap371",
            "wap 371",
            "wap361",
            "wap371",
        ],
        "Cisco Small Business 500 Series Wireless Access Points": [
            "cisco wap581",
            "wap571",
            "wap571_ceiling_mounting",
            "wap571_indoor_mounting_options",
            "wap571_wall_mounting",
            "wap571e",
            "wap581",
        ],
        "Cisco IP Phone 6800 Series with Multiplatform Firmware": [
            "cp-6800",
            "cisco multiplatform firmware",
        ],
        "Cisco IP Phone 7800 Series": [
            "7800",
            "7800 cisco multiplatform phone",
            "cisco 7800 series ip phone",
            "cp-7800",
        ],
        "Cisco IP Phone 8800 Series": [
            "8800",
            "8800 cisco multiplatform phone",
            "cisco 8800 series ip phone",
            "cp-8800",
            "cisco cp-8800",
        ],
        "Cisco Business Dashboard": [
            "cbd",
            "cbd 2.3",
            "cbd licensing",
            "cbd probe",
            "business dashboard",
            "cisco business dashboard",
            "cisco business dashboard features",
            "cisco business dashboard network monitoring",
        ],
        "Cisco Business Mobile App": [
            "cisco business mobile app",
            "cisco business mobile app features",
            "cisco business mobile app installation",
            "cisco business mobile app setup",
            "mobile",
            "mobile app",
            "mobile network",
            "mobile network settings",
        ],
        "Cisco Business FindIT": [
            "cisco findit",
            "cisco findit network management",
            "cisco findit topology",
        ],
    }

    @classmethod
    def resolve_series(cls, tags: List[str]):
        for series, tags_list in cls.SERIES_TAGS.items():
            if any(word in tags for word in tags_list):
                return series
        return None


class CiscoYouTubeDataLoader:
    def __init__(
        self,
        api_key: str,
        playlist_id: str,
        channel_ids: List[str],
        fetch: bool = True,
    ):
        """
        Initializes the CiscoYouTubeDataLoader class with the necessary API key, playlist ID, and channel IDs.

        :param api_key: A valid Google API key.
        :param playlist_id: The ID of the YouTube playlist to process.
        :param channel_ids: A list of YouTube channel IDs to gather stats for.
        """
        self.api_key = api_key
        self.playlist_id = playlist_id
        self.channel_ids = channel_ids
        self.youtube_service = build("youtube", "v3", developerKey=self.api_key)
        self.scraped_videos_json = self._load_scraped_videos()
        self.series_catalog = SeriesCatalogToTags()
        self._videos = []
        if fetch:
            self._fetch()

    def _fetch(self):
        channel_stats = self.get_channel_stats_by_id()
        playlist_video_ids = self.get_video_ids_by_playlist_id()
        video_data = self.get_video_data(playlist_video_ids)
        videos_with_transcripts = self.get_video_transcript(video_data)
        videos_with_categories = self.resolve_category(videos_with_transcripts)
        videos_with_series = self.resolve_to_series(videos_with_categories)
        self.videos = videos_with_series

    @property
    def videos(self):
        return self._videos

    @videos.setter
    def videos(self, value):
        self._videos = value

    @staticmethod
    def _load_scraped_videos() -> List[Dict[str, Any]]:
        """
        Loads previously scraped video data from a JSON file.

        Returns:
            List: Returns the list of video data from the JSON file or an empty list if the file is not found.
        """
        try:
            with open("./data/smb_youtube_videos.json", "r") as file:
                data = json.load(file)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _get_previously_scraped_video(self, video_id: str) -> Dict[str, Any]:
        for video in self.scraped_videos_json:
            if video["video_id"] == video_id:
                return video

    def _has_previously_scraped_video(self, video_id: str) -> bool:
        for video in self.scraped_videos_json:
            if video["video_id"] == video_id:
                return True
        return False

    def get_channel_stats_by_id(self):
        """
        Retrieves the statistics for the channels associated with the provided channel IDs.

        Returns:
            List: Returns a list of dictionaries containing the channel statistics.
        """
        stats = []
        request = self.youtube_service.channels().list(
            part="snippet,contentDetails,statistics", id=",".join(self.channel_ids)
        )
        response = request.execute()

        for i in range(len(response["items"])):
            data = dict(
                channel_name=response["items"][i]["snippet"]["title"],
                subscribers=response["items"][i]["statistics"]["subscriberCount"],
                videos=response["items"][i]["statistics"]["videoCount"],
                views=response["items"][i]["statistics"]["viewCount"],
                playlist_id=response["items"][i]["contentDetails"]["relatedPlaylists"][
                    "uploads"
                ],
            )
            stats.append(data)
        return stats

    def get_video_ids_by_playlist_id(self):
        """
        Retrieves the video IDs from the specified playlist.

        Returns:
            List: Returns a list of video IDs from the playlist.
        """
        videos = []
        request = self.youtube_service.playlistItems().list(
            part="contentDetails", playlistId=self.playlist_id, maxResults=50
        )
        response = request.execute()

        for i in range(len(response["items"])):
            video_id = response["items"][i]["contentDetails"]["videoId"]
            videos.append(video_id)
        next_page_token = response.get("nextPageToken")

        while next_page_token:
            request = self.youtube_service.playlistItems().list(
                part="contentDetails",
                playlistId=self.playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            response = request.execute()
            for i in range(len(response["items"])):
                video_id = response["items"][i]["contentDetails"]["videoId"]
                videos.append(video_id)
            next_page_token = response.get("nextPageToken")

        return videos

    def get_video_data(self, video_ids: List[str]):
        """
        Retrieves the data for the specified video IDs.

        Args:
            video_ids (List[str]): A list of video IDs to retrieve data for.

        Returns:
            List: Returns a list of dictionaries containing the video data.
        """
        videos = []

        try:
            for i in range(0, len(video_ids), 50):
                request = self.youtube_service.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=",".join(video_ids[i : i + 50]),
                )
                response = request.execute()
                for video in response["items"]:

                    data = dict(
                        title=video["snippet"]["title"],
                        published_date=video["snippet"]["publishedAt"],
                        description=video["snippet"]["description"],
                        url=f"https://www.youtube.com/embed/{video['id']}",
                        video_id=video["id"],
                        views=video["statistics"]["viewCount"],
                        likes=video["statistics"]["likeCount"],
                        duration=video["contentDetails"]["duration"],
                        comments=video["statistics"]["commentCount"],
                        kind=video["kind"].split("#")[0],
                        tags=video["snippet"]["tags"],
                    )
                    video_id = data["video_id"]
                    if self._has_previously_scraped_video(video_id=video_id):
                        stale_video_data = self._get_previously_scraped_video(
                            video_id=video_id
                        )
                        # update stale_data and spread fetched data as likes, comments and views could have changed.
                        stale_video_data.update(data)
                        videos.append(stale_video_data)
                    else:
                        videos.append(data)
        except Exception as e:
            print(e)

        return videos

    def get_video_transcript(
        self, video_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        videos = []
        for video in video_data:
            if "transcript" in video:
                videos.append(video)
                print(
                    f"Skipping video ID {video['video_id']} as transcript already exists."
                )
                continue
            video_id = video["video_id"]
            transcript = []
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id=video_id, preserve_formatting=True
                )
            except Exception as e:
                print(
                    f"Error fetching transcript for video ID {video_id}. Error {type(e)}: {e}"
                )
                transcript = []
            video["transcript"] = " ".join([line["text"] for line in transcript])
            videos.append(video)
        return videos

    def resolve_category(
        self, video_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Dict[str, Any]]]:
        """
        Resolves the category of the videos based on the title, description, and tags.

        Args:
            video_data (List[Dict[str, Dict[str, Any]]]): A list of dictionaries containing the video data.

        Returns:
            List: Returns a list of dictionaries containing the video data with the resolved category.
        """
        videos_with_categories = []

        videos: List[Dict[str, Dict[str, Any]]] = []

        for video in video_data:
            video_id: str = video["video_id"]
            video_details = {video_id: video}
            videos.append(video_details)

        for video in videos:
            for k, v in video.items():
                print(f"key {k}: value {v}")
                title = v["title"].lower()
                description = v["description"].lower()
                tags = [tag.lower() for tag in v["tags"]]
                video[k]["category"] = "Configuration"

                # Configuration
                configuring = [
                    "firewall",
                    "configure",
                    "tech talk",
                    "cisco tech talk",
                    "bluetooth",
                    "configurations",
                    "configuring",
                    "configuration",
                    "deploy",
                ]
                if (
                    any(word in title for word in configuring)
                    or any(word in description for word in configuring)
                    or any(word in tags for word in configuring)
                ):
                    video[k]["category"] = "Configuration"
                # Install & Upgrade
                install_upgrade = [
                    "install",
                    "upgrade",
                    "installation",
                    "upgrading",
                    "day 0",
                    "day",
                    "get to know",
                    "getting to know",
                    "get-to-know",
                ]
                if any(word in title for word in install_upgrade) or any(
                    word in description for word in install_upgrade
                ):
                    video[k]["category"] = "Install & Upgrade"
                # Maintain & Operate
                maintain_operate = [
                    "reboot",
                    "restarting",
                    "restart",
                    "rebooting",
                    "rebooted",
                    "restarting",
                    "maintain",
                    "operate",
                    "cli",
                    "command line",
                    "command-line",
                    "command line interface",
                    "terminal",
                ]
                if any(word in title for word in maintain_operate) or any(
                    word in description for word in maintain_operate
                ):
                    video[k]["category"] = "Maintain & Operate"
                # Troubleshooting
                troubleshooting = [
                    "troubleshoot",
                    "troubleshooting",
                    "troubleshooter",
                    "troubleshooters",
                    "tips",
                ]
                if any(word in title for word in troubleshooting) or any(
                    word in description for word in troubleshooting
                ):
                    video[k]["category"] = "Troubleshooting"
                # Design
                design = [
                    "design",
                    "designing",
                    "designs",
                    "new to cisco",
                    "cisco business",
                ]
                if any(word in title for word in design) or any(
                    word in description for word in design
                ):
                    video[k]["category"] = "Design"

            videos_with_categories.append(video)

        return videos_with_categories

    def resolve_to_series(
        self, videos: List[Dict[str, Dict[str, Any]]]
    ) -> List[Dict[str, Dict[str, Any]]]:
        """
        Resolves the series of the videos based on the tags.

        Args:
            videos (List[Dict[str, Dict[str, Any]]]): A list of dictionaries containing the video data.

        Returns:
            List: Returns a list of dictionaries containing the video data with the resolved series.
        """
        concepts = []
        for video in videos:
            for _, values in video.items():
                tags = [tag.lower() for tag in values["tags"]]

                # Catalyst 1200 Series
                catalyst_1200_series = ["c1200", "cat1200"]
                if any(word in tags for word in catalyst_1200_series):
                    values["series"] = "Cisco Catalyst 1200 Series Switches"
                    concepts.append(values.copy())

                # Catalyst 1300 Series
                catalyst_1300_series = ["c1300", "cat1300"]
                if any(word in tags for word in catalyst_1300_series):
                    values["series"] = "Cisco Catalyst 1300 Series Switches"
                    concepts.append(values.copy())

                # CBS110
                cbs110_series = ["cbs110"]
                if any(word in tags for word in cbs110_series):
                    values["series"] = "Cisco Business 110 Series Unmanaged Switches"
                    concepts.append(values.copy())

                # CBS220
                cbs220_series = ["cbs220"]
                if any(word in tags for word in cbs220_series):
                    values["series"] = "Cisco Business 220 Series Smart Switches"
                    concepts.append(values.copy())

                # CBS250
                cbs250_series = ["cbs250"]
                if any(word in tags for word in cbs250_series):
                    values["series"] = "Cisco Business 250 Series Smart Switches"
                    concepts.append(values.copy())

                # CBS350
                cbs350_series = ["cbs350"]
                if any(word in tags for word in cbs350_series):
                    values["series"] = "Cisco Business 350 Series Managed Switches"
                    concepts.append(values.copy())

                # SMB350
                smb350_series = ["sf350", "sg350", "sg 350 series"]
                if any(word in tags for word in smb350_series):
                    values["series"] = "Cisco 350 Series Managed Switches"
                    concepts.append(values.copy())

                # SMB350X
                smb350x_series = [
                    "sf350",
                    "sg350x",
                    "sg 350x series",
                    "sg350x",
                    "sg350xg",
                    "sf",
                    "sg",
                ]
                if any(word in tags for word in smb350x_series):
                    values["series"] = "Cisco 350X Series Stackable Managed Switches"
                    concepts.append(values.copy())

                # SMB550X
                smb550x_series = [
                    "550x",
                    "sf550x",
                    "sg550x",
                    "sg 550x series",
                    "sg500",
                    "sg500x",
                    "sg550",
                    "sg550 series small business switches",
                    "sg550 seriesz",
                    "sg550x",
                    "sg550xg",
                ]
                if any(word in tags for word in smb550x_series):
                    values["series"] = "Cisco 550X Series Stackable Managed Switches"
                    concepts.append(values.copy())

                # RV100
                rv100_series = [
                    "how to create a secure tunnel between two rv130w routers",
                    "rv120w",
                    "rv130",
                    "rv130w",
                    "rv130w router",
                    "rv180",
                    "rv180w",
                ]
                if any(word in tags for word in rv100_series):
                    values["series"] = "RV100 Product Family"
                    concepts.append(values.copy())

                # RV160 VPN Router
                rv160_series = [
                    "rv160",
                    "rv160 rv260 rv series routers",
                    "cisco rv160",
                    "cisco rv160 router",
                    "smb-routers-rv160-series",
                    "what is rv160 router",
                ]
                if any(word in tags for word in rv160_series):
                    values["series"] = "RV160 VPN Router"
                    concepts.append(values.copy())

                # RV260 VPN Router
                rv260_series = [
                    "cisco rv260",
                    "cisco rv260 router",
                    "cisco rv260w",
                    "cisco rv260w router",
                    "how to configure rv260w router",
                    "rv160 rv260 rv series routers",
                    "rv260",
                    "rv260 series",
                    "rv260p",
                    "rv260w",
                    "rv260w router",
                    "rv260w router set up",
                    "rv260w router setup",
                    "rv260w set up",
                    "rv260w setup",
                    "set up rv260w",
                    "set up rv260w router",
                    "setup rv260w router",
                ]
                if any(word in tags for word in rv260_series):
                    values["series"] = "RV260 VPN Router"
                    concepts.append(values.copy())

                # RV320 Series
                rv320_series = ["rv320", "smb-routers-rv320-series"]
                if any(word in tags for word in rv320_series):
                    values["series"] = "RV320 Product Family"
                    concepts.append(values.copy())

                # RV340 Series
                rv340_series = [
                    "rv340",
                    "smb-routers-rv340-series",
                    "cisc rv340 router",
                    "cisco business rv340",
                    "cisco rv340",
                    "cisco rv340 router",
                    "cisco rv340 router policy",
                    "cisco rv340 series",
                    "cisco rv340 series router",
                    "cisco rv340 series routers",
                    "cisco rv340w",
                    "ciscorv340",
                    "rv340 router",
                    "rv340 series",
                    "rv340 series router",
                    "rv340w",
                ]
                if any(word in tags for word in rv340_series):
                    values["series"] = "RV340 Product Family"
                    concepts.append(values.copy())

                # CBW AC
                cbw_ac_series = [
                    "cbw140",
                    "cbw140ac",
                    "cbw141",
                    "cbw141acm",
                    "cbw142",
                    "cbw142acm",
                    "cbw143acm",
                    "cbw144ac",
                    "cbw145",
                    "cbw145ac",
                    "cisco mesh",
                    "cbw240",
                    "cbw240ac",
                ]
                if any(word in tags for word in cbw_ac_series):
                    values["series"] = "Cisco Business Wireless AC"
                    concepts.append(values.copy())

                # CBW AX
                cbw_ax_series = [
                    "cbw150",
                    "cbw150ax",
                    "cbw151",
                    "cbw151ax",
                    "cbw151axm",
                ]
                if any(word in tags for word in cbw_ax_series):
                    values["series"] = "Cisco Business Wireless AX"
                    concepts.append(values.copy())
                # WAP 100 Series
                wap_100_series = [
                    "cisco wap125",
                    "ciscowap150",
                    "configuring wap",
                    "wap125",
                    "wap150",
                    "wap150_indoor_wall_mounting",
                ]
                if any(word in tags for word in wap_100_series):
                    values["series"] = (
                        "Cisco Small Business 100 Series Wireless Access Points"
                    )
                    concepts.append(values.copy())

                # WAP 300 Series
                wap_300_series = [
                    "how to manage channels on wap371",
                    "wap 371",
                    "wap361",
                    "wap371",
                ]

                if any(word in tags for word in wap_300_series):
                    values["series"] = (
                        "Cisco Small Business 300 Series Wireless Access Points"
                    )
                    concepts.append(values.copy())

                # WAP 500 Series
                wap_500_series = [
                    "cisco wap581",
                    "wap571",
                    "wap571_ceiling_mounting",
                    "wap571_indoor_mounting_options",
                    "wap571_wall_mounting",
                    "wap571e",
                    "wap581",
                ]
                if any(word in tags for word in wap_500_series):
                    values["series"] = (
                        "Cisco Small Business 500 Series Wireless Access Points"
                    )
                    concepts.append(values.copy())

                # CP6800 Phones
                cp6800_series = ["cp-6800", "cisco multiplatform firmware"]
                if any(word in tags for word in cp6800_series):
                    values["series"] = (
                        "Cisco IP Phone 6800 Series with Multiplatform Firmware"
                    )
                    concepts.append(values.copy())

                # CP7800 Phones
                cp7800_series = [
                    "7800",
                    "7800 cisco multiplatform phone",
                    "cisco 7800 series ip phone",
                    "cp-7800",
                ]
                if any(word in tags for word in cp7800_series):
                    values["series"] = "Cisco IP Phone 7800 Series"
                    concepts.append(values.copy())

                # CP8800 Phones
                cp8800_series = [
                    "8800",
                    "8800 cisco multiplatform phone",
                    "cisco 8800 series ip phone",
                    "cp-8800",
                    "cisco cp-8800",
                    "8800",
                    "8800 cisco multiplatform phone",
                ]
                if any(word in tags for word in cp8800_series):
                    values["series"] = "Cisco IP Phone 8800 Series"
                    concepts.append(values.copy())

                # Cisco Business Dashboard
                business_dashboard = [
                    "cbd",
                    "cbd 2.3",
                    "cbd licensing",
                    "cbd probe",
                    "business dashboard",
                    "cisco business dashboard",
                    "cisco business dashboard features",
                    "cisco business dashboard network monitoring",
                ]
                if any(word in tags for word in business_dashboard):
                    values["series"] = "Cisco Business Dashboard"
                    concepts.append(values.copy())

                # Cisco Business Mobile App
                business_mobile_app = [
                    "cisco business mobile app",
                    "cisco business mobile app features",
                    "cisco business mobile app installation",
                    "cisco business mobile app setup",
                    "mobile",
                    "mobile app",
                    "mobile network",
                    "mobile network settings",
                ]

                if any(word in tags for word in business_mobile_app):
                    values["series"] = "Cisco Business Mobile App"
                    concepts.append(values.copy())

                # Cisco Business FindIT
                business_findit = [
                    "cisco findit",
                    "cisco findit network management",
                    "cisco findit topology",
                ]
                if any(word in tags for word in business_findit):
                    values["series"] = "Cisco Business FindIT"
                    concepts.append(values.copy())
        return concepts

    def save_videos_to_json(self, path: str):
        try:
            with open(path, "w") as file:
                json.dump(self.videos, file, indent=2)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error saving videos to JSON file. Error: {e}")

    def save_videos_to_csv(self, path: str):
        try:
            df = pd.DataFrame(self.videos)
            df.to_csv(path, index=True)
        except Exception as e:
            print(f"Error saving videos to CSV file. Error: {e}")


GOOGLE_API_KEY = "AIzaSyBk6-IBPgcCK4G8Uelh483sWbq2iguao7k"
PLAYLIST_ID = "PLB4F91009260AB3D7"

channel_ids = ["UCEWiIE6Htd8mvlOR6YQez1g"]

youtube_loader = CiscoYouTubeDataLoader(
    GOOGLE_API_KEY, PLAYLIST_ID, channel_ids, fetch=True
)

youtube_loader.save_videos_to_csv("./data/smb_youtube_videos.csv")
