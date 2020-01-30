# espeak-song-creator
Let eSpeak sing your songs!
The program takes a MIDI file and a text file as an input.

## Required packages
* NumPy
* SciPy
* [Python MIDI](https://github.com/vishnubob/python-midi)

## How to modify eSpeak
Unfortunately, my code does not run out of the box.
If you want to use it, you must download eSpeak, modify its code and compile it.
* You should start by implementing a method to control the pitch of the
spoken/sung tones. The built-in method (command-line parameter p) is not sufficient because you have to set the exact frequency. I have shown how to do this in a
[ YouTube video](https://www.youtube.com/watch?v=UTu5fP0lrjY).
* You have to implement a new  command-line parameter to set the frequency. I gave it the letter e. I have not covered this in the aforementioned tutorial.

## Usage
* Please check the exemplary MIDI file and the corresponding phonemes in the folder [input](https://github.com/MajorThird/espeak-song-creator/tree/master/input) to find out how the files must look like.
* The paths to eSpeak and the input files must be provided in [options.cfg](https://github.com/MajorThird/espeak-song-creator/blob/master/readme/options.cfg).
* Run `python main.py`.
