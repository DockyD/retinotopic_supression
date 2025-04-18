from exptools2.core import Trial
from psychopy.visual import TextStim,ImageStim
import numpy as np
from psychopy import core
import os.path as op


class InstructionTrial(Trial):

    def __init__(self, session, trial_nr, txt, bottom_txt=None, image_path=None, keys=None, phase_durations=None, 
                 phase_names=None, **kwargs):

        self.keys = keys

        if phase_durations is None:
            phase_durations = [.5, np.inf]

        if phase_names is None:
            phase_names = ['instruction'] * len(phase_durations)

        super().__init__(session, trial_nr, phase_durations=phase_durations, phase_names=phase_names, **kwargs)

        txt_height = self.session.settings['various'].get('text_height')
        txt_width = self.session.settings['various'].get('text_width')
        txt_color = self.session.settings['various'].get('text_color')

        if image_path:
            self.text = TextStim(session.win, txt,
                                pos=(-6.0, 0.0), height=txt_height, wrapWidth=txt_width, color=txt_color)
        else:
            self.text = TextStim(session.win, txt,
                                pos=(0.0, 0.0), height=txt_height, wrapWidth=txt_width, color=txt_color)

        print(self.text)
        print(txt)

        if bottom_txt is None:
            bottom_txt = "Press any button to continue"

        self.text2 = TextStim(session.win, bottom_txt, pos=(
            0.0, -6.0), height=txt_height, wrapWidth=txt_width,
            color=txt_color)
        
        self.image = None
        print(f"Trying to load image: {image_path}")
        if image_path:
            print("Exists?", op.exists(image_path))
        else:
            print("No image provided.")
        
        if image_path is not None and op.exists(image_path):
            self.image = ImageStim(
                session.win,
                image=image_path,
                pos=(6, 0),  
                size=(10,10),  
                units='deg'
            )

    def get_events(self):

        events = Trial.get_events(self)

        if self.keys is None:
            if events:
                self.stop_phase()
        else:
            for key, t in events:
                if key in self.keys:
                    self.stop_phase()

    def draw(self):
        if self.image:
            self.image.draw()
        self.text.draw()
        self.text2.draw()



class SingletonTrial(Trial):

    def __init__(self, session, trial_nr, iti,
                distractor_location=None,
                target_location=None,
                distractor_color=None,
                target_orientation=None,
                dot_presence=None,
                most_likely_distractor_location=1,
                  **kwargs):


        trial_start_duration = session.settings['durations'].get('trial_start', 1)
        cue_duration = session.settings['durations'].get('cue', 1)
        target_duration = session.settings['durations'].get('target', 1)
        feedback_duration = session.settings['durations'].get('feedback', 1)


        phase_durations = [trial_start_duration, cue_duration, target_duration, feedback_duration, iti]
        phase_names = ['trial_start', 'pre-target', 'target', 'feedback', 'iti']

        super().__init__(session, trial_nr, phase_durations=phase_durations, phase_names=phase_names, **kwargs) 

        self.parameters['distractor_color'] = np.random.choice(['red', 'green']) if distractor_color is None else distractor_color
        self.parameters['target_orientation'] = np.random.choice([0.0, 90]) if target_orientation is None else target_orientation

        if distractor_location is None:
            locations = range(1, 8, 2)
            most_likely_distractor_p = self.session.settings['design'].get('most_likely_distractor_p', 0.66)
            probabilities = [(1 - most_likely_distractor_p)/3] * 4
            probabilities[locations.index(most_likely_distractor_location)] = most_likely_distractor_p
            self.parameters['distractor_location'] = np.random.choice(locations, p=probabilities)
        else:
            self.parameters['distractor_location'] = distractor_location

        if dot_presence is None:
            #to ensure always and only 2 dots on the possible target locations
            dot_presence = [False] * 8  
            for i in np.random.choice([0, 2, 4, 6], 2, replace=False):
                dot_presence[i] = True
            for i in np.random.choice([1, 3, 5, 7], 2, replace=False):
                dot_presence[i] = True
            self.parameters['dot_presence'] = dot_presence

            # self.parameters['dot_presence'] = ([True] * 4) + ([False] * 4)
            # np.random.shuffle(self.parameters['dot_presence'])
        else:
            self.parameters['dot_presence'] = dot_presence

        if target_location is None:
            self.parameters['target_location'] = np.random.choice([i for i in range(1, 8, 2) if i != self.parameters['distractor_location']])
        else:
            self.parameters['target_location'] = target_location

        self.parameters['correct'] = np.nan
        self.responded = False

        #for the dot version
        # print(self.parameters['dot_presence'])
        # print(self.parameters['target_location'])
        self.parameters['correct_response'] = self.parameters['dot_presence'][self.parameters['target_location']]

        # for present/absent version
        # if self.parameters['target_location'] < 9:
        #     self.parameters['correct_response'] = True
        # else:
        #     self.parameters['correct_response'] = False

        self.stimulus_onset = None

    
    def draw(self):

        # #if cue that search is about to start
        # if self.phase == 0:
        #     self.session.fixation_dot.color = 'blue'
        # elif self.phase == 1:
        #     self.session.fixation_dot.color = 'white'

        self.session.fixation_dot.color = 'white'

        if self.phase == 2:
            if self.stimulus_onset is None:
                self.stimulus_onset = self.session.clock.getTime()

            self.session.target_stimuli.draw()

        self.session.sweeping_bars.draw()

        if self.phase == 3:
            if (not self.responded) or (not self.parameters['correct']):
                self.session.error_stimulus.draw()
            else:
                if self.session.settings['experiment'].get('show_correct_feedback', False):
                    self.session.correct_stimulus.draw()
                else:
                    self.session.fixation_dot.draw()
        else:
            self.session.fixation_dot.draw()

    def run(self):
        self.setup_trial_stimuli()
        super().run()
    
    def setup_trial_stimuli(self):
        self.session.target_stimuli.setup(self.parameters['distractor_color'], self.parameters['target_orientation'],
                                          self.parameters['distractor_location'], self.parameters['target_location'],
                                          self.parameters['dot_presence'])

    def get_events(self):
        events = super().get_events()
        keys = self.session.settings['experiment']['keys']

        if self.phase == 2:
            for key, t in events:
                if (not self.responded) and (key in self.session.settings['experiment']['keys']):
                    self.parameters['response'] = key
                    self.parameters['rt'] = t - self.stimulus_onset
                    self.parameters['correct'] = bool(keys.index(self.parameters['response'])) == self.parameters['correct_response']
                    self.responded = True


class SingletonTrial_training(SingletonTrial):
    def __init__(self, session, trial_nr, iti,
                distractor_location=None,
                target_location=None,
                distractor_color=None,
                target_orientation=None,
                dot_presence=None,
                most_likely_distractor_location=1,
                  **kwargs):

        super().__init__(session, trial_nr, iti, distractor_location=distractor_location,
                         target_location=target_location, distractor_color=distractor_color,
                         target_orientation=target_orientation, dot_presence=dot_presence,
                         most_likely_distractor_location=most_likely_distractor_location, **kwargs)
        self.audio_played = False
   
    def draw(self):

        if self.phase == 0:
            self.session.fixation_dot.color = 'white'
        elif self.phase == 1:
            self.session.fixation_dot.color = 'white'

        if self.phase == 2:
            if self.stimulus_onset is None:
                self.stimulus_onset = core.getTime()

            self.session.target_stimuli.draw()
            
            if self.session.eyetracker_on and self.session.settings["various"]["eyemovements_alert"]:
                el_smp = self.session.tracker.getNewestSample()
                if el_smp != None:
                    if el_smp.isLeftSample():
                        sample = np.array(el_smp.getLeftEye().getGaze())
                    elif el_smp.isRightSample():
                        sample = np.array(el_smp.getRightEye().getGaze())
                    fix_dist_pix = np.linalg.norm(
                        (np.array(self.session.win.size) / 2) -
                        np.array(sample)
                    )
                    fix_dist_deg = fix_dist_pix / self.session.pix_per_deg
                    print(f"played: {self.audio_played}, fix_dist_deg: {fix_dist_deg}, fix_dist_pix: {fix_dist_pix}, pix_per_deg: {self.session.pix_per_deg}")
                    if (
                        fix_dist_deg
                        > self.session.settings["various"]["gaze_threshold_deg"]
                    ):
                        if not self.audio_played:
                            self.session.beep.play()
                            core.wait(0.03)
                            self.session.beep.stop()
                            # playsound(self.session.soundfile)
                            self.audio_played = True
                            self.session.beep_count += 1

        self.session.sweeping_bars.draw()

        if self.phase == 3:
            if (not self.responded) or (not self.parameters['correct']):
                self.session.error_stimulus.draw()
            else:
                if self.session.settings['experiment'].get('show_correct_feedback', False):
                    self.session.correct_stimulus.draw()
                else:
                    self.session.fixation_dot.draw()
        else:
            self.session.fixation_dot.draw()


class BlankTrial(Trial):

    def __init__(self, session, trial_nr,
                  **kwargs):


        blank_duration = session.settings['durations'].get('blank', 1)
        phase_durations = [blank_duration]
        phase_names = ['blank']

        super().__init__(session, trial_nr, phase_durations=phase_durations, phase_names=phase_names, **kwargs)

        self.parameters['correct'] = np.nan
        self.responded = False
        self.stimulus_onset = None

    
    def draw(self):
        self.session.backgroundcircle.draw()
        self.session.fixation_dot.color = 'white'
        self.session.fixation_dot.draw()

    def run(self):
        super().run()
