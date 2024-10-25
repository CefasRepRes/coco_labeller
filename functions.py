
def load_json(file_path):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    return json_data

def select_particles(json_data, particle_ids):
    particles = [p for p in json_data['particles'] if p['particleId'] in particle_ids]
    return particles if particles else None

def get_pulses(particles):
    pulses = {p['particleId']: p.get('pulseShapes') for p in particles}
    return pulses
