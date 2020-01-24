import configparser
import argparse
import midi



def is_note_off(event):
    velocity = event.data[1]
    name = event.name
    return name == "Note Off" or velocity == 0


def read_midi(filename):
    midi_tracks = midi.read_midifile(filename)
    note_ons = []
    note_offs = []
    for t in midi_tracks:
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                if is_note_off(elem):
                    note_offs.append((total_ticks, elem))
                else:
                    note_ons.append((total_ticks, elem))
    note_ons = sorted(note_ons, key=lambda x: x[0])
    note_offs = sorted(note_offs, key=lambda x: x[0])
    return note_ons, note_offs


def midi_tests(config):
    filename = config["DEFAULT"]["PathToMidiFileHuman"]
    ons, offs = read_midi(filename)



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
