from googleapiclient.discovery import build

class YouTubeAPI:

    def __init__(self, api_key):

        self.youtube = build(
            "youtube",
            "v3",
            developerKey=api_key
        )

    def get_videos(self, dish):

        request = self.youtube.search().list(
            q=f"{dish} recipe",
            part="snippet",
            maxResults=10,
            type="video",
            order="viewCount"
        )

        response = request.execute()

        videos = []

        for item in response["items"]:

            videos.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "channel": item["snippet"]["channelTitle"]
            })

        return videos