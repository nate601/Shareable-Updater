import spotify
import steam
import pendulum
import json

if __name__ == "__main__":
    gameSharables = steam.GetSharables()
    songSharables = spotify.GetSharables()
    filename = "updatableSharables.md"
    with open(filename, "w") as f:
        f.write("* Recent Game(s)\n")
        for game in gameSharables:
            f.write(f" * ({game['name']})[{game['link']}]\n")
        f.write("* Recent Song(s)\n")
        for song in songSharables:
            f.write(f" * ({song['name']})[{song['link']}]\n")
    with open("sharables.json", "w") as f:
        json.dump({"steam": gameSharables, "spotify": songSharables}, f)
