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
    """
    This creates the pause that is required
    if the start time of the note is larger than the end time
    of the previous note.
    """
    if n.start_time > current_time:
        diff = n.start_time - current_time
        silent_wav = get_silent_wav(diff, samples_per_sec)
        wav = np.concatenate((wav, silent_wav))
        return wav
    else:
        return wav


def get_audio_duration(wav, samples_per_sec):
    return len(wav) / float(samples_per_sec)


def add_to_track_wave(
        track_wave,
        speech_wav,
        n,
        current_time,
        samples_per_sec):
    """
    For each note, three parts are added to the wave:
    - a silent wave at the beginning if the start time of
      the note is larger than the end time of the previous note
    - the wave generated by eSpeak
    - another silent wave if the wave generated by
      eSpeak is too short
    """
    track_wave = add_pause_before_note(
        track_wave, n, current_time, samples_per_sec)
    note_duration = n.end_time - n.start_time
    diff_audio_note = note_duration - \
        get_audio_duration(speech_wav, samples_per_sec)
    silence_after = get_silent_wav(diff_audio_note, samples_per_sec)
    speech_wav = get_speech_wav_with_dynamics(n.velocity, speech_wav)
    track_wave = np.concatenate((track_wave, speech_wav, silence_after))
    return track_wave


def render_track(track, config, track_filename):
    tmp_wav_filename = "./tmp/tmp.wav"
    track_wave = np.zeros(shape=(0), dtype=np.int16)
    current_time = 0.0
    step = int(config["PERFORMANCE"]["StepESpeakSpeedIncrease"])
    for n in track:
        current_speed = 60
        too_long = True
        while too_long:
            exec_espeak_command(
                phoneme=n.phoneme,
                frequency=get_frequency(n.pitch, config),
                path=config["PATHS"]["PathToESpeak"],
                speed=current_speed,
                filename=tmp_wav_filename)
            samples_per_sec, speech_wav = scipy.io.wavfile.read(tmp_wav_filename)
            current_speed += step
            duration = get_audio_duration(speech_wav,samples_per_sec)
            if duration <= n.end_time - n.start_time:
                too_long = False
        track_wave = add_to_track_wave(
            track_wave, speech_wav, n, current_time, samples_per_sec)
        current_time = n.end_time
    scipy.io.wavfile.write(
        "./output/" +
        track_filename,
        samples_per_sec,
        track_wave)


def get_silent_wav(duration, samples_per_sec):
    number_of_samples = duration * samples_per_sec
    silent = np.zeros(shape=(int(number_of_samples)), dtype=np.int16)
    return silent


def get_speech_wav_with_dynamics(velocity, speech_wav, max_velocity=127.0):
    """
    Multiply speech_wav with the factor velocity/max_velocity.
    """
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


def calculate_note_times(note_tracks, tempo_bpm, resolution):
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
    calculate_note_times(note_tracks, tempo_bpm, resolution)
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
