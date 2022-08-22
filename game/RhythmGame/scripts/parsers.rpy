
init -8 python in rhythm_game:
    
    class _OsuSkin(_BasicInheritable):

        __author__ = "Vladya"
        SKINS_FOLDER = utils.path.renpy_join(BASE_FOLDER, "Skins")
        DEFAULT_SKIN = "_DEFAULT"
        
        def __init__(self, name):
            self.__name = utils.other.get_unicode(name)
            self.__elements = {}
        
        def _visit_disp(self):

            yield self.approachcircle
            yield self.hitcircle
            yield self.hitcircleoverlay

            for i in range(10):
                yield getattr(self, "default_{0}".format(i))
        
        def get_hitcircle_render(
            self,
            state,
            is_available_for_click,
            number=None,
            *render_args
        ):
        
            state = min(max(float(state), .0), 1.)
            hc_overlay_rend = renpy.render(self.hitcircleoverlay, *render_args)
            width, height = map(int, hc_overlay_rend.get_size())

            mix_render = renpy.Render(width, height)
            mix_render.blit(hc_overlay_rend, (0, 0))
            
            if is_available_for_click:
                hc_rend = renpy.render(self.hitcircle, *render_args)
                x = (width * .5) - (hc_rend.width * .5)
                y = (height * .5) - (hc_rend.height * .5)
                x, y = map(int, (x, y))
                mix_render.blit(hc_rend, (x, y))
                
            if number is not None:
                for n in str(number):
                    picture = self.__get_image("default_{0}".format(n))
                    if not picture:
                        continue
                    number_rend = renpy.render(picture, *render_args)
                    x = (width * .5) - (number_rend.width * .5)
                    y = (height * .5) - (number_rend.height * .5)
                    x, y = map(int, (x, y))
                    mix_render.blit(number_rend, (x, y))

            xzoom = utils.other.warp_value(state, lambda a: (a ** (1. / 12.)))
            yzoom = utils.other.warp_value(state, "easeout")

            xzoom *= yzoom
            
            xzoom *= GLOBAL_HITCIRCLE_ZOOM
            yzoom *= GLOBAL_HITCIRCLE_ZOOM

            return utils.render.zoom_render(mix_render, xzoom, yzoom)

        @property
        def name(self):
            return self.__name

        @property
        def approachcircle(self):
            return self.__get_image("approachcircle")

        @property
        def hitcircle(self):
            return self.__get_image("hitcircle")

        @property
        def hitcircleoverlay(self):
            return self.__get_image("hitcircleoverlay")

        def __getattr__(self, name):
            _search = re.search(r"default_\d", name)
            if _search and (_search.group() == name):
                return self.__get_image(name)
            raise AttributeError(name)

        def __get_image(self, element_name):

            element_name = utils.other.get_unicode(element_name)
            element_name = element_name.replace('_', '-')
            if element_name in self.__elements:
                return self.__elements[element_name]

            for variant in (self.name, self.DEFAULT_SKIN):
                fn = utils.path.renpy_join(
                    self.SKINS_FOLDER,
                    variant,
                    "{}.png".format(element_name)
                )

                if not renpy.loadable(fn):
                    continue
                try:
                    result = utils.display.get_imagebase(fn)
                except Exception as ex:
                    if DEBUG:
                        raise ex
                    continue
                else:
                    self.__elements[element_name] = result
                    return result
                    
            return None

    class _HitObjectsGroup(_BasicInheritable):

        __author__ = "Vladya"

        def __init__(self):
        
            self.__start_align = (random.uniform(.0, PHI_CONST1), PHI_CONST1)
            self.__dest_align = (PHI_CONST2, PHI_CONST2)

        @property
        def xalign(self):
            return self.__start_align[0]

        @property
        def yalign(self):
            return self.__start_align[1]

        @property
        def dest_xalign(self):
            return self.__dest_align[0]

        @property
        def dest_yalign(self):
            return self.__dest_align[1]

        
    # https://osu.ppy.sh/wiki/ru/Client/File_formats/Osu_%28file_format%29
    class _HitObject(_BasicInheritable):

        class TypeFlags(enum.IntFlag):
            Circle = 0b0001
            Slider = 0b0010
            NewCombo = 0b0100
            Spinner = 0b1000

        __author__ = "Vladya"

        def __init__(
            self,
            hitobject_time,
            hitobject_type,
            group,
            number_in_group,
            raw_data=None
        ):

            self.__ho_time = float(hitobject_time)
            if not isinstance(hitobject_type, self.TypeFlags):
                raise TypeError("Incorrect type.")
            self.__ho_type = hitobject_type
            
            if not isinstance(group, _HitObjectsGroup):
                raise TypeError("Incorrect type.")

            self.__group = group
            self.__number_in_group = int(number_in_group)

            self.__raw_data = raw_data

        def _calculate_align(self, xstate, ystate=None):
            if ystate is None:
                ystate = xstate
            xalign = self.xalign + ((self.dest_xalign - self.xalign) * xstate)
            yalign = self.yalign + ((self.dest_yalign - self.yalign) * ystate)
            return (xalign, yalign)

        def __hash__(self):
            return hash(
                (
                    self.__ho_time,
                    self.__ho_type,
                    self.__raw_data
                )
            )

        @property
        def number(self):
            return self.__number_in_group

        @property
        def xalign(self):
            return self.__group.xalign

        @property
        def yalign(self):
            return self.__group.yalign

        @property
        def dest_xalign(self):
            return self.__group.dest_xalign

        @property
        def dest_yalign(self):
            return self.__group.dest_yalign

        @property
        def ho_time(self):
            return self.__ho_time
        
        @property
        def ho_type(self):
            return self.__ho_type
            
        @property
        def spinner_end_time(self):
            if self.ho_type is not self.TypeFlags.Spinner:
                return None
            _a, _a, _a, _a, _a, end_time, *_a = self.__raw_data
            return float(end_time)


    class _OsuEvents(_BasicInheritable):

        __author__ = "Vladya"

        def __init__(self, raw_string, zip_object):

            self.__raw_string = utils.other.get_unicode(raw_string)
            
            self.__video_binary = None
            self.__video_filename = None
            video_name = self.__get_video_name()
            if video_name and (video_name in zip_object.namelist()):
                with zip_object.open(video_name) as video_file:
                    self.__video_binary = video_file.read()
                self.__video_filename = video_name

            self.__background_binary = None
            self.__background_filename = None
            filename = self.__get_background_name()
            if filename and (filename in zip_object.namelist()):
                with zip_object.open(filename) as background_file:
                    self.__background_binary = background_file.read()
                self.__background_filename = filename
            
        def get_background(self):
            return (self.__background_filename, self.__background_binary)

        def get_video(self):
            return (self.__video_filename, self.__video_binary)

        def __get_background_name(self):
            for _events in self.__get_background_and_video_events():
                if _events[0] == "Video":
                    continue
                a, b, image_path, *_other = _events
                image_path = image_path[1:-1]
                ext = utils.path.get_ext(image_path)
                if ext in (".jpg", ".jpeg", ".png", ".webp"):
                    return image_path
            return None
        
        def __get_video_name(self):
            for _events in self.__get_background_and_video_events():
                if _events[0] == "Video":
                    _a, _a, video, *_a = _events
                    return video[1:-1]
            return None
        
        def __get_background_and_video_events(self):
        
            for _raw_events in re.finditer(
                r"(?<=//Background and Video events)[^/]+",
                self.__raw_string,
                flags=re.DOTALL
            ):
                _raw_events = _raw_events.group()
                for _string in re.split(r"[\r\n]+", _raw_events):
                    _string = _string.strip()
                    if not _string:
                        continue
                        
                    yield tuple(
                        map(lambda x: x.strip(), re.split(r',', _string))
                    )

    class _OsuMap(_BasicInheritable):

        __author__ = "Vladya"
        
        SECTION_PATTERN = re.compile(
            r"\[(?P<section_name>[^\[\]]+)\](?P<section_data>[^\[\]]*)",
            flags=re.DOTALL
        )
        NO_BACKGROUND = renpy.object.Sentinel("OsuMapNoBackground")
        
        
        class GameModes(enum.IntEnum):
            std = 0
            Taiko = 1
            CtB = 2
            Mania = 3

        def __init__(self, infozip_object, zip_object):
            
            with zip_object.open(infozip_object) as map_file:
                raw_data = map_file.read()
           
            raw_data = utils.other.get_unicode(raw_data)
            self.__sections = dict(self._get_sections_from_text(raw_data))
            
            self.__audio = None
            audio_name = self.get_parameter("General", "AudioFilename")
            with zip_object.open(audio_name) as audio_file:
                self.__audio_binary = audio_file.read()

            self.__events = None
            events_raw = self.get_parameter("Events", _raise=False)
            if events_raw:
                self.__events = _OsuEvents(events_raw, zip_object)
                
            self.__background = None

            self.__hitobjects = self.parse_and_get_hitobjects()
            self.__ar_time = None
            self.__hit_time = None


        def __str__(self):
            return "{0.artist} - {0.title} ({0.version})".format(self)

        def __repr__(self):
            return "<_OsuMap {0}>".format(self.__str__())

        def _get_hitobjects(self):
            return self.__hitobjects

        def get_visible_hitobjects(self, song_time):
        
            song_time = float(song_time)
            for hitobject in self._get_hitobjects():
            
                ho_start_time = hitobject.ho_time - self.ar_time
                ho_end_time = hitobject.ho_time + self.hit_time
                if not (ho_start_time <= song_time <= ho_end_time):
                    continue
                
                state_duration = self.ar_time
                if state_duration != .0:
                    state = (song_time - ho_start_time) / state_duration
                else:
                    state = 1.
                state = min(max(state, .0), 1.)
                
                is_available_for_click = False
                if hitobject.ho_time <= song_time <= ho_end_time:
                    is_available_for_click = True

                yield (hitobject, state, is_available_for_click)

        @property
        def ar_time(self):
            if self.__ar_time is None:
                ar = min(max(self.AR, .0), 12.)
                if ar <= 5.:
                    self.__ar_time = 1200. + ((600. * (5. - ar)) / 5.)
                else:
                    self.__ar_time = 1200. - ((750. * (ar - 5.)) / 5.)
                self.__ar_time *= 12.
            return self.__ar_time
        
        @property
        def hit_time(self):
            if self.__hit_time is None:
                od = min(max(self.OD, .0), 12.)
                self.__hit_time = 80. - (6. * od)
            return self.__hit_time

        @property
        def AR(self):
            """
            https://osu.ppy.sh/wiki/en/Beatmap/Approach_rate
            """
            if FORCED_AR is not None:
                return float(FORCED_AR)
            ar = self.get_parameter("Difficulty", "ApproachRate", False)
            if ar is None:
                return 5.
            return float(ar)

        @property
        def OD(self):
            """
            https://osu.ppy.sh/wiki/en/Beatmap/Overall_difficulty
            """
            if FORCED_OD is not None:
                return float(FORCED_OD)
            od = self.get_parameter("Difficulty", "OverallDifficulty", False)
            if od is None:
                return 5.
            return float(od)

            
        @property
        def background(self):
            
            if self.__background is self.NO_BACKGROUND:
                return None
            elif self.__background:
                return self.__background
            
            
            if not self.__events:
                self.__background = self.NO_BACKGROUND
                return None

            bg_filename, bg_binary = self.__events.get_background()
            if not (bg_filename and bg_binary):
                self.__background = self.NO_BACKGROUND
                return None
            
            _sha512 = hashlib.sha512(bg_binary)
            renpy_name = utils.path.renpy_join(
                "virtual_folder_for_rhythm_game",
                _sha512.hexdigest(),
                bg_filename
            )
            _back = store.im.Data(bg_binary, renpy_name)

            try:
                # loadable test
                _back.load()
            except Exception:
                self.__background = self.NO_BACKGROUND
                return None
            else:
                # Resize
                
                w, h = utils.display.get_size(_back)
                screen_width, screen_height = map(
                    float,
                    (config.screen_width, config.screen_height)
                )
                multipler = max(
                    (screen_width / w),
                    (screen_height / h)
                )
                _back = store.im.FactorScale(_back, multipler)
                
                # centered
                w, h = utils.display.get_size(_back)
                xalign = .5
                yalign = .5
                x = (w * xalign) - (screen_width * xalign)
                y = (h * yalign) - (screen_height * yalign)
                _back = store.im.Crop(
                    _back,
                    tuple(map(int, (x, y, screen_width, screen_height)))
                )

                self.__background = _back
                return self.__background
        
        @property
        def audio(self):
        
            if self.__audio:
                return self.__audio
        
            audio_name = self.get_parameter("General", "AudioFilename")
            _sha512 = hashlib.sha512(self.__audio_binary)
            renpy_name = utils.path.renpy_join(
                "virtual_folder_for_rhythm_game",
                _sha512.hexdigest(),
                audio_name
            )
            
            self.__audio = store.AudioData(self.__audio_binary, renpy_name)
            return self.__audio
            
        @property
        def mode(self):
            _mode = int(self.get_parameter("General", "Mode"))
            return self.GameModes(_mode)


        @property
        def title(self):
            for variant in ("Title", "TitleUnicode"):
                result = self.get_parameter("Metadata", variant, False)
                if result:
                    return result
            return "Unknown title"
            
        @property
        def artist(self):
            for variant in ("Artist", "ArtistUnicode"):
                result = self.get_parameter("Metadata", variant, False)
                if result:
                    return result
            return "Unknown artist"
            
        @property
        def version(self):
            result = self.get_parameter("Metadata", "Version", False)
            if result:
                return result
            return "unknownDifficulty"

        def parse_and_get_hitobjects(self):

            hit_objects = sorted(
                self.get_parameter("HitObjects"),
                key=lambda _data: float(_data[2])
            )
            
            result = []
            _group = _HitObjectsGroup()
            _number_in_group = 0
            for hitobject_data in hit_objects:
            
                _x, _y, hitobject_time, hitobject_type, *_otr = hitobject_data
                hitobject_time = float(hitobject_time)
                hitobject_type_bits = int(hitobject_type)

                if hitobject_type_bits & _HitObject.TypeFlags.Circle:
                    hitobject_type = _HitObject.TypeFlags.Circle

                elif hitobject_type_bits & _HitObject.TypeFlags.Slider:
                    hitobject_type = _HitObject.TypeFlags.Slider

                else:
                    continue

                if hitobject_type_bits & _HitObject.TypeFlags.NewCombo:
                    _group = _HitObjectsGroup()
                    _number_in_group = 0

                _number_in_group += 1
                hitobject = _HitObject(
                    hitobject_time,
                    hitobject_type,
                    group=_group,
                    number_in_group=_number_in_group,
                    raw_data=hitobject_data
                )
                result.append(hitobject)

            return tuple(result)

        def get_parameter(self, section, name=None, _raise=True):

            section = section.strip().upper()
            if name:
                name = name.strip().upper()
                
            if section not in self.__sections:
                if not _raise:
                    return None
                raise ValueError("Section \"{0}\" not found.".format(section))
                
            result = self.__sections[section]
            if isinstance(result, builtins.dict) and name:
                if name not in result:
                    if not _raise:
                        return None
                    raise ValueError("Param \"{0}\" not found.".format(name))
                result = result[name]
            
            return result

        @classmethod
        def _get_sections_from_text(cls, text):
        
            text = utils.other.get_unicode(text)

            MAPPING_SECTIONS = (
                "COLOURS",
                "DIFFICULTY",
                "EDITOR",
                "GENERAL",
                "METADATA"
            )
            LIST_SECTIONS = (
                "HITOBJECTS",
                "TIMINGPOINTS"
            )

            for section in cls.SECTION_PATTERN.finditer(text):
            
                section_name, section_raw_data = section.group(
                    "section_name",
                    "section_data"
                )

                section_name = section_name.strip().upper()
                section_data = None

                if section_name in MAPPING_SECTIONS:
                
                    section_data = {}
                    for strn in utils.other.get_strings_from_text(
                        section_raw_data
                    ):
                    
                        value = tuple(
                            map(lambda x: x.strip(), strn.split(':', 1))
                        )
                        
                        if len(value) != 2:
                            raise ValueError(
                                "Incorrect params {0} on {1} section".format(
                                    value,
                                    section_name
                                )
                            )
                            
                        key, value = value
                        key = key.strip().upper()
                        if not value:
                            value = None

                        section_data[key] = value

                elif section_name in LIST_SECTIONS:
                    
                    section_data = tuple(
                        map(
                            lambda x: tuple(
                                map(lambda y: y.strip(), x.split(','))
                            ), 
                            utils.other.get_strings_from_text(section_raw_data)
                        )
                    )

                elif section_name == "EVENTS":

                    section_data = section_raw_data

                else:
                    continue

                yield (section_name, section_data)
                

    class OSZ(_BasicInheritable):

        __author__ = "Vladya"
        
        def __init__(self, filename):
            """
            :filename:
                .osz file in Ren'Py format.
            """

            self._diffs = tuple(
                sorted(
                    self._get_diffs_from_osz(filename),
                    key=lambda _arg: (_arg.artist, _arg.title, _arg.version)
                )
            )

        def __iter__(self):
            yield from self._diffs

        @property
        def title(self):
            return ", ".join(
                sorted(frozenset(map(lambda x: x.title, self._diffs)))
            )

        @property
        def artist(self):
            return ", ".join(
                sorted(frozenset(map(lambda x: x.artist, self._diffs)))
            )

        @staticmethod
        def _get_diffs_from_osz(filename):
            filename = utils.path.renpy_normpath(filename)
            with renpy.file(filename) as _file_object:
                with zipfile.ZipFile(_file_object) as _zip:
                    for _info in _zip.infolist():
                        ext = utils.path.get_ext(_info.filename)
                        if ext == ".osu":
                            try:
                                _map_object = _OsuMap(_info, _zip)
                            except Exception as ex:
                                if DEBUG:
                                    raise ex
                            else:
                                if _map_object.mode is _OsuMap.GameModes.std:
                                    yield _map_object
