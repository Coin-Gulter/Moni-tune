import pyautogui
import numpy as np
import screen_brightness_control as sbc
import keyboard
import time
import os
import pickle
import json
from sklearn import linear_model
from windows_toasts import InteractableWindowsToaster, ToastText1, ToastInputTextBox, ToastButton


get_avg_screen_color = lambda: np.array(pyautogui.screenshot()).mean()

class monitor_bright_control():
    def __init__(self):
        self.program_work = True
        self.program_paused = False

        self.training_avg_color_db = np.array([[100.]])
        self.training_screen_bright_db = np.array([50.])

        self.last_bright = sbc.get_brightness()
        self.last_avg_color = get_avg_screen_color()

        if os.path.isfile('app_setting.json'):
            with open('app_setting.json', 'r', encoding='utf-8') as outfile:
                self.setting = json.load(outfile)
        else:
            self.setting = {"max_screen_object":30, "avg_color_diviation":15}
            with open("app_setting.json", "w", encoding="utf-8") as infile:
                json.dump(self.setting, infile)

        if os.path.isfile('bright_recog_reg_model.pkl'):
            self.img_reg_model = pickle.load(open("bright_recog_reg_model.pkl", "rb"))
            self.trained = True
        else:
            self.img_reg_model = linear_model.LinearRegression()
            self.trained = False

        self.interacteble_toaster = InteractableWindowsToaster('Moni-tune')
        self.toast_notification = ToastText1()
        self.toast_input_box = ToastText1()
        self.toast_input_box.SetBody(f"Your setting now:\nSaved screens: {self.setting['max_screen_object']}\nDiviation: {self.setting['avg_color_diviation']}")
        self.toast_input_box.AddInput(ToastInputTextBox('max_screen_object', 'Saved screen from 5 to 200:', 'only number'))
        self.toast_input_box.AddInput(ToastInputTextBox('avg_color_diviation', 'Diviation value from 5 to 200:', 'only number'))
        self.toast_input_box.AddAction(ToastButton('submit', 'submit'))
        self.toast_input_box.on_activated = self.accept_new_setting
        self.show_notification = False
        self.notification_setting = False
        self.notification_text = ''

        keyboard.add_hotkey('ctrl+alt+c', self.pause_program)
        keyboard.add_hotkey('ctrl+alt+v', self.alive_program)
        keyboard.add_hotkey('ctrl+alt+x', self.close_program)
        keyboard.add_hotkey('ctrl+alt+z', self.additional_setting)
        

    def insert_in_db(self, current_avg_screen_color, current_bright):

        if len(self.training_screen_bright_db) == self.setting["max_screen_object"]:
            self.training_avg_color_db = np.delete(self.training_avg_color_db, 0, 0)
            self.training_screen_bright_db = np.delete(self.training_screen_bright_db, 0)

        avg_color_array = np.array([[current_avg_screen_color]])
        self.training_avg_color_db = np.concatenate((self.training_avg_color_db, avg_color_array), axis=0)

        screen_bright_array = np.array(current_bright)
        self.training_screen_bright_db = np.concatenate((self.training_screen_bright_db, screen_bright_array))

    def start_program(self):

        self.notification_text = 'Moni-tune working'
        self.set_notification()

        while self.program_work:
            time.sleep(0.5)
            if not self.program_paused:

                current_bright = sbc.get_brightness()
                current_avg_screen_color = get_avg_screen_color()

                if self.last_bright != current_bright or self.trained==False:

                    print('train')
                    self.insert_in_db(current_avg_screen_color, current_bright)

                    self.img_reg_model.fit(self.training_avg_color_db, self.training_screen_bright_db)

                    self.last_bright = current_bright
                    self.last_avg_color = current_avg_screen_color
                    self.time_now = time.time()
                    self.trained = True

                    pickle.dump(self.img_reg_model, open("bright_recog_reg_model.pkl", "wb"))

                elif abs(current_avg_screen_color-self.last_avg_color) > self.setting["avg_color_diviation"]:

                    print('predict')
                    predict_avg_screen_array = np.array([current_avg_screen_color]).reshape((1,1))

                    new_bright = int(self.img_reg_model.predict(predict_avg_screen_array))
                    print('curret bright=', self.last_bright, 'predicted bright=', [new_bright])

                    sbc.set_brightness(new_bright)

                    self.last_bright = [new_bright]
                    self.last_avg_color = current_avg_screen_color
                    self.time_now = time.time()

            if self.show_notification:
                if self.notification_setting:
                    self.toast_input_box.SetBody(f"Your setting now:\nSaved screens: {self.setting['max_screen_object']}\nDiviation: {self.setting['avg_color_diviation']}")
                    self.interacteble_toaster.show_toast(self.toast_input_box)
                    self.notification_setting = False
                else:
                    self.toast_notification.SetBody(self.notification_text)
                    self.interacteble_toaster.show_toast(self.toast_notification)

                self.show_notification = False

    def set_notification(self):
        self.show_notification = True

    def additional_setting(self):
        self.notification_setting = True
        self.show_notification = True

    def accept_new_setting(self, activatedEventArgs):
        temp_setting = activatedEventArgs.inputs
        for key in temp_setting:
            value = temp_setting[key]
            if value.isdigit():
                value_num = int(value)
                if value_num<=200 and value_num>=5 :
                    self.setting[key] = value_num

        with open("app_setting.json", "w", encoding="utf-8") as infile:
            json.dump(self.setting, infile)

    def close_program(self):
        self.program_work = False
        self.notification_text = 'Moni-tune closed'
        self.set_notification()

    def pause_program(self):
        if self.program_paused:
            print('Program already paused')
            self.notification_text = 'Moni-tune already paused'
            self.set_notification()

        else:
            print('Program paused...')
            self.program_paused = True
            self.notification_text = 'Moni-tune paused...'
            self.set_notification()
    
    def alive_program(self):
        if not self.program_paused:
            print('Program already alive')
            self.notification_text = 'Moni-tune already unpaused'
            self.set_notification()

        else:
            print('Program now ALIIIIIIVE!!!')
            self.program_paused = False
            self.notification_text = 'Moni-tune now ALIVE!!!'
            self.set_notification()


if __name__ == "__main__":
    monitorchik = monitor_bright_control()
    monitorchik.start_program()
