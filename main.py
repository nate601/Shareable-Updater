from KavitaModels import Volume
from pydantic import TypeAdapter
import json

import kavita
import spotify
import steam

if __name__ == "__main__":
    gameSharables = steam.GetSharables()
    songSharables = spotify.GetSharables()
    bookSharables = kavita.GetSharables()
    filename = "updatableSharables.md"
    with open(filename, "w") as f:
        f.write("* Recent Game(s)\n")
        for game in gameSharables:
            f.write(f" * ({game['name']})[{game['link']}]\n")
        f.write("* Recent Song(s)\n")
        for song in songSharables:
            f.write(f" * ({song['name']})[{song['link']}]\n")
        f.write("* Recent Book(s)\n")
        for book in bookSharables:
            f.write(f" * ({book['name']})[{book['link']}]\n")
    with open("sharables.json", "w") as f:
        json.dump(
            {"steam": gameSharables, "spotify": songSharables, "kavita": bookSharables},
            f,
        )
    with open("completedBooks.json", "wb") as f:
        ta = TypeAdapter(list[Volume]).dump_json(
            sorted(
                kavita.GetReadVolumes(),
                key=lambda volume: volume.lastReadingProgressLocal,
            )
        )
        f.write(ta)
