import configparser
import argparse
import midi
import note
import os
import subprocess
import scipy.io.wavfile
import numpy as np
import math


def render_track(track, config, track_filename):
    subprocess.call(["mkdir", "-p", "tmp"])
    total_wav = np.zeros(shape=(0), dtype=np.int16)
    current_time = 0.0
    for n_index, n in enumerate(track):
        duration = n.end_time - n.start_time
        filename = "./tmp/tmp.wav"
        for s in range(55,300,1):
            freq = get_frequency(n.pitch)
            exec_espeak_command(phoneme=n.phoneme, frequency=freq, path=config["DEFAULT"]["PathToESpeak"], speed=s, filename=filename)

            samples_per_sec, speech_wav = scipy.io.wavfile.read(filename)
            sample_length = 1.0 / samples_per_sec
            audio_duration = len(speech_wav) * sample_length
            if audio_duration <= duration:
                if n.start_time > current_time:
                    diff = n.start_time - current_time
                    silent_wav = get_silent_wav(diff, samples_per_sec)
                    total_wav = np.concatenate((total_wav, silent_wav))

                diff_audio_note = duration - audio_duration
                silence_to_compensate_short_audio = get_silent_wav(diff_audio_note, samples_per_sec)
                speech_wav = get_speech_wav_with_dynamics(n.velocity, speech_wav)
                total_wav = np.concatenate((total_wav, speech_wav))
                total_wav = np.concatenate((total_wav, silence_to_compensate_short_audio))
                #print("filename: " + str(track_filename) + "  current_time: " + str(current_time))
                current_time = n.end_time
                break
    scipy.io.wavfile.write("./output/" + track_filename, samples_per_sec, total_wav)
    subprocess.call(["rm", "-r", "tmp"])


def get_silent_wav(duration, samples_per_sec):
    number_of_samples = duration * samples_per_sec
    silent = np.zeros(shape=(int(number_of_samples)), dtype=np.int16)
    return silent

def get_speech_wav_with_dynamics(velocity, speech_wav):
    max_velocity = 127.0
    amplitude = velocity / max_velocity
    speech_wav_dynamic = (speech_wav * amplitude).astype(np.int16)
    return speech_wav_dynamic

def get_frequency(midi_pitch):
    reference_freq = 432.0
    reference_midi_pitch = 69
    f = math.pow(2.0, (midi_pitch - reference_midi_pitch) / 12.0 ) * reference_freq
    return f



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

def exec_espeak_command(path="./", phoneme="a", language="de", frequency=70, speed=63, filename="out.wav"):
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
    call_list.append("[[%s]]" % phoneme)
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
    tempo_bpm = 0.0
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
                # print(tempo_bpm)

    notes = [n for l in notes_pitchwise for n in l]
    notes = sorted(notes, key=lambda x: x.start_ticks)

    # print("Hallo", filename)
    # for n in notes:
    #     print(n)
    return notes

def group_notes_by_ticks(notes):
    grouped = [[notes[0]]]
    for n in notes[1:]:
        if n.start_ticks == grouped[-1][0].start_ticks:
            grouped[-1].append(n)
        else:
            grouped.append([n])

    return grouped


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

def get_tracks_from_notes(notes):
    tracks = []
    for n in notes:
        track_no = n.track
        while len(tracks) < track_no + 1:
            tracks.append([])
        tracks[track_no].append(n)
    tracks_wo_empty = [t for t in tracks if t != []]
    return tracks_wo_empty

def humanize(g_quantized, g_human):
    for g_quantized, g_human in zip(g_quantized,g_human):
        human_dict = {}
        for n in g_human:
            human_dict[n.pitch] = n
        for n in g_quantized:
            n.start_ticks = human_dict[n.pitch].start_ticks
            n.start_time = human_dict[n.pitch].start_time
            n.end_ticks = human_dict[n.pitch].end_ticks
            n.end_time = human_dict[n.pitch].end_time
            n.velocity = human_dict[n.pitch].velocity


def midi_tests(config):
    filename_human = config["DEFAULT"]["PathToMidiFileHuman"]
    filename_quantized = config["DEFAULT"]["PathToMidiFile"]

    notes_quantized = read_midi(filename_quantized)

    grouped_notes_quantized = group_notes_by_ticks(notes_quantized)

    notes_human = read_midi(filename_human)
    grouped_notes_human = group_notes_by_ticks(notes_human)
    humanize(grouped_notes_quantized, grouped_notes_human)


    tracks = get_tracks_from_notes(notes_quantized)
    phonemes = get_phonemes(config["DEFAULT"]["PathToPhonemes"])
    for t_index, t in enumerate(reversed(tracks)):
        for note, phoneme in zip(t, phonemes[t_index]):
            note.phoneme = phoneme
        track_filename = "track_%i.wav" % t_index
        render_track(t, config, track_filename)


def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

def get_phonemes(filename):
    phoneme_tracks = []
    with open(filename) as infile:
        content = infile.read().replace("\n", " ").replace("  ", " ")
        for c in content.split(" "):
            if c == "[track]":
                phoneme_tracks.append([])
            else:
                phoneme_tracks[-1].append(c)
    return phoneme_tracks

def main():
    subprocess.call(["rm", "-r", "output"])
    subprocess.call(["mkdir", "-p", "output"])

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=False, default="options.cfg", help="path to program options file")
    arguments = vars(parser.parse_args())

    filename = arguments["config"]
    config = get_config(filename)

    midi_tests(config)


if __name__ == '__main__':
    main()
