import configparser
import argparse
import midi
import note


def is_note_off(event):
    velocity = event.data[1]
    name = event.name
    return name == "Note Off" or velocity == 0


def read_midi(filename):
    midi_tracks = midi.read_midifile(filename)
    notes = []
    for t_index, t in enumerate(midi_tracks):
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                if not is_note_off(elem):
                    n = note.Note(velocity=elem.data[1], pitch=elem.data[0], track=t_index, start_ticks=total_ticks)
                    notes.append(n)
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

def midi_tests(config):
    filename_human = config["DEFAULT"]["PathToMidiFileHuman"]
    filename_quantized = config["DEFAULT"]["PathToMidiFile"]

    notes_quantized = read_midi(filename_quantized)
    grouped_notes_quantized = group_notes_by_ticks(notes_quantized)

    notes_human = read_midi(filename_human)
    grouped_notes_human = group_notes_by_ticks(notes_human)

    grouped_notes_humanized = humanize_quantized_notes(grouped_notes_quantized, grouped_notes_human)
    for g in grouped_notes_humanized:
        for n in g:
            print(n)



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
