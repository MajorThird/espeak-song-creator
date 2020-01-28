class Note(object):
    def __init__(
            self,
            velocity=127,
            pitch=50,
            start_ticks=0,
            end_ticks=0,
            start_time=0.0,
            end_time=0.0,
            phoneme="a"):
        self.velocity = velocity
        self.pitch = pitch
        self.start_ticks = start_ticks
        self.end_ticks = end_ticks
        self.start_time = start_time
        self.end_time = end_time
        self.phoneme = phoneme
        self.finished = True

    def calculate_start_and_end_time(self, tempo_bpm, resolution):
        self.start_time = get_time_of_ticks(self.start_ticks, resolution, tempo_bpm)
        self.end_time = get_time_of_ticks(self.end_ticks, resolution, tempo_bpm)

    def __str__(self):
        out_string = "Note velocity=%i pitch=%i start_ticks=%i end_ticks=%i start_time=%.3f end_time=%.3f phoneme=%s" % (
            self.velocity, self.pitch, self.start_ticks, self.end_ticks, self.start_time, self.end_time, self.phoneme)
        return out_string



def get_time_of_ticks(ticks, resolution, tempo_bpm):
    time_per_beat = 60.0 / tempo_bpm
    time_per_tick = time_per_beat / resolution
    return time_per_tick * ticks
