import os
from osrparse import parse_replay_file
from enum import Enum
import hashlib
import csv
from tkinter import *

# Folder locations to use
LEGIT_DIR = "legit_spin"
CHEAT_DIR = "cheat_spin"
PROCESS_DIR = "replays/to_process"
DONE_DIR = "replays/done"
BEATMAP_DIR = "spinner_beatmaps"

# Key mappings
LEGIT_KEY = 'a'
CHEAT_KEY = 'd'


def split_after(s, sep):
    return s.split(sep)[1]


HitObjectType = Enum("HitObjectType", "circle slider spinner")

class HitObject(object):
    pass


class Beatmap(object):
    """Incomplete Beatmap class to store info about a beatmap."""
    def __init__(self, beatmap_path):
        self.path = beatmap_path

        _ln = 0  # Internal line num counter

        with open(beatmap_path) as f:
            lines = f.read().splitlines()

        self.format_version = int(split_after(lines[0], 'v'))

        # Fast-forward to metadata
        while lines[_ln] != "[Metadata]":
            _ln += 1

        self.title           = split_after(lines[_ln+1], "Title:")
        self.title_unicode   = split_after(lines[_ln+2], "TitleUnicode:")
        self.artist          = split_after(lines[_ln+3], "Artist:")
        self.artist_unicode  = split_after(lines[_ln+4], "ArtistUnicode:")
        self.creator         = split_after(lines[_ln+5], "Creator:")
        self.version         = split_after(lines[_ln+6], "Version:")
        self.source          = split_after(lines[_ln+7], "Source:")
        self.tags            = split_after(lines[_ln+8], "Tags:").split(' ')
        self.beatmap_id      = int(split_after(lines[_ln+9], "BeatmapID:"))
        self.beatmap_set_id  = int(split_after(lines[_ln+10], "BeatmapSetID:"))

        # Fast-forward to hit objects
        while lines[_ln] != "[HitObjects]":
            _ln += 1

        _ln += 1

        self.hit_objects = []

        while _ln != len(lines):
            h = HitObject()
            vals = lines[_ln].split(',')
            h.x, h.y, h.time, h.type, h.hit_sound = \
                (int(v) for v in vals[:5])

            h.new_combo = bool(h.type & 4)

            if h.type & 1:
                h.type_decoded = HitObjectType.circle
                # Not implemented

            if h.type & 2:
                h.type_decoded = HitObjectType.slider
                # Not implemented

            if h.type & 8:
                h.type_decoded = HitObjectType.spinner

                h.end_time = int(vals[5])
                # Addition not implemented

            self.hit_objects.append(h)
            _ln += 1



def extract_spinner_movement(replay, beatmap):
    """Returns list of lists, with each sublist representing 1 spinner
    (consisting of coordinate pairs)"""
    spinners_times = []  # start and end in ms
    spinners_coords = []

    for hitobj in beatmap.hit_objects:
        if hitobj.type_decoded == HitObjectType.spinner:
            spinners_times.append((hitobj.time, hitobj.end_time))
            spinners_coords.append([])

    print("Spinner times:", spinners_times)


    current_time = 0
    for event in replay.play_data:

        current_time += event.time_since_previous_action

        # Assuming current_time is increasing, this can be made more efficient
        # TODO: handle large negative offsets
        for i in range(len(spinners_times)):
            if spinners_times[i][0] <= current_time <= spinners_times[i][1]:
                spinners_coords[i].append((event.x, event.y))

    print("Spinner lengths (frames):", [len(s) for s in spinners_coords])

    return spinners_coords


class Callback(object):
    def __init__(self):
        self.data = None
        self.quit = False

    def key(self, event):
        """tkinter key event"""
        print("Pressed", event.char)
        self.data = event.char

        if event.char in (LEGIT_KEY, CHEAT_KEY):
            self.quit = True


def visualize(replay, coords, beatmap, width=512, height=384, animate=True):
    """Simple tkinter spinner cursor movement drawer. Returns key press data"""
    master = Tk()

    w = Canvas(master, width=width, height=height)
    w.focus_set()
    callback = Callback()
    w.bind("<Key>", callback.key)
    w.pack()

    w.frame = 0
    frame_delay = 10 if animate else 0

    def draw_frame():
        w.create_line(coords[w.frame][0], coords[w.frame][1],
                      coords[w.frame + 1][0], coords[w.frame + 1][1])

        w.frame += 1
        if w.frame < len(coords) - 1:
            w.after(frame_delay, draw_frame)
        else:
            w.after(0, done_wait())

    def done_wait():
        if callback.quit:
            master.destroy()
            return

        w.after(0, done_wait)


    # Draw center
    w.create_line(width/2 - 5, height/2, width/2 + 5, height/2, fill="red")
    w.create_line(width/2, height/2 - 5, width/2, height/2 + 5, fill="red")

    # Add info text
    key_str = "Legit: {}\nCheat: {}".format(LEGIT_KEY, CHEAT_KEY)
    info_str = replay.player_name + '\n' + beatmap.path
    w.create_text(5, height-30, text=info_str, anchor=W, width=width)
    w.create_text(5, 20, text=key_str, anchor=W)


    draw_frame()
    mainloop()

    return callback.data


def write_coords_csv(replay, spinner_ind, coords, dir):
    os.makedirs(dir, exist_ok=True)
    filename = "{}.{}.{}.csv".format(
        replay.player_name, replay.filename, spinner_ind)
    path = os.path.join(dir, filename)

    with open(path, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for coord_pair in coords:
            writer.writerow(coord_pair)

    print("Wrote csv to", path)


def main():
    # Create hashes of beatmaps and store as dict
    beatmap_dict = dict()

    for filename in os.listdir(BEATMAP_DIR):
        full_path = os.path.join(BEATMAP_DIR, filename)
        md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
        print("Loaded beatmap", filename, md5)
        beatmap_dict[md5] = Beatmap(full_path)


    # Process replays
    for filename in os.listdir(PROCESS_DIR):
        print("Processing replay " + str(filename) + "... ", end='')
        replay = parse_replay_file(os.path.join(PROCESS_DIR, filename))
        replay.filename = filename  # Save filename from osu page


        # Found matching beatmap
        if replay.beatmap_hash in beatmap_dict:
            print("Found matching beatmap")
            move_done = False 
            beatmap = beatmap_dict[replay.beatmap_hash]
            spinners_coords = extract_spinner_movement(replay, beatmap)

            # Handle multiple spinners per map
            for i in range(len(spinners_coords)):
                coords = spinners_coords[i]
                key_data = visualize(replay, coords, beatmap)
                print("Returning key from visualization", key_data)

                if key_data == LEGIT_KEY:
                    write_coords_csv(replay, i, coords, LEGIT_DIR)
                    move_done = True
                elif key_data == CHEAT_KEY:
                    write_coords_csv(replay, i, coords, CHEAT_DIR)
                    move_done = True
                else:
                    raise ValueError("Bad returned key")

            if move_done:  # Move to done dir
                os.rename(os.path.join(PROCESS_DIR, filename),
                          os.path.join(DONE_DIR, filename))
                print("Moved replay to", os.path.join(DONE_DIR, filename))


        else:
            print("No matching beatmap found! Skipping...")
            continue



if __name__ == "__main__":
    main()