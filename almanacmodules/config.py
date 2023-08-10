#!/bin/env python

""" config.py contains the BaseModel information for all
    of the pydantic classes used within Almanac. It is also used
    for reference of what fields each class contains.
"""

# BUILT INS
import re

# THIRD PARTY
from pydantic import BaseModel
from pydantic import ValidationError
from pydantic import validator

#       RE USED VALIDATOR FUNCTIONS

# def must_be_a_num(cls, v):
#    if v != int:
#        raise ValueError('must be a number')
#     return v

# def must_not_contain_num(cls, v):   # need to finish building this to reuse

# class biome(BaseModel):
#    forest: int
#    plains: int
#    desert: int
#    swamp: int
#    jungle: int
#    mountain: int
#    lake: int
#    river: int
#    ocean: int
#    beach: int
#    underdark: int
#    urban: int


class world(BaseModel):
    id: int
    name: str
    type: str

    forest: int
    plains: int
    desert: int
    swamp: int
    jungle: int
    mountain: int
    lake: int
    river: int
    ocean: int
    beach: int
    underdark: int
    urban: int

    temp_zone: str
    capital: str
    owner: str


class monster(BaseModel):
    id: int
    name: str
    type: str

    forest: int
    plains: int
    desert: int
    swamp: int
    jungle: int
    mountain: int
    lake: int
    river: int
    ocean: int
    beach: int
    underdark: int
    urban: int


class biome(BaseModel):
    id: int
    name: str


class astral(BaseModel):
    id: int
    name: str
    type: str
    moon_of: str


class natural(BaseModel):
    id: int
    name: str
    forest: int
    plains: int
    desert: int
    swamp: int
    jungle: int
    mountain: int
    lake: int
    river: int
    beach: int
    ocean: int
    underdark: int
    urban: int
    season: str
    temp_zone: list[int]


class effects(BaseModel):
    id: int
    type: str
    rarity: int
    base_duration: int
    tags: list
    effect_text_rarity: list
    initial_text: str
    modifier: list
    effect_text: list
    fallout: list
