import pyautogui
import numpy as np
import screen_brightness_control as sbc
import keyboard
import time
from sklearn import linear_model
from windows_toasts import InteractableWindowsToaster, ToastText1


get_avg_screen_color = lambda: np.array(pyautogui.screenshot()).mean()

class monitor_bright_control():
    def __init__(self):
        self.trained = False
        self.program_work = True
        self.program_paused = False

        self.max_trainig_objects = 15
        self.training_avg_color_db = np.array([[55.]])
        self.training_screen_bright_db = np.array([40.])

        self.last_bright = sbc.get_brightness()
        self.last_avg_color = get_avg_screen_color()
        self.img_reg_model = linear_model.LinearRegression()

        self.avg_color_diviation = 15

        self.interacteble_toaster = InteractableWindowsToaster('Moni-tune')
        self.toast_notification = ToastText1()
        self.show_notification = False
        self.notification_text = ''

        keyboard.add_hotkey('ctrl+alt+c', self.pause_program)
        keyboard.add_hotkey('ctrl+alt+v', self.alive_program)
        keyboard.add_hotkey('ctrl+alt+x', self.close_program)

    def insert_in_db(self, current_avg_screen_color, current_bright):

        if len(self.training_screen_bright_db) == self.max_trainig_objects:
            self.training_avg_color_db = np.delete(self.training_avg_color_db, 0, 0)
            self.training_screen_bright_db = np.delete(self.training_screen_bright_db, 0)

        avg_color_array = np.array([[current_avg_screen_color]])
        self.training_avg_color_db = np.concatenate((self.training_avg_color_db, avg_color_array), axis=0)

        screen_bright_array = np.array(current_bright)
        self.training_screen_bright_db = np.concatenate((self.training_screen_bright_db, screen_bright_array))

    def start_program(self):

        self.set_notification('Moni-tune working')

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

                elif abs(current_avg_screen_color-self.last_avg_color) > self.avg_color_diviation:

                    print('predict')
                    predict_avg_screen_array = np.array([current_avg_screen_color]).reshape((1,1))

                    new_bright = int(self.img_reg_model.predict(predict_avg_screen_array))
                    print('curret bright=', self.last_bright, 'predicted bright=', [new_bright])

                    sbc.set_brightness(new_bright)

                    self.last_bright = [new_bright]
                    self.last_avg_color = current_avg_screen_color
                    self.time_now = time.time()

            if self.show_notification:
                self.toast_notification.SetBody(self.notification_text)
                self.interacteble_toaster.show_toast(self.toast_notification)

                self.show_notification = False

    def set_notification(self, text):
        self.show_notification = True
        self.notification_text = text

    def close_program(self):
        self.program_work = False
        self.set_notification('Moni-tune closed')

    def pause_program(self):
        if self.program_paused:
            print('Program already paused')
            self.set_notification('Moni-tune already paused')

        else:
            print('Program paused...')
            self.program_paused = True
            self.set_notification('Moni-tune paused...')
    
    def alive_program(self):
        if not self.program_paused:
            print('Program already alive')
            self.set_notification('Moni-tune already unpaused')

        else:
            print('Program now ALIIIIIIVE!!!')
            self.program_paused = False
            self.set_notification('Moni-tune now ALIVE!!!')


if __name__ == "__main__":
    monitorchik = monitor_bright_control()
    monitorchik.start_program()
