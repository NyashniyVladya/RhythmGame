
init -9 python in rhythm_game:

    class _AudioUtils(_BasicInheritable):

        __author__ = "Vladya"
        _channel_switch_lock = threading.Lock()

        def __init__(self):
            self.__sfx_channels = tuple(self._create_and_get_sfx_channels())
            self.__active_channel = self.__sfx_channels[0]

        @staticmethod
        def _create_and_get_sfx_channels(amount=30):

            if not renpy.game.context().init_phase:
                raise RuntimeError("Works only during initialization.")
        
            template = "rhythm_game_sfx_{0:0>3}"
            channels_get = 0
            _counter = 0

            while True:

                if channels_get >= amount:
                    break

                _counter += 1
                channel_name = template.format(_counter)
                if channel_name in renpy.audio.audio.channels:
                    continue
                    
                renpy.music.register_channel(channel_name, mixer="sfx")
                yield channel_name
                channels_get += 1

        def play_sfx(self, _audio):

            with self._channel_switch_lock:

                renpy.audio.music.play(
                    _audio,
                    channel=self.__active_channel,
                    loop=False
                )
                
                last_index = self.__sfx_channels.index(self.__active_channel)
                new_index = (last_index + 1) % len(self.__sfx_channels)
                self.__active_channel = self.__sfx_channels[new_index]
            
    class _RenderUtils(_BasicInheritable):

        __author__ = "Vladya"
        
        @classmethod
        def zoom_render(cls, render_object, xzoom, yzoom=None):
        
            if yzoom is None:
                yzoom = xzoom
        
            xzoom = float(xzoom)
            yzoom = float(yzoom)
            render_object = cls.copy_render(render_object)
            
            new_width = render_object.width * xzoom
            new_height = render_object.height * yzoom
            new_width, new_height = map(int, (new_width, new_height))

            render_object.zoom(xzoom, yzoom)
            render_object = render_object.subsurface(
                (0, 0, new_width, new_height)
            )
                
            result = renpy.Render(new_width, new_height)
            result.blit(render_object, (0, 0))
            return result

        @staticmethod
        def copy_render(render_object):
            
            width, height = map(int, render_object.get_size())
            copy_render = render_object.subsurface((0, 0, width, height))
            
            result = renpy.Render(width, height)
            result.blit(copy_render, (0, 0))
            return result

    class _DisplayUtils(_BasicInheritable):

        __author__ = "Vladya"

        @staticmethod
        def get_displayable(data):
            result = renpy.displayable(data)
            if not isinstance(result, renpy.display.core.Displayable):
                raise ValueError("Incorrect data {0!r}.".format(data))
            return result

        @classmethod
        def get_imagebase(cls, data):
            result = cls.get_displayable(data)
            if not isinstance(result, renpy.display.im.ImageBase):
                raise ValueError("Not ImageBase displayable.")
            return result

        @classmethod
        def get_size(cls, data):

            if renpy.game.context().init_phase:
                _msg = "It doesn't work on init phase, 'cause render is used."
                raise RuntimeError(_msg)

            disp = cls.get_displayable(data)
            if isinstance(disp, renpy.display.im.ImageBase):
                surface = renpy.load_surface(disp)
            else:
                surface = renpy.render(disp, 0, 0, 0, 0)

            return tuple(map(float, surface.get_size()))

    class _PathUtils(_BasicInheritable):
    
        __author__ = "Vladya"
        
        
        @classmethod
        def renpy_walk(cls, root_dir, _common=False):

            root_dir = path.normpath(_OtherUtils.get_unicode(root_dir))
            if root_dir.strip() == '.':
                root_dir = ""

            for renpy_fn in renpy.list_files(_common):
                fn = path.normpath(renpy_fn)
                directory = path.dirname(fn)
                while True:

                    if directory == root_dir:
                        yield renpy_fn
                        break

                    if not directory:
                        break
                    
                    directory = path.dirname(directory)

        @staticmethod
        def get_ext(fn):
            fn = _OtherUtils.get_unicode(fn)
            _fn, ext = path.splitext(path.normpath(fn))
            return ext.strip().lower()
        
        @staticmethod
        def renpy_normpath(fn):
            fn = _OtherUtils.get_unicode(fn)
            fn = path.normpath(fn)
            if fn.strip() == '.':
                fn = ""
            return fn.replace('\\', '/')
            
        @classmethod
        def renpy_join(cls, *parts):
            return cls.renpy_normpath(
                path.join(
                    *map(path.normpath, map(_OtherUtils.get_unicode, parts))
                )
            )


    class _OtherUtils(_BasicInheritable):
        
        __author__ = "Vladya"
        
        @staticmethod
        def string_assert(data):
            if not isinstance(data, (str, bytes)):
                raise TypeError("{0!r} isn't a string.".format(data))

        @classmethod
        def get_unicode(cls, text, errors=None):
            cls.string_assert(text)
            if isinstance(text, bytes):
                if errors:
                    text = text.decode("utf_8", errors)
                else:
                    text = text.decode("utf_8")
            return text

        @classmethod
        def get_strings_from_text(cls, text):
            text = cls.get_unicode(text)
            for _string in re.split(r"[\r\n]+", text):
                _string = _string.strip()
                if _string:
                    yield _string

        @staticmethod
        def warp_value(value, warper="linear"):
        
            value = min(max(float(value), .0), 1.)
            if isinstance(warper, (str, bytes)):
                warper = renpy.atl.warpers[warper]
                
            if not callable(warper):
                raise TypeError("Incorrect warper {0!r}.".format(warper))

            return warper(value)
    
        @staticmethod
        def random_exclude(*exclude_areas):
            while True:
                result = random.random()
                for _area in exclude_areas:
                    ignore_start, ignore_end = map(float, _area)
                    if ignore_start <= result <= ignore_end:
                        break
                else:
                    return result


    class _GeneralUtils(_BasicInheritable):

        __author__ = "Vladya"

        def __init__(self):
            self.__audio_utils = _AudioUtils()
            self.__display_utils = _DisplayUtils()
            self.__render_utils = _RenderUtils()
            self.__path_utils = _PathUtils()
            self.__other_utils = _OtherUtils()

        @property
        def audio(self):
            return self.__audio_utils
        
        @property
        def display(self):
            return self.__display_utils

        @property
        def render(self):
            return self.__render_utils

        @property
        def path(self):
            return self.__path_utils

        @property
        def other(self):
            return self.__other_utils


    utils = _GeneralUtils()
