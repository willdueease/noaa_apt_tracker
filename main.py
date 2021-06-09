import orbit_predictor.predictors
from orbit_predictor.sources import get_predictor_from_tle_lines
from orbit_predictor.locations import Location
# from rtlsdr import RtlSdr
import satellite_tle


class Satellite:
    def __init__(self, norad_number, tle_lines, name):
        self.norad_number = norad_number
        self.name = name
        self.tle_lines = tle_lines
        self.predictor = ""
        self.passes = []

    def predict_passes(self, location, count=5):
        self.predictor = get_predictor_from_tle_lines(self.tle_lines)
        self.passes = []  # Clear the existing pass list
        for i in range(count):
            if len(self.passes) == 0:
                next_pass = self.predictor.get_next_pass(location)
            else:
                new_time = self.passes[i-1].los
                next_pass = self.predictor.get_next_pass(location, new_time)

            print(next_pass.los)
            self.passes.append(next_pass)


class AppManager:
    min_elevation_for_valid_pass = 5  # Degrees
    scheduled_passes = []

    def __init__(self, tracked_satellites: list, station_location: Location):
        self.tracked_satellites = {}
        self.station_location = station_location
        for sat in tracked_satellites:
            tle = satellite_tle.fetch_tle_from_celestrak(sat)  # Get TLE for sat
            name = tle[0]
            tle_lines = tle[1], tle[2]  # Add the TLE to the new object
            new_sat = Satellite(sat, tle_lines, name)  # Create object, extract name from TLE line 0
            self.tracked_satellites[new_sat] = name
        print(f"Created new AppManager object to follow these Satellites:{self.tracked_satellites.keys()}")

    def generate_passes_for_tracked_sats(self, count=5):
        sat: Satellite
        for sat in self.tracked_satellites:
            sat.predict_passes(self.station_location, count)

    def schedule_next_pass(self):
        # Loop through all the passes of all the sats, toss out the ones that don't meet criteria
        sat: Satellite
        for sat in self.tracked_satellites:
            predicted_pass: orbit_predictor.predictors.PredictedPass
            for predicted_pass in sat.passes:
                if predicted_pass.max_elevation_deg > self.min_elevation_for_valid_pass:
                    self.scheduled_passes.append(predicted_pass)

        # Make tuples based off of AOS for each pass
        unordered_list = []
        predicted_pass: orbit_predictor.predictors.PredictedPass
        for predicted_pass in self.scheduled_passes:
            unordered_list.append((predicted_pass.aos, predicted_pass))
        # Sort by time
        sorted_list = sorted(unordered_list)
        tmp = []
        # Extract back into a sorted pass list
        for i in sorted_list:
            tmp.append(i[1])
        sorted_list = tmp
        print("hello")

if __name__ == '__main__':
    location = Location("GNV", 29.618630, -82.306738, 25)
    manager = AppManager([25338, 33591], location)
    manager.generate_passes_for_tracked_sats()
    manager.schedule_next_pass()