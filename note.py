class Note(object):
    def __init__(self, syllable="a", velocity=127, pitch=50, start_ticks=0):
        self.syllable = syllable
        self.velocity = velocity
        self.pitch = pitch
        self.start_ticks = start_ticks
