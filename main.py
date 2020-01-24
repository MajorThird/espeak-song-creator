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
    for t in midi_tracks:
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                if not is_note_off(elem):
                    n = note.Note(velocity=elem.data[1], pitch=elem.data[0], start_ticks=total_ticks)
                    notes.append(n)
    notes = sorted(notes, key=lambda x: x.start_ticks)
    return notes


def midi_tests(config):
    filename = config["DEFAULT"]["PathToMidiFileHuman"]
    notes = read_midi(filename)



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
