import configparser
import argparse
import midi
import note


def is_note_off(event):
    velocity = event.data[1]
    name = event.name
    return name == "Note Off" or velocity == 0


def get_time_of_ticks(ticks, resolution, tempo_bpm):
    time_per_beat = 60.0 / tempo_bpm
    time_per_tick = time_per_beat / resolution
    return time_per_tick * float(ticks)

def read_midi(filename):
    midi_tracks = midi.read_midifile(filename)
    resolution = midi_tracks.resolution
    notes = []
    for t_index, t in enumerate(midi_tracks):
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                if not is_note_off(elem):
                    start_time = get_time_of_ticks(total_ticks, resolution, tempo_bpm)
                    n = note.Note(velocity=elem.data[1], pitch=elem.data[0], track=t_index, start_ticks=total_ticks, start_time=start_time)
                    notes.append(n)
            elif elem.name == "Set Tempo":
                tempo_bpm = elem.get_bpm()
                print("Tempo: " + str(tempo_bpm))
    notes = sorted(notes, key=lambda x: x.start_ticks)
    return notes

def group_notes_by_ticks(notes):
    grouped = [[notes[0]]]
    for n in notes[1:]:
        if n.start_ticks == grouped[-1][0].start_ticks:
            grouped[-1].append(n)
        else:
            grouped.append([n])

    return grouped

def humanize_quantized_notes(grouped_notes_quantized, grouped_notes_human):
    for g_quantized, g_human in zip(grouped_notes_quantized,grouped_notes_human):
        for note in g_quantized:
            note.start_ticks = g_human[0].start_ticks
            note.velocity = g_human[0].velocity
    return grouped_notes_quantized

def get_tracks_from_grouped_notes(groups):
    tracks = []
    for group in groups:
        for n in group:
            track_no = n.track
            while len(tracks) < track_no + 1:
                tracks.append([])
            tracks[track_no].append(n)
    tracks_wo_empty = [t for t in tracks if t != []]
    return tracks_wo_empty

def render_track(track):
    for n in track:
        pass


def midi_tests(config):
    filename_human = config["DEFAULT"]["PathToMidiFileHuman"]
    filename_quantized = config["DEFAULT"]["PathToMidiFile"]

    notes_quantized = read_midi(filename_quantized)
    grouped_notes_quantized = group_notes_by_ticks(notes_quantized)

    notes_human = read_midi(filename_human)
    grouped_notes_human = group_notes_by_ticks(notes_human)

    grouped_notes_humanized = humanize_quantized_notes(grouped_notes_quantized, grouped_notes_human)


    tracks = get_tracks_from_grouped_notes(grouped_notes_humanized)
    for t in tracks:
        render_track(t)


def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=False, default="options.cfg", help="path to program options file")
    arguments = vars(parser.parse_args())

    filename = arguments["config"]
    config = get_config(filename)

    midi_tests(config)


if __name__ == '__main__':
    main()
