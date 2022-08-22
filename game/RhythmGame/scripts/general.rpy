
init -7 python in rhythm_game:
    


    class GameLogic(renpy.Displayable, _BasicInheritable):

        __author__ = "Vladya"
        BACK_PICTURE = store.Solid("#000")

        def __init__(self, osz_folder="", skin=None):

            super(GameLogic, self).__init__()

            osz_folder = utils.path.renpy_join(BASE_FOLDER, osz_folder)

            if skin is None:
                skin = _OsuSkin.DEFAULT_SKIN

            self._skin = _OsuSkin(skin)
            self._oszs = tuple(
                sorted(
                    self.get_osz_from_folder(osz_folder),
                    key=lambda _arg: (_arg.artist, _arg.title)
                )
            )
            self.__current_song = None
            self.__current_hitobjects = None
            self.__active_hitobject = None
            
            self.__switcher = False


        def start_game(self, disp_name="rhythmGame"):

            self.__switcher = False
            self._set_song(None)

            song = renpy.call_screen("choice_song", game_object=self)
            self._set_song(song)
            
            renpy.show(disp_name, what=self)
            
            renpy.audio.music.play(
                song.audio,
                channel=MUSIC_CHANNEL,
                loop=False
            )
            self.__switcher = True
            
            result = ui.interact()
            self.__switcher = False

            return result

        @property
        def current_song(self):
            return self.__current_song

        @property
        def accuracy(self):
            
            if not (self.__current_song and self.__current_hitobjects):
                return .0
            
            sum_list = []
            for _h, result in self.__current_hitobjects:
                if (result is True) or (result is False):
                    sum_list.append(float(result))
            
            if not sum_list:
                return .0
                
            return sum(sum_list) / len(sum_list)
            

        def _set_song(self, song):
        
            if not (isinstance(song, _OsuMap) or (song is None)):
                raise TypeError("{0!r} isn't _OsuMap object.".format(song))
            
            renpy.music.stop(MUSIC_CHANNEL)
            
            self.__current_hitobjects = None
            self.__active_hitobject = None
            self.__current_song = song
            if song:
                self.__current_hitobjects = dict.fromkeys(
                    song._get_hitobjects(),
                    None
                )

        @staticmethod
        def get_osz_from_folder(folder_name):
            for renpy_fn in utils.path.renpy_walk(folder_name, True):
                if utils.path.get_ext(renpy_fn) == ".osz":
                    yield OSZ(renpy_fn)
            
        def visit(self):

            _result = [self.BACK_PICTURE]
            _result.extend(self._skin._visit_disp())
            for _osz in self._oszs:
                for diff in _osz:
                    if diff.background:
                        _result.append(diff.background)

            result = []
            for disp in _result:
                if disp in result:
                    continue
                result.append(disp)

            return result
            
        def render(self, *rend_args):
            
            width, height, st, at = rend_args
            result_render = renpy.Render(
                *map(int, (config.screen_width, config.screen_height))
            )
            
            rend = renpy.render(self.BACK_PICTURE, *rend_args)
            result_render.blit(rend, (0, 0))

            # Draw BG.
            if self.__current_song and self.__current_song.background:
                back = store.im.Alpha(self.__current_song.background, alpha=.1)
                rend = renpy.render(back, *rend_args)
                result_render.blit(rend, (0, 0))
        
            if self.__switcher and self.__current_song:
            
                song_pos = renpy.music.get_pos(channel=MUSIC_CHANNEL)
                
                if song_pos is not None:

                    song_pos *= 1e3  # Seconds to ms.
                    song_pos += GLOBAL_OFFSET
                    
                    if self.__active_hitobject:
                        if self.__active_hitobject.ho_time < song_pos:
                            pass #todo
                        
                    _gen = self.__current_song.get_visible_hitobjects(song_pos)
                    for ho, state, is_available_for_click in _gen:

                        if self.__current_hitobjects[ho] is not None:
                            continue
                            
                        state = utils.other.warp_value(
                            state,
                            "easeout_expo"
                        )
                        hitcircle_rend = self._skin.get_hitcircle_render(
                            state,
                            is_available_for_click,
                            ho.number,
                            *rend_args
                        )

                        hc_w, hc_h = hitcircle_rend.get_size()
                        xalign, yalign = ho._calculate_align(
                            utils.other.warp_value(state, "easein"),
                            utils.other.warp_value(state, "easeout_quad")
                        )

                        x = (config.screen_width * xalign) - (hc_w * xalign)
                        y = (config.screen_height * yalign) - (hc_h * yalign)
                        x, y = map(int, (x, y))

                        result_render.blit(hitcircle_rend, (x, y))

            renpy.redraw(self, .0)
            return result_render


    _game = GameLogic("songMaps")
    
    
    #  https://osu.ppy.sh/wiki/ru/Client/File_formats/Osu_%28file_format%29#hit-objects
    

screen choice_song(game_object):
    
    modal True
    default hover_picture = None
    
    if hover_picture:
        add hover_picture:
            align (.5, .5)

    viewport:
        scrollbars "vertical"
        style_prefix "choice"
        draggable True
        mousewheel True
        vbox:
            xfill True
            for _osz in game_object._oszs:
                hbox:
                    xalign .5
                    label _osz.artist
                    null width 50
                    label _osz.title
                null height 15
                for _diff in _osz:
                    textbutton "{0.title} ({0.artist}) <{0.version}>".format(_diff):
                        xalign .5
                        hovered SetScreenVariable("hover_picture", _diff.background)
                        action Return(_diff)
                null height 20

