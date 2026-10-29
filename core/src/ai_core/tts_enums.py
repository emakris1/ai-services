import enum


class Language(enum.Enum):
    AMERICAN_ENGLISH = 'a'
    BRITISH_ENGLISH = 'b'
    SPANISH = 'e'


class Voice(enum.Enum):
    AMERICAN_MALE_ADAM = 'am_adam'
    AMERICAN_MALE_ECHO = 'am_echo'
    AMERICAN_MALE_ERIC = 'am_eric'
    AMERICAN_MALE_FENRIR = 'am_fenrir'
    AMERICAN_MALE_LIAM = 'am_liam'
    AMERICAN_MALE_MICHAEL = 'am_michael'
    AMERICAN_MALE_ONYX = 'am_onyx'
    AMERICAN_MALE_PUCK = 'am_puck'
    AMERICAN_MALE_SANTA = 'am_santa'

    AMERICAN_FEMALE_HEART = 'af_heart'
    AMERICAN_FEMALE_ALLOY = 'af_alloy'
    AMERICAN_FEMALE_AOEDE = 'af_aoede'
    AMERICAN_FEMALE_BELLA = 'af_bella'
    AMERICAN_FEMALE_JESSICA = 'af_jessica'
    AMERICAN_FEMALE_KORE = 'af_kore'
    AMERICAN_FEMALE_NICOLE = 'af_nicole'
    AMERICAN_FEMALE_NOVA = 'af_nova'
    AMERICAN_FEMALE_RIVER = 'af_river'
    AMERICAN_FEMALE_SARAH = 'af_sarah'
    AMERICAN_FEMALE_SKY = 'af_sky'

    BRITISH_MALE_DANIEL = 'bm_daniel'
    BRITISH_MALE_FABLE = 'bm_fable'
    BRITISH_MALE_GEORGE = 'bm_george'
    BRITISH_MALE_LEWIS = 'bm_lewis'

    BRITISH_FEMALE_ALICE = 'bf_alice'
    BRITISH_FEMALE_EMMA = 'bf_emma'
    BRITISH_FEMALE_ISABELLA = 'bf_isabella'
    BRITISH_FEMALE_LILY = 'bf_lily'

    SPANISH_MALE_ALEX = 'em_alex'
    SPANISH_MALE_SANTA = 'em_santa'

    SPANISH_FEMALE_DORA = 'ef_dora'

def get_voice(index: int) -> Voice:
    voices = list(Voice)
    if index >= len(voices):
        raise ValueError(f'Voice index {index} is out of range')

    return voices[index]
