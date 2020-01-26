class Note(object):
    def __init__(
            self,
            velocity=127,
            pitch=50,
            start_ticks=0,
            end_ticks=0,
            start_time=0.0,
            end_time=0.0,
            track=0,
            phoneme="a"):
        self.velocity = velocity
        self.pitch = pitch
        self.start_ticks = start_ticks
        self.end_ticks = end_ticks
        self.start_time = start_time
        self.end_time = end_time
        self.track = track
        self.phoneme = phoneme
        self.finished = True

    def __str__(self):
        out_string = "Note velocity=%i pitch=%i start_ticks=%i end_ticks=%i start_time=%.3f end_time=%.3f track=%i phoneme=%s" % (
            self.velocity, self.pitch, self.start_ticks, self.end_ticks, self.start_time, self.end_time, self.track, self.phoneme)
        return out_string
