import cv2
import numpy as np
from image_viewer import ImageViewer
from image_viewer import DOWNSAMPLE

SCALE_PREVIEW_SAVE_LOCATION = 'previews/scale_preview.jpeg'


class ScaleSelector(ImageViewer):
    WINDOW_NAME = "CAD Lasso"
    MAX_ZOOM_LEVEL = 20

    def __init__(self, screen_width, screen_height, image_location=None, downsample=DOWNSAMPLE):
        super().__init__(screen_width, screen_height, image_location, downsample)

        if image_location is None:
            # points in scale measurement
            self.first_point = None
            self.second_point = None
            self.next_point = None

    def load_image(self, image_location, downsample=DOWNSAMPLE):
        super().load_image(image_location, downsample)

        # points in scale measurement
        self.first_point = None
        self.second_point = None
        self.next_point = None

        cv2.imwrite(SCALE_PREVIEW_SAVE_LOCATION, self.im)

    def get_processed_image(self):
        image_to_show = self.show_scale_preview(self.im.copy())
        image_to_show = self.handle_zoom_and_pan(image_to_show)
        return image_to_show

    def handle_mouse_event(self, event, x, y, flags, param):
        x, y = self.convert_local_to_global(x, y)
        x = int(x)
        y = int(y)
        if event == cv2.EVENT_LBUTTONDOWN:
            print(x, y)
        # check to see if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:

            if self.first_point is None:
                self.first_point = (x, y)
            elif self.second_point is None:
                self.second_point = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE:
            self.next_point = (x, y)
        elif event == cv2.EVENT_RBUTTONUP:
            # undo previous click if right mouse button clicked
            if self.second_point is not None:
                self.second_point = None
            elif self.first_point is not None:
                self.first_point = None

    def handle_key_press(self, key):
        if super().handle_key_press(key):
            return True
        elif key == 13:  # enter key
            if self.second_point is not None:
                preview = self.show_scale_preview(self.im.copy(), thickness_scale_factor=2)
            else:
                preview = self.im.copy()
            cv2.imwrite(SCALE_PREVIEW_SAVE_LOCATION, preview)
            return True
        return False

    def show_scale_preview(self, image, thickness_scale_factor=1):
        image_copy = image.copy()
        thickness = thickness_scale_factor * \
                    int(np.ceil(3 * (self.image_width / self.window_width) / self.get_zoom_scale_factor()))

        if self.second_point is not None:
            cv2.line(image_copy, self.first_point, self.second_point, (255, 0, 0), thickness)
        elif self.first_point is not None:
            cv2.line(image_copy, self.first_point, self.next_point, (0, 255, 0), thickness)

        return image_copy

    def get_pixel_distance(self):
        if self.second_point is not None:
            x1, y1 = self.first_point
            x2, y2 = self.second_point
            dx = x2 - x1
            dy = y2 - y1
            return np.sqrt(dx*dx + dy*dy)
        else:
            return None


if __name__ == "__main__":
    test = ScaleSelector(1920, 1080)
    test.load_image("test_lens.jpg")
    test.init_window()
    test.show()
