# application for task 3

from keras.models import load_model
import joblib
import pyglet
from pyglet.window import mouse
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
FONT_SIZE = 64

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
        self.label = pyglet.text.Label(
            '', font_name='Arial', font_size=24,
            x=self.width//2, y=30, anchor_x='center'
        )
        self.current_x = 0
        self.current_y = 0

    def on_draw(self):
        self.clear()
        if self.view_points:
            for stroke_point in self.view_points:
                c = pyglet.shapes.Circle(stroke_point[0], stroke_point[1], BRUSH_WIDTH)
                c.draw()
        self.label.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.label.text = ''
            self.drawing = True
            self.view_points = [(x, y)]
            self.stroke_points = [[x, WINDOW_HEIGHT - y]]
            self.current_x = x
            self.current_y = y
            pyglet.clock.schedule_interval(self.add_point, DRAW_TIME_INTERVAL)  # Add points for view
            pyglet.clock.schedule_interval(self.add_stroke_point, STORE_TIME_INTERVAL)  # Add points for storing

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.drawing:
            self.current_x = x
            self.current_y = y

    def get_stroke(self, points): #preprocessing data
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
            self.label.text = encoder.inverse_transform(np.array([prediction]))[0]

    def add_point(self, dt):
        if self.drawing and (self.view_points[-1] != (self.current_x, self.current_y)):
            self.view_points.append((self.current_x, self.current_y))

    def add_stroke_point(self, dt):
        #pyglet has origin on the left down, not left up! therefore flip y for stroke points
        self.stroke_points.append([self.current_x, WINDOW_HEIGHT - self.current_y])

# Run the application
if __name__ == '__main__':
    window = DrawWindow()
    pyglet.app.run()

