from time import sleep
from ytmusicapi import YTMusic
from loguru import logger
from yandex_music import Client
from art import tprint



class Yandex:
    def __init__(self, token):
        self.client = Client(token)
        self.client.init()
    
    def nextLikes(self):
        for track in self.client.users_likes_tracks()[::-1]:
            track = track.fetch_track()
            yield {
                "playlist": "Любимое в Yandex.Music",
                "title": track.title,
                "artists": [artist.name for artist in track.artists],
                "album": track.albums[0].title
            }

    def nextAllPlaylists(self):
        playlists = list(set(self.client.users_playlists_list().extend([like.playlist for like in self.client.users_likes_playlists()])))
        for playlist in playlists:
            for track in  self.client.users_playlists(playlist.kind).tracks:
                track = track.fetch_track()
                yield {
                    "playlist": playlist.title,
                    "title": track.title,
                    "artists": [artist.name for artist in track.artists]
                }


    def playlist(self):
        return list(set(self.client.users_playlists_list().extend([like.playlist for like in self.client.users_likes_playlists()])))

    def nextAlbom(self):
        for album in self.client.users_likes_albums():
            yield {

                "title": album.album.title,
                "artists": [artist.name for artist in album.album.artists]
            }

    def nextLikedArtists(self):
        for artist in self.client.users_likes_artists():
            yield {
                "title": artist.artist.name
            }
        
class Youtube:
    def __init__(self, token):
        self.ytmusic = YTMusic(token)
    
    def createPlaylist(self, title, description):
        return self.ytmusic.create_playlist(title, description)
    
    def addPlaylistItems(self, playlistId, videoId):
        try:
            return self.ytmusic.add_playlist_items(playlistId, [videoId])
        except Exception as ex:
            logger.warning(f"Error added {videoId} to {playlistId} - {ex}")
            sleep(5)
            return self.addPlaylistItems(playlistId, videoId)

    def search(self, query, filter="songs"):
        search = []
        types = ["songs", "albums", "playlists", "artists", "videos"]
        for type in types:
            search.extend(self.ytmusic.search(query, type))
            if len(search) > 0:
                break
        return search


    def rateTrack(self, track):
        search = self.search(track["title"] + " " + track["artists"][0], "songs")
        if len(search) > 0:
            try:
                self.ytmusic.rate_song(search[0]["videoId"], "LIKE")
                logger.success(f"Added: {track['title']} {track['artists'][0]}")
            except Exception as ex:
                logger.warning(f"Error added {track['title']} {track['artists'][0]} - {ex}")
                sleep(5)
                self.rateTrack(track)
                
        else:
            logger.warning(f"Not found: {track['title']} {track['artists'][0]}")

    def rateAlbom(self, albom):
        search = self.search(albom["title"] + " " + albom["artists"][0], "albums")
        if len(search) > 0:
            try:
                self.ytmusic.rate_playlist(search[0]["browseId"], "LIKE")
                logger.success(f"Added: {albom['title']} {albom['artists'][0]}")
            except Exception as ex:
                logger.warning(f"Error added {albom['title']} {albom['artists'][0]} - {ex}")
                
        
        else:
            logger.warning(f"Not found: {albom['title']} {albom['artists'][0]}")


    def ratePlaylist(self, playlist):
        search = self.search(playlist["title"], "playlists")
        if len(search) > 0:
            try:
                self.ytmusic.rate_playlist(search[0]["browseId"], "LIKE")
                logger.success(f"Added: {playlist['title']}")
            except Exception as ex:
                logger.warning(f"Error added {playlist['title']} - {ex}")
                sleep(5)
                self.ratePlaylist(playlist)
        else:
            logger.warning(f"Not found: {playlist['title']}")

    
    def rateAuthor(self, author):
        search = self.search(author["title"], "artists")
        if len(search) > 0:
            try:
                self.ytmusic.subscribe_artists([search[0]["browseId"]])
                logger.success(f"Added: {author['title']}")
            except Exception as ex:
                logger.warning(f"Error added {author['title']} - {ex}")
                sleep(5)
                self.rateAuthor(author)
        else:
            logger.warning(f"Not found: {author['title']}")
            
class YandexToYoutube:
    def __init__(self, yandexToken, youtubeToken):
        self.yandex = Yandex(yandexToken)
        self.youtube = Youtube(youtubeToken)
    
    def run(self):
        self.playlists = {
            name.title: 0 for name in self.yandex.playlist()
            }

        
        for playlist in self.playlists:
            self.playlists[playlist] = self.youtube.createPlaylist(playlist, "By Kado")

        logger.info("Playlists created")

        self.transferLikes()
        self.transferLikedArtists()
        self.transferPLaylist()
        

        
    def transferPLaylist(self):
        for track in self.yandex.nextAllPlaylists():
            search = self.youtube.search(track["title"] + " " + track["artists"][0], "songs")
            if len(search) > 0:
                self.youtube.addPlaylistItems(self.playlists[track["playlist"]], search[0]["videoId"])
                logger.success(f"Added: {track['title']} {track['artists'][0]}")
            else:
                logger.warning(f"Not found: {track['title']} {track['artists'][0]}")


    def transferLikes(self):
        for track in self.yandex.nextLikes():
            self.youtube.rateTrack(track)


    
    def transferAlbom(self):
        for albom in self.yandex.nextAlbom():
            self.youtube.rateAlbom(albom)


    def transferLikedArtists(self):
        for author in self.yandex.nextLikedArtists():
            self.youtube.rateAuthor(author)

if __name__ == "__main__":
    tprint("Yandex to Youtube")
    if input("You want to setting up? (y/n): ") == "y":
        YTMusic.setup(filepath="headers_auth.json")
    YandexToYoutube(input("Input yandex token: "), "headers_auth.json").run()