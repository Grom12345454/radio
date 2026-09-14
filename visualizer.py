import random


class Visualizer:

    def __init__(self, canvas, color="#6C63FF"):

        self.canvas = canvas
        self.color = color

        self.enabled = True


    def draw(self, active=False):

        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        bar_width = 8
        gap = 4

        count = max(
            1,
            int(width / (bar_width + gap))
        )

        for i in range(count):

            if active:

                level = random.randint(
                    8,
                    max(
                        10,
                        int(height * 0.85)
                    )
                )

            else:

                level = 3

            x1 = i * (bar_width + gap)
            x2 = x1 + bar_width

            y1 = height - level
            y2 = height

            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=self.color,
                outline=""
            )