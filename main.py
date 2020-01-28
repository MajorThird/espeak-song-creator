import configparser
import argparse
import midi
import note
import os
import subprocess
import scipy.io.wavfile
import numpy as np
import math


def add_pause_before_note(wav, n, current_time, samples_per_sec):
    if n.start_time > current_time:
        diff = n.start_time - current_time
        silent_wav = get_silent_wav(diff, samples_per_sec)
        wav = np.concatenate((wav, silent_wav))
        return wav
    else:
        return wav

def get_audio_duration(wav, samples_per_sec):
    return len(wav) / float(samples_per_sec)

def add_to_wave_of_track(wave_of_track, speech_wav, n, current_time, samples_per_sec):
    wave_of_track = add_pause_before_note(wave_of_track, n, current_time, samples_per_sec)
    note_duration = n.end_time - n.start_time
    diff_audio_note = note_duration - get_audio_duration(speech_wav, samples_per_sec)
    silence_after = get_silent_wav(diff_audio_note, samples_per_sec)
    speech_wav = get_speech_wav_with_dynamics(n.velocity, speech_wav)
    wave_of_track = np.concatenate((wave_of_track, speech_wav, silence_after))
    return wave_of_track

def render_track(track, config, track_filename):
    filename = "./tmp/tmp.wav"
    wave_of_track = np.zeros(shape=(0), dtype=np.int16)
    current_time = 0.0
    for n in track:
        step = int(config["PERFORMANCE"]["StepESpeakSpeedIncrease"])
        current_speed = 60
        too_long = True
        while too_long:
            exec_espeak_command(
                phoneme=n.phoneme,
                frequency=get_frequency(n.pitch, config),
                path=config["PATHS"]["PathToESpeak"],
                speed=current_speed,
                filename=filename)

            samples_per_sec, speech_wav = scipy.io.wavfile.read(filename)
            current_speed += step
            if get_audio_duration(speech_wav, samples_per_sec) <= n.end_time - n.start_time:
                too_long = False
        wave_of_track = add_to_wave_of_track(wave_of_track, speech_wav, n, current_time, samples_per_sec)
        current_time = n.end_time
    scipy.io.wavfile.write("./output/" + track_filename, samples_per_sec, wave_of_track)



def get_silent_wav(duration, samples_per_sec):
    number_of_samples = duration * samples_per_sec
    silent = np.zeros(shape=(int(number_of_samples)), dtype=np.int16)
    return silent


def get_speech_wav_with_dynamics(velocity, speech_wav):
    """
    Multiply speech_wav with the factor velocity/max_velocity.
    """
    max_velocity = 127.0
    amplitude = velocity / max_velocity
    speech_wav_dynamic = (speech_wav * amplitude).astype(np.int16)
    return speech_wav_dynamic


def get_frequency(midi_pitch, config):
    reference_freq = float(config["SOUND"]["ReferenceFrequency"])
    reference_midi_pitch = 69
    f = math.pow(2.0, (midi_pitch - reference_midi_pitch) /
                 12.0) * reference_freq
    return f


def get_pitch(frequency):
    """
    Depending on the frequency, one might
    want to adjust the eSpeak command-line parameter p
    to change the timbre. This function returns the values
    I found pleasing.
    """
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


def exec_espeak_command(
        path="./",
        phoneme="a",
        language="de",
        frequency=70,
        speed=63,
        filename="out.wav"):
    """
    This runs eSpeak. eSpeak creates a wave file.
    Please note that this only works with a modified
    version of eSpeak that accepts the command-line
    parameter e for the frequency of the note.
    """
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


def is_note_on(event):
    velocity = event.data[1]
    return event.name == "Note On" and velocity > 0


def flatten_list(l):
    return [n for k in l for n in k]


def read_midi(filename):
    """
    Create tracks containing Note objects.
    The start and end times of the notes are not yet calculated;
    this is done separately.
    """
    midi_tracks = midi.read_midifile(filename)
    resolution = midi_tracks.resolution
    tempo_bpm = 120.0  # may be changed repeatedly in the loop
    note_tracks = []
    for t_index, t in enumerate(midi_tracks):
        notes_pitchwise = [[] for i in range(128)]
        total_ticks = 0
        for elem in t:
            total_ticks += elem.tick
            if elem.name in ["Note On", "Note Off"]:
                pitch = elem.data[0]
                if is_note_on(elem):
                    n = note.Note(
                        velocity=elem.data[1],
                        pitch=pitch,
                        start_ticks=total_ticks)
                    notes_pitchwise[pitch].append(n)
                else:
                    for n in reversed(notes_pitchwise[pitch]):
                        if not n.finished:
                            n.end_ticks = total_ticks
                            n.finished = True
                        else:
                            break
            elif elem.name == "Set Tempo":
                tempo_bpm = elem.get_bpm()
        notes = flatten_list(notes_pitchwise)
        notes = sorted(notes, key=lambda x: x.start_ticks)
        if notes != []:
            note_tracks.append(notes)
    return note_tracks, tempo_bpm, resolution


def calculate_note_time(note_tracks, tempo_bpm, resolution):
    for t in note_tracks:
        for n in t:
            n.calculate_start_and_end_time(tempo_bpm, resolution)

def render_tracks(note_tracks, config):
    subprocess.call(["mkdir", "-p", "tmp"])
    for t_index, t in enumerate(note_tracks):
        track_filename = "track_%i.wav" % t_index
        print("Render track " + str(t_index))
        render_track(t, config, track_filename)
    subprocess.call(["rm", "-r", "tmp"])

def assign_phonemes_to_notes(note_tracks, phonemes):
    for t_index, t in enumerate(note_tracks):
        for note, phoneme in zip(t, phonemes[t_index]):
            note.phoneme = phoneme


def convert(config):
    filename = config["PATHS"]["PathToMidiFile"]
    note_tracks, tempo_bpm, resolution = read_midi(filename)
    calculate_note_time(note_tracks, tempo_bpm, resolution)
    phonemes = get_phonemes(config["PATHS"]["PathToPhonemes"])
    assign_phonemes_to_notes(note_tracks, phonemes)
    render_tracks(note_tracks, config)


def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def remove_multiple_whitespaces(s):
    return ' '.join(s.split())


def get_phonemes(filename):
    phoneme_tracks = []
    with open(filename) as infile:
        content = infile.read().replace("\n", " ")
        content = remove_multiple_whitespaces(content)
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
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        default="options.cfg",
        help="path to program options file")
    arguments = vars(parser.parse_args())
    filename = arguments["config"]
    config = get_config(filename)
    convert(config)


if __name__ == '__main__':
    main()
