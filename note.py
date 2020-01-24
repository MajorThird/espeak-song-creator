class Note(object):
    def __init__(self, velocity=127, pitch=50, start_ticks=0, track=0, syllable="a"):
        self.velocity = velocity
        self.pitch = pitch
        self.start_ticks = start_ticks
        self.track = track
        self.syllable = syllable

    def __str__(self):
        out_string = "Note velocity=%i pitch=%i start_ticks=%i track=%i syllable=%s" % (
            self.velocity, self.pitch, self.start_ticks, self.track, self.syllable)
        return out_string
