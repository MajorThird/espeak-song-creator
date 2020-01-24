class Note(object):
    def __init__(self, velocity=127, pitch=50, start_ticks=0, syllable="a"):
        self.velocity = velocity
        self.pitch = pitch
        self.start_ticks = start_ticks
        self.syllable = syllable
