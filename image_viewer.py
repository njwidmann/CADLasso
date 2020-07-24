import cv2

DOWNSAMPLE = 1


class ImageViewer:

    WINDOW_NAME = "CAD Lasso"
    MAX_ZOOM_LEVEL = 20

    def __init__(self, screen_width, screen_height, image_location=None, downsample=DOWNSAMPLE):

        self.screen_width = screen_width
        self.screen_height = screen_height

        if image_location is not None:
            self.load_image(image_location, downsample)
        else:
            self.im = None
            self.raw_image_width = None
            self.raw_image_height = None
            self.image_width = None
            self.image_height = None
            self.window_width = None
            self.window_height = None
            self.zoom_center_x = None
            self.zoom_center_y = None
            self.current_zoom_level = None

    def load_image(self, image_location, downsample=DOWNSAMPLE):
        self.im = cv2.imread(image_location)
        self.raw_image_height, self.raw_image_width, _ = self.im.shape
        self.im = cv2.resize(self.im, None, fx=1.0/downsample, fy=1.0/downsample)
        self.image_height, self.image_width, _ = self.im.shape
        scale_width = self.screen_width / self.image_width
        scale_height = self.screen_height / self.image_height
        scale = min(scale_width, scale_height)

        # resized window width and height
        self.window_width = int(self.image_width * scale * 0.5)
        self.window_height = int(self.image_height * scale * 0.5)

        # for zooming and panning
        self.zoom_center_x = self.image_width / 2
        self.zoom_center_y = self.image_height / 2
        self.current_zoom_level = 0

    def init_window(self):
        # cv2.WINDOW_NORMAL makes the output window resizeable
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_KEEPRATIO)

        # resize the window according to the screen resolution
        cv2.resizeWindow(self.WINDOW_NAME, self.window_width, self.window_height)

        # set callback
        cv2.setMouseCallback(self.WINDOW_NAME, self.handle_mouse_event)

    def show(self):
        while True:
            image_to_show = self.get_processed_image()

            cv2.imshow(self.WINDOW_NAME, image_to_show)

            key = cv2.waitKey(10)
            if self.handle_key_press(key):
                cv2.destroyAllWindows()
                break

    def get_processed_image(self):
        image_to_show = self.handle_zoom_and_pan(self.im.copy())
        return image_to_show

    def handle_mouse_event(self, event, x, y, flags, param):
        pass

    def handle_key_press(self, key):
        if key == 27:  # esc
            return True
        elif key == ord("e"):  # "e" -> zoom in
            self.increment_zoom(1)
        elif key == ord("q"):  # "q" -> zoom out
            self.increment_zoom(-1)
        elif key == ord("a"):  # "a" -> pan left
            self.increment_pan_x(-1)
        elif key == ord("d"):  # "d" -> pan right
            self.increment_pan_x(1)
        elif key == ord("w"):  # "w" -> pan up
            self.increment_pan_y(1)
        elif key == ord("s"):  # "s" -> pan down
            self.increment_pan_y(-1)
        return False

    def convert_local_to_global(self, x, y):
        zoom = self.get_zoom_scale_factor()
        zoom_width = self.image_width / zoom
        zoom_height = self.image_height / zoom
        global_x = self.zoom_center_x - zoom_width/2 + x/zoom
        global_y = self.zoom_center_y - zoom_height/2 + y/zoom
        return global_x, global_y

    def convert_global_to_local(self, x, y):
        zoom = self.get_zoom_scale_factor()
        zoom_width = self.image_width / zoom
        zoom_height = self.image_height / zoom
        local_x = (x - (self.zoom_center_x - zoom_width/2)) * zoom
        local_y = (y - (self.zoom_center_y - zoom_height/2)) * zoom

        if local_x < 0 or local_x > self.image_width:
            local_x = -1
        if local_y < 0 or local_y > self.image_height:
            local_y = -1

        return local_x, local_y

    def increment_zoom(self, zoom_increment):
        self.current_zoom_level += zoom_increment
        if self.current_zoom_level < 0:
            self.current_zoom_level = 0
        elif self.current_zoom_level > self.MAX_ZOOM_LEVEL:
            self.current_zoom_level = self.MAX_ZOOM_LEVEL
        # make sure zoom center is still accurate
        self.increment_pan_x(0)
        self.increment_pan_y(0)

    def get_zoom_scale_factor(self):
        return 1 + pow(0.15 * self.current_zoom_level, 2)

    def increment_pan_x(self, pan_increment):
        # we want to pan 1/10 of the current image view size
        zoom_width = self.image_width / self.get_zoom_scale_factor()
        pan_increment_size = zoom_width / 10
        self.zoom_center_x += pan_increment * pan_increment_size
        if self.zoom_center_x - zoom_width / 2 < 0:
            self.zoom_center_x = zoom_width / 2
        elif self.zoom_center_x + zoom_width / 2 > self.image_width:
            self.zoom_center_x = self.image_width - zoom_width / 2

    def increment_pan_y(self, pan_increment):
        # we want to pan 1/10 of the current image view size
        zoom_height = self.image_height / self.get_zoom_scale_factor()
        pan_increment_size = zoom_height / 10
        self.zoom_center_y -= pan_increment * pan_increment_size  # minus because origin is top left
        if self.zoom_center_y - zoom_height / 2 < 0:
            self.zoom_center_y = zoom_height / 2
        elif self.zoom_center_y + zoom_height / 2 > self.image_height:
            self.zoom_center_y = self.image_height - zoom_height / 2

    def get_zoom_region_position(self):
        zoom_scale_factor = self.get_zoom_scale_factor()
        zoom_width = int(self.image_width / zoom_scale_factor)
        zoom_height = int(self.image_height / zoom_scale_factor)
        zoom_x = int(self.zoom_center_x - zoom_width / 2)
        zoom_y = int(self.zoom_center_y - zoom_height / 2)
        return zoom_x, zoom_y, zoom_width, zoom_height

    def handle_zoom_and_pan(self, image):
        zoom_x, zoom_y, zoom_width, zoom_height = self.get_zoom_region_position()

        if zoom_x < 0:
            zoom_x = 0
        elif zoom_x + zoom_width > self.image_width:
            zoom_x = self.image_width - zoom_width
        if zoom_y < 0:
            zoom_y = 0
        elif zoom_y + zoom_height > self.image_height:
            zoom_y = self.image_height - zoom_height

        roi = image[zoom_y:zoom_y+zoom_height, zoom_x:zoom_x+zoom_width]
        image_to_show = cv2.resize(roi, (self.image_width, self.image_height))
        return image_to_show


if __name__ == "__main__":
    test = ImageViewer(1920, 1080)
    test.load_image("test_lens2.jpg")
    test.init_window()
    test.show()

