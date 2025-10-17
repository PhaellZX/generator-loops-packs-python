import mido
import random
import time
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import numpy as np

# --- 1. CONFIGURAÇÃO E CONSTANTES ---

NOTES = {'C': 48, 'C#': 49, 'D': 50, 'D#': 51, 'E': 52, 'F': 53,
         'F#': 54, 'G': 55, 'G#': 56, 'A': 57, 'A#': 58, 'B': 59}
SCALES = {'major': [2, 2, 1, 2, 2, 2, 1], 'minor': [2, 1, 2, 2, 1, 2, 2]}
DRUM_MAP = {'kick': 36, 'snare': 38, 'closed_hat': 42, 'open_hat': 46, 'crash': 49, 'ride': 51}
LILYPOND_NOTE_NAMES = ['c', 'cis', 'd', 'dis', 'e', 'f', 'fis', 'g', 'gis', 'a', 'ais', 'b']
LILYPOND_DRUM_MAP = {'kick': 'bd', 'snare': 'sn', 'closed_hat': 'hh', 'open_hat': 'ho', 'crash': 'cc', 'ride': 'cymr'}
TICKS_PER_BEAT = 480

# --- 2. FUNÇÕES AUXILIARES ---

def note_to_midi(note_name: str) -> int:
    if len(note_name) > 1 and note_name[1] in ('#', 'b'): name, octave = note_name[:2], int(note_name[2:])
    else: name, octave = note_name[0], int(note_name[1:])
    if 'b' in name:
        base_notes = list(NOTES.keys())
        note_val = NOTES[name[0]] - 1
        name = base_notes[(note_val - NOTES['C']) % 12]
    return NOTES[name] + (octave - 3) * 12

def get_scale_notes(root_note: str, scale_type: str, octave: int = 3) -> list[int]:
    if scale_type not in SCALES: raise ValueError(f"Escala '{scale_type}' não definida.")
    root_midi = note_to_midi(f"{root_note}{octave}")
    scale_intervals = SCALES[scale_type]
    scale_notes = [root_midi]
    current_note = root_midi
    for interval in scale_intervals:
        current_note += interval
        scale_notes.append(current_note)
    return scale_notes

def get_chord_notes(root_note: int, chord_type: str) -> list[int]:
    if chord_type == 'major': return [root_note, root_note + 4, root_note + 7]
    elif chord_type == 'minor': return [root_note, root_note + 3, root_note + 7]
    elif chord_type == 'dominant7': return [root_note, root_note + 4, root_note + 7, root_note + 10]
    elif chord_type == 'minor7': return [root_note, root_note + 3, root_note + 7, root_note + 10]
    elif chord_type == 'major7': return [root_note, root_note + 4, root_note + 7, root_note + 11]
    elif chord_type == 'power': return [root_note, root_note + 7]
    return [root_note]

def midi_to_lilypond(midi_note: int) -> str:
    octave = (midi_note // 12) - 1
    note_name = LILYPOND_NOTE_NAMES[midi_note % 12]
    octave_char = "'" * (octave - 3) if octave >= 3 else "," * (3 - octave)
    return note_name + octave_char

def _convert_absolute_times_to_delta(track: mido.MidiTrack):
    absolute_messages = list(track)
    track.clear()
    absolute_messages.sort(key=lambda msg: msg.time)
    last_time = 0
    for msg in absolute_messages:
        delta_time = msg.time - last_time
        msg.time = delta_time
        track.append(msg)
        last_time += delta_time
    return track

# --- 3. FUNÇÕES DE GERAÇÃO DE BAIXO (MIDI) ---

def generate_funk_bassline(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=2)
    s16 = TICKS_PER_BEAT // 4
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, _ in progression:
            root_note = scale_notes[degree - 1]
            track.append(mido.Message('note_on', note=root_note, velocity=100, time=0))
            track.append(mido.Message('note_off', note=root_note, velocity=64, time=s16 * 2))
            for _ in range(14):
                if random.random() < 0.7:
                    note_choice = random.choices(['root', 'fifth', 'other'], weights=[0.5, 0.25, 0.25])[0]
                    note_to_play = root_note if note_choice == 'root' else root_note + 7 if note_choice == 'fifth' else random.choice(scale_notes)
                    track.append(mido.Message('note_on', note=note_to_play, velocity=random.randint(85, 105), time=0))
                    track.append(mido.Message('note_off', note=note_to_play, velocity=64, time=s16))
                else: track.append(mido.Message('note_on', note=1, velocity=0, time=s16))
    return track

def generate_jazz_walking_bassline(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=2)
    full_scale = scale_notes + [n + 12 for n in scale_notes]
    q_note = TICKS_PER_BEAT
    prog_len = len(progression)
    for i in range(bars):
        prog_index = i % prog_len
        next_prog_index = (i + 1) % prog_len
        current_root = scale_notes[progression[prog_index][0] - 1]
        next_root = scale_notes[progression[next_prog_index][0] - 1]
        notes = [current_root, random.choice(full_scale), random.choice(full_scale), next_root + random.choice([-1, 1])]
        for note in notes:
            track.append(mido.Message('note_on', note=note, velocity=random.randint(80, 95), time=0))
            track.append(mido.Message('note_off', note=note, velocity=64, time=q_note))
    return track

def generate_blues_bassline(key: str, bars: int) -> mido.MidiTrack:
    track = mido.MidiTrack()
    notes = get_scale_notes(key, 'major', octave=2)
    roots = [notes[0]]*4 + [notes[3]]*2 + [notes[0]]*2 + [notes[4], notes[3], notes[0], notes[4]]
    q_note = TICKS_PER_BEAT
    for i in range(bars):
        root = roots[i % 12]
        pattern = [root, root + 7, root + 9, root + 7] if random.random() > 0.5 else [root, root + 7, root + 12, root + 7]
        for note in pattern:
            track.append(mido.Message('note_on', note=note, velocity=random.randint(90, 100), time=0))
            track.append(mido.Message('note_off', note=note, velocity=64, time=q_note))
    return track

def generate_rock_bassline(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=1)
    e_note = TICKS_PER_BEAT // 2
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, _ in progression:
            root_note = scale_notes[degree - 1]
            for i in range(8):
                note = root_note if i % 4 == 0 else root_note if random.random() < 0.8 else random.choice([root_note + 12, root_note + 7])
                track.append(mido.Message('note_on', note=note, velocity=random.randint(100, 115), time=0))
                track.append(mido.Message('note_off', note=note, velocity=64, time=e_note))
    return track

def generate_reggae_bassline(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=2)
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, chord_type in progression:
            root = scale_notes[degree - 1]
            third = root + (4 if chord_type == 'major' else 3)
            fifth = root + 7
            patterns = [[(TICKS_PER_BEAT * 2, None), (TICKS_PER_BEAT, root), (TICKS_PER_BEAT, fifth)],
                        [(TICKS_PER_BEAT, None), (TICKS_PER_BEAT, root), (TICKS_PER_BEAT, third), (TICKS_PER_BEAT, fifth)]]
            pattern = random.choice(patterns)
            time_delta = 0
            for duration, note in pattern:
                if note:
                    track.append(mido.Message('note_on', note=note, velocity=90, time=int(time_delta)))
                    track.append(mido.Message('note_off', note=note, velocity=64, time=int(duration)))
                    time_delta = 0
                else: time_delta += duration
    return track

# --- 4. FUNÇÕES DE GERAÇÃO DE BATERIA (MIDI) ---

def generate_drum_track(bars: int, pattern: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.append(mido.Message('program_change', channel=9, program=0, time=0))
    s16 = TICKS_PER_BEAT // 4
    for bar in range(bars):
        bar_start_time = bar * TICKS_PER_BEAT * 4
        for instrument, active_16ths in pattern.items():
            for i, is_active in enumerate(active_16ths):
                if is_active:
                    vel = random.randint(90, 110) if instrument == 'snare' else random.randint(100, 120)
                    note = DRUM_MAP[instrument]
                    time_on = bar_start_time + i * s16
                    track.append(mido.Message('note_on', channel=9, note=note, velocity=vel, time=time_on))
                    track.append(mido.Message('note_off', channel=9, note=note, velocity=64, time=time_on + s16 - 1))
    return _convert_absolute_times_to_delta(track)

def generate_rock_drums(bars: int) -> mido.MidiTrack:
    pattern = {'kick': [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0], 'snare': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0], 'closed_hat': [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0]}
    return generate_drum_track(bars, pattern)
def generate_funk_drums(bars: int) -> mido.MidiTrack:
    pattern = {'kick': [1,0,0,0,0,0,1,0,1,1,0,0,0,0,1,0], 'snare': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0], 'closed_hat': [1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,0], 'open_hat': [0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1]}
    return generate_drum_track(bars, pattern)
def generate_jazz_drums(bars: int) -> mido.MidiTrack:
    pattern = {'ride': [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0], 'closed_hat': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0], 'kick': [1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1]}
    return generate_drum_track(bars, pattern)
def generate_blues_drums(bars: int) -> mido.MidiTrack:
    pattern = {'kick': [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0], 'snare': [0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,1], 'closed_hat': [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0]}
    return generate_drum_track(bars, pattern)
def generate_reggae_drums(bars: int) -> mido.MidiTrack:
    pattern = {'kick': [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0], 'snare': [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0], 'closed_hat': [0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0]}
    return generate_drum_track(bars, pattern)

# --- 5. FUNÇÕES DE GERAÇÃO DE PIANO (MIDI) ---

def generate_rock_piano(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=4)
    duration = TICKS_PER_BEAT // 2
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, _ in progression:
            root_note = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root_note, 'power')
            for _ in range(8):
                for note in chord_notes: track.append(mido.Message('note_on', note=note, velocity=95, time=0))
                time_passed = 0
                for note in chord_notes:
                    track.append(mido.Message('note_off', note=note, velocity=64, time=duration - time_passed))
                    time_passed = duration
    return track

def generate_funk_piano(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=4)
    duration = TICKS_PER_BEAT // 4
    pattern = [0,0,0,1,0,1,0,1,0,0,1,0,0,1,0,0]
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, chord_type in progression:
            root_note = scale_notes[degree - 1]
            final_chord_type = 'minor7' if chord_type == 'minor' else 'dominant7'
            chord_notes = get_chord_notes(root_note, final_chord_type)
            time_since_last_note = 0
            for i, is_active in enumerate(pattern):
                if is_active:
                    for note in chord_notes: track.append(mido.Message('note_on', note=note, velocity=100, time=time_since_last_note if note == chord_notes[0] else 0))
                    time_since_last_note = 0
                    for note in chord_notes: track.append(mido.Message('note_off', note=note, velocity=64, time=duration if note == chord_notes[0] else 0))
                time_since_last_note += duration
    return track

def generate_jazz_piano(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=4)
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, chord_type in progression:
            root_note = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root_note, chord_type)
            time_on = TICKS_PER_BEAT
            duration = int(TICKS_PER_BEAT * 1.5)
            for note in chord_notes: track.append(mido.Message('note_on', note=note, velocity=80, time=time_on if note == chord_notes[0] else 0))
            for note in chord_notes: track.append(mido.Message('note_off', note=note, velocity=64, time=duration if note == chord_notes[0] else 0))
    return track

def generate_blues_piano(key: str, bars: int) -> mido.MidiTrack:
    track = mido.MidiTrack()
    notes = get_scale_notes(key, 'major', octave=4)
    roots = [notes[0]]*4 + [notes[3]]*2 + [notes[0]]*2 + [notes[4], notes[3], notes[0], notes[4]]
    for i in range(bars):
        root_note = roots[i % 12]
        chord_notes = get_chord_notes(root_note, 'dominant7')
        for note in chord_notes: track.append(mido.Message('note_on', note=note, velocity=90, time=0))
        for note in chord_notes: track.append(mido.Message('note_off', note=note, velocity=64, time=TICKS_PER_BEAT * 4 if note == chord_notes[0] else 0))
    return track

def generate_reggae_piano(key: str, scale: str, bars: int, progression: list) -> mido.MidiTrack:
    track = mido.MidiTrack()
    scale_notes = get_scale_notes(key, scale, octave=4)
    duration = TICKS_PER_BEAT // 2
    prog_len = len(progression)
    for _ in range(bars // prog_len if prog_len > 0 else bars):
        for degree, chord_type in progression:
            root_note = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root_note, chord_type)
            track.append(mido.Message('note_on', note=1, velocity=0, time=TICKS_PER_BEAT))
            for note in chord_notes: track.append(mido.Message('note_on', note=note, velocity=85, time=0))
            for note in chord_notes: track.append(mido.Message('note_off', note=note, velocity=64, time=duration if note == chord_notes[0] else 0))
            track.append(mido.Message('note_on', note=1, velocity=0, time=TICKS_PER_BEAT - duration))
            for note in chord_notes: track.append(mido.Message('note_on', note=note, velocity=85, time=0))
            for note in chord_notes: track.append(mido.Message('note_off', note=note, velocity=64, time=duration if note == chord_notes[0] else 0))
    return track

# --- 6. FUNÇÕES DE GERAÇÃO DE PARTITURA (LILYPOND) ---

def generate_rock_bass_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=1)
    for _ in range(bars // len(progression)):
        for degree, _ in progression:
            root = scale_notes[degree - 1]
            for i in range(8):
                note = root if i % 4 == 0 else root if random.random() < 0.8 else random.choice([root + 12, root + 7])
                score += midi_to_lilypond(note) + "8 "
            score += "| "
    return score

def generate_funk_bass_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=2)
    for _ in range(bars // len(progression)):
        for degree, _ in progression:
            root = scale_notes[degree - 1]
            score += f"r16 {midi_to_lilypond(root)}16 r8 r16 {midi_to_lilypond(random.choice(scale_notes))}16 r8 r16 {midi_to_lilypond(root+7)}16 r8 | "
    return score

def generate_jazz_bass_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes, full_scale = "", get_scale_notes(key, scale, octave=2), get_scale_notes(key, scale, octave=2) + get_scale_notes(key, scale, octave=3)
    for i in range(bars):
        root = scale_notes[progression[i % len(progression)][0] - 1]
        next_root = scale_notes[progression[(i+1) % len(progression)][0] - 1]
        notes = [root, random.choice(full_scale), random.choice(full_scale), next_root + random.choice([-1, 1])]
        for note in notes: score += f"{midi_to_lilypond(note)}4 "
        score += "| "
    return score

def generate_blues_bass_lilypond(key: str, bars: int) -> str:
    score, notes = "", get_scale_notes(key, 'major', octave=2)
    roots = [notes[0]]*4 + [notes[3]]*2 + [notes[0]]*2 + [notes[4], notes[3], notes[0], notes[4]]
    for i in range(bars):
        root = roots[i % 12]
        score += f"{midi_to_lilypond(root)}4 {midi_to_lilypond(root+7)}4 {midi_to_lilypond(root+9)}4 {midi_to_lilypond(root+7)}4 | "
    return score

def generate_reggae_bass_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=2)
    for _ in range(bars // len(progression)):
        for degree, _ in progression:
            root = scale_notes[degree - 1]
            score += f"r2 {midi_to_lilypond(root)}4 {midi_to_lilypond(root+7)}4 | "
    return score

def generate_rock_piano_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=4)
    for _ in range(bars // len(progression)):
        for degree, _ in progression:
            root = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root, 'power')
            chord_ly = f"<{midi_to_lilypond(chord_notes[0])} {midi_to_lilypond(chord_notes[1])}>"
            score += f"{chord_ly}4 {chord_ly}4 {chord_ly}4 {chord_ly}4 | "
    return score

def generate_funk_piano_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=4)
    for _ in range(bars // len(progression)):
        for degree, chord_type in progression:
            root = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root, 'minor7' if chord_type == 'minor' else 'dominant7')
            chord_ly = f"<{ ' '.join(midi_to_lilypond(n) for n in chord_notes) }>"
            score += f"r8. {chord_ly}16 r8. {chord_ly}16 r8. {chord_ly}16 r8. {chord_ly}16 | "
    return score

def generate_jazz_piano_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=4)
    for _ in range(bars // len(progression)):
        for degree, chord_type in progression:
            root = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root, chord_type)
            chord_ly = f"<{ ' '.join(midi_to_lilypond(n) for n in chord_notes) }>"
            score += f"r4 {chord_ly}4. r8 | "
    return score

def generate_blues_piano_lilypond(key: str, bars: int) -> str:
    score, notes = "", get_scale_notes(key, 'major', octave=4)
    roots = [notes[0]]*4 + [notes[3]]*2 + [notes[0]]*2 + [notes[4], notes[3], notes[0], notes[4]]
    for i in range(bars):
        root = roots[i % 12]
        chord_notes = get_chord_notes(root, 'dominant7')
        chord_ly = f"<{ ' '.join(midi_to_lilypond(n) for n in chord_notes) }>"
        score += f"{chord_ly}1 | "
    return score

def generate_reggae_piano_lilypond(key: str, scale: str, bars: int, progression: list) -> str:
    score, scale_notes = "", get_scale_notes(key, scale, octave=4)
    for _ in range(bars // len(progression)):
        for degree, chord_type in progression:
            root = scale_notes[degree - 1]
            chord_notes = get_chord_notes(root, chord_type)
            chord_ly = f"<{ ' '.join(midi_to_lilypond(n) for n in chord_notes) }>"
            score += f"r4 {chord_ly}8 r8 r4 {chord_ly}8 r8 | "
    return score

def generate_drums_lilypond(bars: int, pattern: dict) -> str:
    score = ""
    for _ in range(bars):
        for i in range(4): # 4 tempos
            notes_in_beat = []
            if pattern.get('kick') and pattern['kick'][i*4]: notes_in_beat.append(LILYPOND_DRUM_MAP['kick'])
            if pattern.get('snare') and pattern['snare'][i*4]: notes_in_beat.append(LILYPOND_DRUM_MAP['snare'])
            if pattern.get('closed_hat') and pattern['closed_hat'][i*4]: notes_in_beat.append(LILYPOND_DRUM_MAP['closed_hat'])
            if pattern.get('ride') and pattern['ride'][i*4]: notes_in_beat.append(LILYPOND_DRUM_MAP['ride'])
            if not notes_in_beat: score += "r4 "
            else: score += f"<{ ' '.join(notes_in_beat) }>4 "
        score += "| "
    return score

def create_pdf_score(folder_path: str, filename: str, bass_ly: str, drums_ly: str, piano_ly: str, title: str):
    lilypond_content = f"""\\version "2.24.4"
\\header {{
  title = "{title}"
  composer = "Generated by LoopGenerator AI"
  tagline = ##f
}}
\\paper {{ #(set-paper-size "a4") }}
\\score {{
  <<
    \\new StaffGroup <<
      \\new Staff \\with {{ instrumentName = "Piano" }} {{
        \\clef treble \\time 4/4 {piano_ly}
      }}
      \\new Staff \\with {{ instrumentName = "Bass" }} {{
        \\clef bass \\time 4/4 {bass_ly}
      }}
    >>
    \\new DrumStaff \\with {{ instrumentName = "Drums" }} {{
      \\drummode {{ \\time 4/4 {drums_ly} }}
    }}
  >>
  \\layout {{ }}
}}
"""
    ly_filepath = os.path.join(folder_path, filename + ".ly")
    try:
        with open(ly_filepath, "w", encoding='utf-8') as f: f.write(lilypond_content)
        print(f"\nChamando LilyPond para gerar '{filename}.pdf'...")
        subprocess.run(
            ["lilypond", "-o", os.path.join(folder_path, filename), ly_filepath],
            check=True, capture_output=True, text=True
        )
        print("Partitura em PDF gerada com sucesso!")
    except FileNotFoundError:
        print("\n--- ERRO --- \n'lilypond' não foi encontrado. Verifique se está instalado e no PATH do sistema.")
    except subprocess.CalledProcessError as e:
        print(f"\n--- ERRO DO LILYPOND ---\n{e.stderr}")

def generate_cover_art(style: str, key: str, bpm: int, folder_path: str, filename: str = "cover_art.png"):
    """
    Gera uma imagem de capa com gradientes suaves e coloridos, adaptada ao gênero musical.
    """
    print(f"\nGerando capa artística com gradientes para o estilo '{style}'...")

    width, height = 800, 800

    # Paletas de cores vibrantes e suaves para cada estilo
    style_palettes = {
        'rock': [(200, 30, 30), (10, 10, 10), (255, 100, 0), (80, 80, 80)],
        'funk': [(230, 50, 200), (255, 150, 0), (100, 0, 150), (255, 255, 0)],
        'jazz': [(10, 20, 80), (180, 150, 100), (200, 200, 220), (50, 50, 50)],
        'blues': [(0, 40, 120), (100, 80, 50), (10, 10, 10), (180, 180, 180)],
        'reggae': [(200, 0, 0), (255, 220, 0), (0, 150, 50), (10, 10, 10)]
    }
    
    # Usando o dicionário correto 'style_palettes'
    palette = style_palettes.get(style, [(0,0,0), (255,255,255)]) # Fallback

    # Adiciona aleatoriedade para garantir capas únicas
    random_seed = hash(f"{style}{key}{bpm}{time.time()}") % (2**32 - 1)
    random.seed(random_seed)
    
    num_blobs = random.randint(3, 5)
    blobs = []
    for _ in range(num_blobs):
        blobs.append({
            'x': random.randint(0, width),
            'y': random.randint(0, height),
            'r': random.randint(min(width, height) // 4, min(width, height) // 2),
            'color': np.array(random.choice(palette))
        })

    # Cria uma grade de coordenadas com NumPy para cálculos rápidos
    x_coords = np.arange(width)
    y_coords = np.arange(height)
    X, Y = np.meshgrid(x_coords, y_coords)

    # Inicializa arrays para acumular as cores e influências
    total_color = np.zeros((height, width, 3), dtype=np.float64)
    total_influence = np.zeros((height, width), dtype=np.float64)

    for blob in blobs:
        # Calcula a distância de cada pixel para o centro do blob (vetorizado)
        dist_sq = (X - blob['x'])**2 + (Y - blob['y'])**2
        
        # A influência é inversamente proporcional ao quadrado da distância
        influence = (blob['r']**2) / (dist_sq + 1e-9) # Adiciona epsilon para evitar divisão por zero
        
        # Acumula a cor ponderada pela influência
        total_color += influence[:, :, np.newaxis] * blob['color']
        total_influence += influence
    
    # Normaliza as cores pela influência total
    # Empilha a influência para poder dividir cada canal de cor (R, G, B)
    total_influence_rgb = np.stack([total_influence] * 3, axis=-1)
    
    # Previne divisão por zero onde a influência é 0
    with np.errstate(divide='ignore', invalid='ignore'):
        img_array = np.where(total_influence_rgb > 1e-6, total_color / total_influence_rgb, 0)

    # Garante que os valores estão no intervalo correto [0, 255]
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(img_array, 'RGB')
    
    # Adicionando Texto
    try:
        draw = ImageDraw.Draw(img)
        try:
            # Tente usar uma fonte mais ousada, se disponível no sistema
            font = ImageFont.truetype("arialbd.ttf", 60)
            small_font = ImageFont.truetype("arial.ttf", 35)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        title_text = f"{style.upper()} LOOP"
        subtitle_text = f"{key.upper()} - {bpm} BPM"
        
        # Cor do texto com uma sombra simples para melhor legibilidade
        shadow_color = (0, 0, 0)
        text_color = (255, 255, 255)
        
        # Título
        bbox = draw.textbbox((0, 0), title_text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos_x, pos_y = (width - text_w) / 2, height * 0.4
        draw.text((pos_x + 2, pos_y + 2), title_text, font=font, fill=shadow_color) # Sombra
        draw.text((pos_x, pos_y), title_text, font=font, fill=text_color)           # Texto

        # Subtítulo
        sub_bbox = draw.textbbox((0, 0), subtitle_text, font=small_font)
        sub_text_w = sub_bbox[2] - sub_bbox[0]
        sub_pos_x, sub_pos_y = (width - sub_text_w) / 2, pos_y + text_h + 10
        draw.text((sub_pos_x + 1, sub_pos_y + 1), subtitle_text, font=small_font, fill=shadow_color) # Sombra
        draw.text((sub_pos_x, sub_pos_y), subtitle_text, font=small_font, fill=text_color)
        
    except (ImportError, AttributeError) as e:
        print(f"Aviso: Não foi possível adicionar texto à capa. Erro: {e}")
    
    # Salvando a imagem
    output_path = os.path.join(folder_path, filename)
    img.save(output_path)
    print(f"Capa artística '{filename}' gerada com sucesso em '{folder_path}'!")

# --- 7. EXECUÇÃO DO SCRIPT ---

if __name__ == "__main__":
    
    # --- PARÂMETROS DE GERAÇÃO ---
    STYLE_TO_GENERATE = 'reggae'  # rock, funk, jazz, blues, reggae
    BARS = 4
    
    print(f"--- Gerando Loop de {STYLE_TO_GENERATE.capitalize()} ---")

    style_configs = {
        'rock': {'key': 'E', 'scale': 'minor', 'bpm': 140, 'progression': [(1, 'minor'), (6, 'major'), (7, 'major'), (5, 'major')]},
        'funk': {'key': 'E', 'scale': 'minor', 'bpm': 110, 'progression': [(1, 'minor'), (4, 'minor'), (5, 'dominant7'), (1, 'minor')]},
        'jazz': {'key': 'C', 'scale': 'major', 'bpm': 120, 'progression': [(2, 'minor7'), (5, 'dominant7'), (1, 'major7'), (1, 'major7')]},
        'blues': {'key': 'A', 'scale': 'major', 'bpm': 130, 'progression': []},
        'reggae': {'key': 'A', 'scale': 'minor', 'bpm': 70, 'progression': [(1, 'minor'), (4, 'minor')]}
    }
    
    drum_patterns = {
        'rock': {'kick': [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0], 'snare': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0]},
        'funk': {'kick': [1,0,0,0,0,0,1,0,1,1,0,0,0,0,1,0], 'snare': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0]},
        'jazz': {'ride': [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0], 'kick': [1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1]},
        'blues': {'kick': [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0], 'snare': [0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,1]},
        'reggae': {'kick': [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0], 'snare': [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]}
    }
    
    config = style_configs.get(STYLE_TO_GENERATE)
    if not config:
        print(f"Erro: Estilo '{STYLE_TO_GENERATE}' não reconhecido.")
        exit()

    KEY, SCALE, BPM, PROGRESSION = config['key'], config['scale'], config['bpm'], config['progression']
    
    if PROGRESSION:
        prog_len = len(PROGRESSION)
        if prog_len > 0:
            PROGRESSION = (PROGRESSION * (BARS // prog_len + 1))[:BARS]

    # --- DICIONÁRIOS DE FUNÇÕES PARA CHAMADA SEGURA ---
    BASS_MIDI_GENERATORS = {
        'rock': generate_rock_bassline, 'funk': generate_funk_bassline, 'jazz': generate_jazz_walking_bassline,
        'blues': generate_blues_bassline, 'reggae': generate_reggae_bassline
    }
    PIANO_MIDI_GENERATORS = {
        'rock': generate_rock_piano, 'funk': generate_funk_piano, 'jazz': generate_jazz_piano,
        'blues': generate_blues_piano, 'reggae': generate_reggae_piano
    }
    DRUM_MIDI_GENERATORS = {
        'rock': generate_rock_drums, 'funk': generate_funk_drums, 'jazz': generate_jazz_drums,
        'blues': generate_blues_drums, 'reggae': generate_reggae_drums
    }
    BASS_LILYPOND_GENERATORS = {
        'rock': generate_rock_bass_lilypond, 'funk': generate_funk_bass_lilypond, 'jazz': generate_jazz_bass_lilypond,
        'blues': generate_blues_bass_lilypond, 'reggae': generate_reggae_bass_lilypond
    }
    PIANO_LILYPOND_GENERATORS = {
        'rock': generate_rock_piano_lilypond, 'funk': generate_funk_piano_lilypond, 'jazz': generate_jazz_piano_lilypond,
        'blues': generate_blues_piano_lilypond, 'reggae': generate_reggae_piano_lilypond
    }
    
    # --- Geração de todas as partes ---
    
    # Chamada explícita para cada instrumento para evitar erros
    if STYLE_TO_GENERATE == 'blues':
        bass_track = BASS_MIDI_GENERATORS['blues'](KEY, BARS)
        piano_track = PIANO_MIDI_GENERATORS['blues'](KEY, BARS)
        bass_ly = BASS_LILYPOND_GENERATORS['blues'](KEY, BARS)
        piano_ly = PIANO_LILYPOND_GENERATORS['blues'](KEY, BARS)
    else:
        bass_track = BASS_MIDI_GENERATORS[STYLE_TO_GENERATE](KEY, SCALE, BARS, PROGRESSION)
        piano_track = PIANO_MIDI_GENERATORS[STYLE_TO_GENERATE](KEY, SCALE, BARS, PROGRESSION)
        bass_ly = BASS_LILYPOND_GENERATORS[STYLE_TO_GENERATE](KEY, SCALE, BARS, PROGRESSION)
        piano_ly = PIANO_LILYPOND_GENERATORS[STYLE_TO_GENERATE](KEY, SCALE, BARS, PROGRESSION)
        
    drum_track = DRUM_MIDI_GENERATORS[STYLE_TO_GENERATE](BARS)
    drums_ly = generate_drums_lilypond(BARS, drum_patterns[STYLE_TO_GENERATE])

    # --- Criação da Pasta e Salvamento dos Arquivos ---
    timestamp = int(time.time())
    folder_name = f"{STYLE_TO_GENERATE}_loop_{KEY.lower().replace('#', 's')}_{BPM}bpm_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)

    # Salvando MIDI combinado
    combined_mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)
    track_bass_copy = bass_track.copy()
    track_piano_copy = piano_track.copy()
    track_drums_copy = drum_track.copy()
    track_bass_copy.insert(0, mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    combined_mid.tracks.extend([track_bass_copy, track_piano_copy, track_drums_copy])
    combined_filepath = os.path.join(folder_name, f"{STYLE_TO_GENERATE}_full_mix.mid")
    combined_mid.save(combined_filepath)

    # Salvando arquivos MIDI individuais
    for instrument, track in [('bass', bass_track), ('drums', drum_track), ('piano', piano_track)]:
        mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)
        track.insert(0, mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
        mid.tracks.append(track)
        filepath = os.path.join(folder_name, f"{STYLE_TO_GENERATE}_{instrument}.mid")
        mid.save(filepath)

    # Gerando a Partitura em PDF
    pdf_title = f"{STYLE_TO_GENERATE.capitalize()} Loop in {KEY.capitalize()}"
    pdf_filename = f"{STYLE_TO_GENERATE}_score"
    create_pdf_score(folder_name, pdf_filename, bass_ly, drums_ly, piano_ly, pdf_title)

    generate_cover_art(
        style=STYLE_TO_GENERATE,
        key=KEY,
        bpm=BPM,
        folder_path=folder_name,
        filename=f"{STYLE_TO_GENERATE}_cover_art.png" # Nome do arquivo da capa
    )

    print("\nSucesso! Loop completo gerado e salvo na pasta:")
    print(f"  --> '{folder_name}'")