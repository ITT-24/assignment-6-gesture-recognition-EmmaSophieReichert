# gesture input program for first task

import recognizer
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import pyglet
from pyglet.window import mouse
import time
import sys

WINDOW_SIZE = 600
BRUSH_WIDTH = 10
DRAW_TIME_INTERVAL = 0.0001
STORE_TIME_INTERVAL = 0.05
FOLDER_PATH = 'dataset/my-dataset'

type = "stroke"

if len(sys.argv) > 1:
    type = str(sys.argv[1])
    print("T", type)

#Helper class for storing
class Stroke:
    def __init__(self, name, points, number, milliseconds):
        self.name = name
        self.points = points

        self.subject = 0
        self.speed = "medium"
        self.number = number
        self.num_pts = len(self.points)
        self.milliseconds = milliseconds
        self.app_name = "emmas_app"
        self.app_ver = "1.0"
        now = datetime.now()
        self.date = now.strftime("%A, %B %d, %Y")
        self.time_of_day = now.strftime("%I:%M:%S %p")

    def save_XML(self, folder=FOLDER_PATH):
        gesture = ET.Element(
            "Gesture",
            Name=self.name,
            Subject=str(self.subject),
            Speed=self.speed,
            Number=str(self.number),
            NumPts=str(self.num_pts),
            Millseconds=str(self.milliseconds) if self.milliseconds else "0",
            AppName=self.app_name,
            AppVer=self.app_ver,
            Date=self.date,
            TimeOfDay=self.time_of_day
        )
        for point in self.points:
            point_elem = ET.SubElement(
                gesture, "Point",
                X=str(point.x),
                Y=str(point.y),
                T=str(point.t)
            )
        tree = ET.ElementTree(gesture)
        if not os.path.exists(folder):
            os.makedirs(folder)
        xml_file_path = os.path.join(folder, f"{self.name}.xml")
        with open(xml_file_path, 'wb') as xml_file:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        print(f"XML saved to {xml_file_path}")

# Pyglet application, generated with GPT and modified
class DrawWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(WINDOW_SIZE, WINDOW_SIZE, "Draw Stroke")
        self.set_minimum_size(WINDOW_SIZE, WINDOW_SIZE)
        self.dollar_recognizer = recognizer.DollarRecognizer()
        self.view_points = []
        self.stroke_points = []
        self.drawing = False
        self.start_time = 0
        self.strokes = []
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
            print("LEFT MOUSE")
            self.label.text = ''
            self.drawing = True
            self.start_time = time.time()
            self.view_points = [(x, y)]
            self.stroke_points = [(x, WINDOW_SIZE - y, self.start_time)]
            self.current_x = x
            self.current_y = y
            pyglet.clock.schedule_interval(self.add_point, DRAW_TIME_INTERVAL)  # Add points for view
            pyglet.clock.schedule_interval(self.add_stroke_point, STORE_TIME_INTERVAL)  # Add points for storing

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.drawing:
            self.current_x = x
            self.current_y = y

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT and self.drawing:
            self.drawing = False
            pyglet.clock.unschedule(self.add_point)
            pyglet.clock.unschedule(self.add_stroke_point)
            end_time = time.time()
            duration = int((end_time - self.start_time) * 1000)  # Duration in milliseconds

            points = [recognizer.Point(px, py, pt) for px, py, pt in self.stroke_points]
            print("TYPE", type)
            stroke_name = f"{type}{len(self.strokes) + 1:02}"
            stroke = Stroke(stroke_name, points, len(self.strokes) + 1, duration)
            self.strokes.append(stroke)
            stroke.save_XML()

            self.label.text = self.dollar_recognizer.recognize(points).name

    def add_point(self, dt):
        if self.drawing and (self.view_points[-1] != (self.current_x, self.current_y)):
            self.view_points.append((self.current_x, self.current_y))

    def add_stroke_point(self, dt):
        #pyglet has origin on the left down, not left up! therefore flip y for stroke points
        self.stroke_points.append((self.current_x, WINDOW_SIZE - self.current_y, int((time.time()-self.start_time) * 1000)))

# Run the application
if __name__ == '__main__':
    window = DrawWindow()
    pyglet.app.run()