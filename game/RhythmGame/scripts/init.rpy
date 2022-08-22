
init -10 python in rhythm_game:

    import enum
    import builtins
    import hashlib
    import re
    import zipfile
    import random
    import threading
    import store
    from os import path
    from renpy import config

    # Code writing for Ren'Py version 8.0.1 and above.
    # On previous versions working capacity is not guaranteed.

    DEBUG = True
    GLOBAL_OFFSET = 40.0
    GLOBAL_HITCIRCLE_ZOOM = 1.5
    
    MUSIC_CHANNEL = "music"

    FORCED_AR = None
    FORCED_OD = None

    BASE_FOLDER = "RhythmGame"  # "game" relative.

    PHI_CONST1 = (((5. ** (1. / 2.)) - 1.) / 2.)
    PHI_CONST1, PHI_CONST2 = (1. - PHI_CONST1), PHI_CONST1

    class _BasicInheritable(store.NoRollback):
        __author__ = "Vladya"
