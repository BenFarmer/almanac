#!/bin/env python

""" event_coordinator also determines if a likely or random event will attempt to occur.
    Any astral or natural event that does attempt to occur will be inserted into
    their respective table to be verified later by master timer.
"""


# BUILT IN
import random

# THIRD PARTY
import sqlite3

# PERSONAL
from almanacmodules import cfg
from almanacmodules.astral import AstralInfo
from almanacmodules.natural import NaturalInfo

c = sqlite3.connect(r"/home/ben/Envs/databases/sqlite/Almanac.db")

# LIKELY EVENT CONSTANTS
DAYS_PAST = 7  # how many prior days are looked at for scoring
REGION_ID = 2

# past_weather list variables
DAY_NUM = 0
SEASON = 1
REGION_ID = 2
BIOME_NAME = 3
WEIGHT = 7

# score math variables
SCORE_START = 0
WEATHER_WEIGHT = 4
SCORE_LIMIT = 190

# RANDOM EVENT CONSTANTS
LOCATION = 0
EVENT = 1
SEVERITY = 2


class LikelyEvent:
    """this takes the precipitation score of each region and decides whether or not
    precipitation occurs in that region. If precipitation does occur, then this
    updates both regional_weather and master_timeline tables with that information.
    This needs to then:
        - communicate with prereqs module to see if precipitation causes any events
    """

    def __init__(self, day_num, season, country_id):
        self.day_num = day_num
        self.season = season
        self.country_id = country_id
        self.past_date = self.day_num - DAYS_PAST
        self.cursor = c.cursor()

    def read_weather(self):
        fetch_past_weather = f"SELECT * FROM regional_weather WHERE day_num <= {self.day_num} and day_num >= {self.past_date}"

        self.cursor.execute(fetch_past_weather)
        rows = self.cursor.fetchall()
        past_weather = []
        for row in rows:
            past_weather.append(
                (
                    row[DAY_NUM],
                    row[SEASON],
                    row[REGION_ID],
                    row[BIOME_NAME],
                    row[WEIGHT],
                )
            )
        self._likely_event_logic(past_weather)

    def _likely_event_logic(
        self, past_weather
    ):  # this should probably be renamed to something like 'update precip'
        region_index = past_weather[-1][
            REGION_ID
        ]  # returns the largest region_id which is also the number of regions
        current_day = past_weather[
            -region_index:
        ]  # last set of weather from past_weather

        #        print()
        #        print(f"----------------- DAY NUM: {self.day_num} -----------------")
        for region in current_day:
            global score
            score = SCORE_START

            for weather in past_weather:
                if weather[REGION_ID] == region[REGION_ID]:
                    score += weather[WEATHER_WEIGHT]
            if score >= SCORE_LIMIT:
                self.cursor.execute(
                    f"UPDATE regional_weather SET precip_event = 1 WHERE day_num = {self.day_num} AND region_id = {region[2]}"
                )
                self.cursor.execute(
                    f"UPDATE master_timeline SET precip_event = 1 WHERE day_num = {self.day_num} AND region_id = {region[2]}"
                )
                c.commit()


class RandomEvent:
    def __init__(self, day_num, season, country_id, indv_biomes_config):
        """LargeEvent handles the decisions needed to piece together a large scale event.
        These events generally have country-wide implications, but also can have small
        scale effects as well."""
        self.day_num = day_num
        self.season = season
        self.country_id = country_id
        self.indv_biomes_config = indv_biomes_config
        self.event_details = None
        self.cursor = c.cursor()

    def event(self):
        random_events = (
            "astral",
            "natural",
        )

        pick = random.randint(0, len(random_events) - 1)
        self.event_type = random_events[pick]

        if self.event_type == "astral":
            astral_info = AstralInfo()
            self.event_details = astral_info.get_astral()

            astral_name = self.event_details[0][1]
            astral_type = self.event_details[0][2]
            event_description = self.event_details[0][3]
            input_astral = f"""
                INSERT INTO astral_events
                    (day_num, season, astral_name, astral_type, event_description)
                VALUES
                    ({self.day_num}, '{self.season}', '{astral_name}',
                    '{astral_type}', '{event_description}')
                """
            self.cursor.execute(input_astral)
            c.commit()
            # [(61, 'Helene', 'moon', 'has eclipsed the sun,')]

        elif self.event_type == "natural":
            natural_info = NaturalInfo(self.country_id)
            natural_info.load_config()
            self.event_details = natural_info.decide_natural(self.indv_biomes_config)
            events = []
            # this works but natural is only returning 1 event for each day
            for event in self.event_details:
                region_id = event[LOCATION].indv_id
                biome_name = event[LOCATION].biome_name
                event_name = event[EVENT]
                severity = event[SEVERITY]
                event_description = None
                events.append(
                    (region_id, biome_name, event_name, severity, event_description)
                )

            for event in events:
                region_id = event[0]
                biome_name = event[1]
                event_name = event[2]
                severity = event[3]
                event_description = event[4]
                input_natural = f"""
                    INSERT INTO natural_events
                        (day_num, season, region_id, biome_name, event_name, severity, event_description)
                    VALUES
                        ({self.day_num}, '{self.season}', {region_id}, '{biome_name}',
                        '{event_name}',{severity}, '{event_description}')
                    """
                self.cursor.execute(input_natural)
                c.commit()

            # [(IndvBiome(indv_id=56, biome_name='swamp', cell_position_x=2, cell_position_y=0,
            #    region_id=21), ('sinkhole', 'thunderstorm')]


class EventCoordinator:
    def __init__(self, day_num, country_id, season_id, indv_biomes_config):
        """EventCoordinator has a few important responsibilities.
        1 - reference SQLite reader and a prerequisites module to determine if there are any
            events (large/major/global or small/minor/local) that *should* happen.
        2 - determine if an event tries happens randomly, then gather the details of that event
            from whatever module is necessary, then send that information into the correct table.
        """
        self.day_num = day_num
        self.country_id = country_id
        self.season_id = season_id
        self.indv_biomes_config = indv_biomes_config

        self.cursor = c.cursor()
        self._event_determiner()

    def _event_determiner(self):
        likely_event = LikelyEvent(self.day_num, self.season_id, self.country_id)
        random_event = RandomEvent(
            self.day_num, self.season_id, self.country_id, self.indv_biomes_config
        )

        def _random_check():
            if random.randint(0, 100) > cfg.random_event_chance:
                self.random_event = None
            else:
                random_event.event()

        likely_event.read_weather()
        _random_check()
