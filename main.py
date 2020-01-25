import configparser
import argparse
import midi
import note
import os
import subprocess

def render_track(track, config):
    os.system("mkdir -p tmp")
    for n in track:
        duration = n.end_time - n.start_time
        filename = "./tmp/tmp.wav"
        for s in range(60,300,55):
            exec_espeak_command(syllable=n.syllable, path=config["DEFAULT"]["PathToESpeak"], speed=s, filename=filename)
        #print(n.syllable)
    os.system("rm -r tmp")




def get_pitch(frequency):
    if frequency > 180.0:
        return 99
    elif frequency > 160.0:
        return 89
    elif frequency > 110.0:
        return 59
    elif frequency > 90.0:
        return 39
    elif frequency > 70.0:
        return 10
    else:
        return 1

def exec_espeak_command(path="./", syllable="a", language="de", frequency=70, speed=63, filename="out.wav"):
    pitch = get_pitch(frequency)
    call_list = [path + "speak"]
    call_list.append("-w")
    call_list.append(filename)
    call_list.append("-v")
    call_list.append(language)
    call_list.append("-s")
    call_list.append(str(speed))
    call_list.append("-p")
    call_list.append(str(pitch))
    call_list.append("-e")
    call_list.append(str(frequency))
    call_list.append("[[%s]]" % syllable)
    with open(os.devnull, 'wb') as quiet_output:
        subprocess.call(call_list, stdout=quiet_output, stderr=quiet_output)




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
    notes_pitchwise = [ [] for i in range(128)]
    for t_index, t in enumerate(midi_tracks):
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                pitch = elem.data[0]
                if not is_note_off(elem):
                    start_time = get_time_of_ticks(total_ticks, resolution, tempo_bpm)
                    n = note.Note(velocity=elem.data[1], pitch=pitch, track=t_index, start_ticks=total_ticks, start_time=start_time)
                    n.finished = False
                    notes_pitchwise[pitch].append(n)
                else:
                    time_of_ticks = get_time_of_ticks(total_ticks, resolution, tempo_bpm)
                    for n in reversed(notes_pitchwise[pitch]):
                        if not n.finished:
                            n.end_ticks = total_ticks
                            n.end_time = time_of_ticks
                            n.finished = True
                        else:
                            break

            elif elem.name == "Set Tempo":
                tempo_bpm = elem.get_bpm()

    notes = [n for l in notes_pitchwise for n in l]
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
            note.start_time = g_human[0].start_time
            note.end_time = g_human[0].end_time
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
        render_track(t, config)


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

    # for s in range(60,444,30):
    #     filename = "%i.wav" % s
    #     exec_espeak_command(syllable="hE", path=config["DEFAULT"]["PathToESpeak"], speed=s, filename=filename)
    #     from scipy.io import wavfile
    #     samples_per_sec, wav_data = wavfile.read(filename)
    #     sample_length = 1.0 / samples_per_sec
    #     print("samples_per_sec", samples_per_sec, len(wav_data)*sample_length)

if __name__ == '__main__':
    main()
