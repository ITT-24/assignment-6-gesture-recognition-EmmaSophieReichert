# application for task 3

from keras.models import load_model
import joblib
import pyglet
from pyglet.window import mouse, key
from pyglet.gl import glClearColor
import time
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.signal import resample
import random

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400
BRUSH_WIDTH = 10
DRAW_TIME_INTERVAL = 0.0001
STORE_TIME_INTERVAL = 0.05
NUM_POINTS = 50 #must be same as with training model
FONT_SIZE = 100
LETTERS = ['A', 'E', 'I', 'O', 'U']

model= load_model("models/letters.keras")
encoder = joblib.load('label_encoder_letters.pkl')
label_classes = encoder.classes_

#form gesture-input, and modified
class DrawWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Draw Stroke")
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.view_points = []
        self.stroke_points = []
        self.drawing = False
        self.points = 0
        self.predictions_made = 0
        self.correct_predictions = 0
        self.result_screen = False

        self.random_letter = random.choice(LETTERS)
        # self.letter_label = pyglet.text.Label(
        #     self.random_letter, font_name='Brush Script MT', font_size=FONT_SIZE,
        #     x=WINDOW_WIDTH // 4, y=WINDOW_HEIGHT // 2, anchor_x='center', anchor_y='center'
        # )
        self.letter_label = pyglet.text.Label(
            self.random_letter, font_name='Comic Sans MS', font_size=FONT_SIZE,
            x=WINDOW_WIDTH // 4, y=((WINDOW_HEIGHT-50) // 2) + 50, anchor_x='center', anchor_y='center'
        )

        self.status_bar = []
        self.prediction_status = pyglet.text.Label(
            '', font_name='Arial', font_size=24,
            x=WINDOW_WIDTH // 2, y=30, anchor_x='center'
        )

        self.result_label = pyglet.text.Label(
            '', font_name='Arial', font_size=24,
            x=self.width // 2, y=self.height // 2, anchor_x='center'
        )
        
        self.restart_label = pyglet.text.Label(
            'Press R to play again', font_name='Arial', font_size=24,
            x=self.width // 2, y=self.height // 2 - 50, anchor_x='center'
        )

    def clear(self): #set background color
        glClearColor(30 / 255.0, 77 / 255.0, 43 / 255.0, 1)
        super().clear()

    def on_draw(self):
        self.clear()
        
        if self.result_screen:
            self.result_label.draw()
            self.restart_label.draw()
            return

        self.letter_label.draw()

        # if self.view_points: #use points
        #     for stroke_point in self.view_points:
        #         c = pyglet.shapes.Circle(stroke_point[0], stroke_point[1], BRUSH_WIDTH)
        #         c.draw()

        if self.view_points: #use lines
            for i in range(len(self.view_points) - 1):
                line = pyglet.shapes.Line(self.view_points[i][0], self.view_points[i][1], 
                                          self.view_points[i + 1][0], self.view_points[i + 1][1], 
                                          width=BRUSH_WIDTH, color=(255, 255, 255))
                line.draw()

        self.prediction_status.draw()

        # Draw status bar
        for i, color in enumerate(self.status_bar):
            rect = pyglet.shapes.Rectangle(50 + i * 70, 10, 50, 20, color=color)
            rect.draw()

        # Draw separator line
        pyglet.shapes.Line(WINDOW_WIDTH // 2, 50, WINDOW_WIDTH // 2, WINDOW_HEIGHT, width=2, color=(255, 255, 255)).draw()
        pyglet.shapes.Line(0, 50, WINDOW_WIDTH, 50, width=2, color=(255, 255, 255)).draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT and x > WINDOW_WIDTH // 2 and y >= 50 and not self.result_screen:
            self.prediction_status.text = ''
            self.drawing = True
            self.view_points = [(x, y)]
            self.stroke_points = [[x - WINDOW_WIDTH // 2, WINDOW_HEIGHT - y]]
            self.current_x = x
            self.current_y = y
            pyglet.clock.schedule_interval(self.add_point, DRAW_TIME_INTERVAL)  # Add points for view
            pyglet.clock.schedule_interval(self.add_stroke_point, STORE_TIME_INTERVAL)  # Add points for storing

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.drawing and x > WINDOW_WIDTH // 2:
            self.current_x = x
            self.current_y = y

    def get_stroke(self, points):  # preprocessing data
        points = np.array(points, dtype=float)
        scaler = StandardScaler()
        points = scaler.fit_transform(points)
        resampled = resample(points, NUM_POINTS)
        return np.array(resampled)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT and self.drawing:
            self.drawing = False
            pyglet.clock.unschedule(self.add_point)
            pyglet.clock.unschedule(self.add_stroke_point)

            stroke = self.get_stroke(self.stroke_points)

            prediction = model.predict(np.array([stroke]))
            prediction = np.argmax(prediction)
            predicted_letter = encoder.inverse_transform(np.array([prediction]))[0]

            if predicted_letter == self.random_letter:
                self.status_bar.append((0, 255, 0))  # Green
                self.correct_predictions += 1
            else:
                self.status_bar.append((255, 0, 0))  # Red

            self.predictions_made += 1
            if self.predictions_made < 10:
                self.random_letter = random.choice(LETTERS)
                self.letter_label.text = self.random_letter
            else:
                self.result_screen = True
                self.result_label.text = f"{self.correct_predictions} correct"

    def add_point(self, dt):
        if self.drawing and (self.view_points[-1] != (self.current_x, self.current_y)):
            self.view_points.append((self.current_x, self.current_y))

    def add_stroke_point(self, dt):
        # Pyglet has origin on the left down, not left up! therefore flip y for stroke points
        self.stroke_points.append([self.current_x - WINDOW_WIDTH // 2, WINDOW_HEIGHT - self.current_y])

    def on_key_press(self, symbol, modifiers):
        if self.result_screen and symbol == key.R:
            self.reset_game()

    def reset_game(self):
        self.clear()
        self.result_screen = False
        self.predictions_made = 0
        self.correct_predictions = 0
        self.status_bar = []
        self.view_points = []
        self.random_letter = random.choice(LETTERS)
        self.letter_label.text = self.random_letter

# Run the application
if __name__ == '__main__':
    window = DrawWindow()
    pyglet.app.run()

