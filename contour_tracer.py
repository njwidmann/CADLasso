import cv2
import numpy as np
from image_viewer import ImageViewer
from image_viewer import DOWNSAMPLE
import skimage.draw


CONTOUR_PREVIEW_SAVE_LOCATION = 'previews/contour_preview.jpeg'


def find_shortest_route(contour, ind1, ind2):
    num_points = contour.shape[0]
    if ind1 < ind2:
        route1_length = ind2 - ind1
        route2_length = num_points - route1_length
        if route1_length < route2_length:
            route = contour[ind1:ind2 + 1, :, :]
        else:
            route = np.concatenate((contour[ind2:, :, :], contour[:ind1 + 1, :, :]))
            route = np.flip(route, axis=0)
    else:
        route1_length = ind1 - ind2
        route2_length = num_points - route1_length
        if route1_length < route2_length:
            route = contour[ind2:ind1 + 1, :, :]
            route = np.flip(route, axis=0)
        else:
            route = np.concatenate((contour[ind1:, :, :], contour[:ind2 + 1, :, :]))
    return route


def find_closest_contour_point(contour, point):
    target_point_x, target_point_y = point
    points_x = contour[:, 0, 0]
    points_y = contour[:, 0, 1]
    dist = np.sqrt(np.power(points_x - target_point_x, 2) + np.power(points_y - target_point_y, 2))
    ind = np.argmin(dist)
    closest_point_x = contour[ind, 0, 0]
    closest_point_y = contour[ind, 0, 1]

    return ind, (closest_point_x, closest_point_y)


def find_points_along_line(x1, y1, x2, y2):
    discrete_line = skimage.draw.line(y1, x1, y2, x2)
    y, x = discrete_line
    points = np.empty((len(y), 1, 2), np.int32)
    points[:, 0, 0] = x
    points[:, 0, 1] = y

    return points


def add_tolerance(points, tolerance):
    points_len, _, _ = points.shape
    point_slopes = np.empty(points_len)
    # find point slopes
    for i in range(0, points_len):
        prev_index = i-3
        prev_point = points[prev_index, 0, :]
        next_index = i+3
        if next_index >= points_len:
            next_index -= points_len
        next_point = points[next_index, 0, :]

        dx = float(next_point[0] - prev_point[0])
        dy = float(next_point[1] - prev_point[1])
        if dx == 0:  # avoid divide by 0
            dx = 0.00000001
        point_slopes[i] = dy/dx

    # find tolerances as normals to slopes at each point
    x_tolerance = -np.sin(np.arctan(point_slopes)) * tolerance
    y_tolerance = np.cos(np.arctan(point_slopes)) * tolerance

    adjusted_points = points.copy()
    # now find adjusted points
    for i in range(0, points_len):
        point = points[i, 0, :]
        # there are two options for each point. One is inside and one is outside the contour
        adjusted_point_1 = point + np.array([x_tolerance[i], y_tolerance[i]])
        x1, y1 = adjusted_point_1[0], adjusted_point_1[1]
        adjusted_point_2 = point - np.array([x_tolerance[i], y_tolerance[i]])
        x2, y2 = adjusted_point_2[0], adjusted_point_2[1]
        # check which one it is
        if tolerance < 0:  # means we want to make the shape smaller
            if cv2.pointPolygonTest(points, (x1, y1), False) > 0:  # check if point 1 is inside contour
                adjusted_points[i, 0, :] = adjusted_point_1
            elif cv2.pointPolygonTest(points, (x2, y2), False) > 0:  # check if point 2 is inside contour
                adjusted_points[i, 0, :] = adjusted_point_2
        elif tolerance > 0:  # means we want to make the shape bigger
            if cv2.pointPolygonTest(points, (x1, y1), False) < 0:  # check if point 1 is outside contour
                adjusted_points[i, 0, :] = adjusted_point_1
            elif cv2.pointPolygonTest(points, (x2, y2), False) < 0:  # check if point 2 is outside contour
                adjusted_points[i, 0, :] = adjusted_point_2

    return adjusted_points


class ContourTracer(ImageViewer):

    WINDOW_NAME = "CAD Lasso"
    MAX_ZOOM_LEVEL = 20

    def __init__(self, screen_width, screen_height, image_location=None, downsample=DOWNSAMPLE):
        super().__init__(screen_width, screen_height, image_location, downsample)

        if image_location is None:
            # points in lasso
            self.points = []
            self.contours = []
            self.next_point = (0, 0)
            self.next_contour = None

    def load_image(self, image_location, downsample=DOWNSAMPLE):
        super().load_image(image_location, downsample)

        # points in lasso
        self.points = []
        self.contours = []
        self.next_point = (0, 0)
        self.next_contour = None

        cv2.imwrite(CONTOUR_PREVIEW_SAVE_LOCATION, self.im)

    def get_processed_image(self):
        image_to_show = self.show_next_point_preview(self.im.copy())
        image_to_show = self.handle_display_points(image_to_show)
        image_to_show = self.handle_zoom_and_pan(image_to_show)
        return image_to_show

    def handle_mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(x, y)
            x, y = self.convert_local_to_global(x, y)
            print(x, y)
            print(self.convert_global_to_local(x, y))
        # check to see if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:

            if self.next_contour is not None:
                self.points.append((self.next_contour[-1, 0, 0], self.next_contour[-1, 0, 1]))
                self.contours.append(self.next_contour.copy())
            else:
                x, y = self.convert_local_to_global(x, y)
                self.points.append((int(x), int(y)))
                self.contours.append(np.array([[[int(x), int(y)]]]))
        elif event == cv2.EVENT_MOUSEMOVE:
            self.next_point = self.convert_local_to_global(x, y)
        elif event == cv2.EVENT_RBUTTONUP:
            # undo previous click if right mouse button clicked
            if len(self.contours) > 0:
                del self.contours[-1]
                self.next_contour = None
            if len(self.points) > 0:
                del self.points[-1]
                self.next_point = None

    def handle_key_press(self, key):
        if super().handle_key_press(key):
            return True
        elif key == 13:  # enter key
            preview = self.handle_display_points(self.im.copy(), thickness_scale_factor=2)
            cv2.imwrite(CONTOUR_PREVIEW_SAVE_LOCATION, preview)
            return True
        return False

    def handle_display_points(self, image, thickness_scale_factor=1):
        image_copy = image.copy()
        if len(self.contours) > 0:
            color = (255, 0, 0)  # blue
            # choose line thickness (in pixels) based on window size and zoom
            thickness = thickness_scale_factor * \
                        int(np.ceil(3 * (self.image_width / self.window_width) / self.get_zoom_scale_factor()))

            # append all the contours into one giant line
            points = self.contours[0]
            for cont in self.contours[1:]:
                points = np.concatenate((points, cont))

            cv2.polylines(image_copy, [points], False, color, thickness=thickness, lineType=cv2.LINE_AA)

        return image_copy

    def show_next_point_preview(self, image):
        thickness = int(np.ceil(3 * (self.image_width / self.window_width) / self.get_zoom_scale_factor()))

        if len(self.points) > 0 and self.next_point is not None:
            last_point_x, last_point_y = self.points[-1]
            next_point_x, next_point_y = self.next_point

            last_point_x = int(last_point_x)
            last_point_y = int(last_point_y)
            next_point_x = int(next_point_x)
            next_point_y = int(next_point_y)

            top_left_x = min(last_point_x, next_point_x)
            top_left_y = min(last_point_y, next_point_y)
            bottom_right_x = max(last_point_x, next_point_x)
            bottom_right_y = max(last_point_y, next_point_y)

            scale_factor = self.image_width / self.window_width / self.get_zoom_scale_factor()

            if (bottom_right_x - top_left_x) / scale_factor > 1 and (bottom_right_y - top_left_y) / scale_factor > 1:

                im_copy = image.copy()
                roi = im_copy[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
                roi = cv2.resize(roi, None, fx=(1/scale_factor), fy=(1/scale_factor))
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                canny = cv2.Canny(gray, 30, 200)

                contours, hierarchy = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

                min_dist = self.image_width
                closest_contour = -1
                for i, contour in enumerate(contours):
                    contour[:, :, :] = np.round(contour[:, :, :] * scale_factor)
                    contour[:, :, 0] += top_left_x
                    contour[:, :, 1] += top_left_y

                    dist = cv2.pointPolygonTest(contour, (next_point_x, next_point_y), True)
                    if abs(dist) < min_dist:
                        min_dist = abs(dist)
                        closest_contour = i

                if closest_contour >= 0:
                    # find closest contour points for next contour
                    start_ind, (start_point_x, start_point_y) = \
                        find_closest_contour_point(contours[closest_contour], (last_point_x, last_point_y))
                    end_ind, (end_point_x, end_point_y) = \
                        find_closest_contour_point(contours[closest_contour], (next_point_x, next_point_y))

                    # find shortest route (since a contour is a loop)
                    route = find_shortest_route(contours[closest_contour], start_ind, end_ind)

                    # connect end of last contour route to next contour route
                    line = find_points_along_line(last_point_x, last_point_y, start_point_x, start_point_y)
                    route = np.concatenate((line, route), 0)

                    self.next_contour = route

                    # draw closest/shortest contour route
                    cv2.polylines(image, [route], False, (0, 255, 0), thickness=thickness, lineType=cv2.LINE_AA)

                else:
                    line = find_points_along_line(last_point_x, last_point_y, next_point_x, next_point_y)
                    self.next_contour = line

                    # if no contours found, we just draw to the current cursor location
                    cv2.line(image, (last_point_x, last_point_y), (next_point_x, next_point_y), (0, 255, 0),
                             thickness)
            else:
                line = find_points_along_line(last_point_x, last_point_y, next_point_x, next_point_y)
                self.next_contour = line

                # if no contours found, we just draw to the current cursor location
                cv2.line(image, (last_point_x, last_point_y), (next_point_x, next_point_y), (0, 255, 0),
                         thickness)

        return image

    def scale_and_save_points(self, save_location, scale_factor, tolerance):
        # append all the contours into one giant line
        points = self.contours[0]
        for cont in self.contours[1:]:
            points = np.concatenate((points, cont))

        points[:, 0, 1] = -1 * points[:, 0, 1]  # flip y because image zero is top left

        # find tolerance in pixels
        tolerance = tolerance / scale_factor
        points = add_tolerance(points, tolerance)

        points_to_save = points[:, 0, :]
        points_to_save = points_to_save * scale_factor  # convert from pixels to cm
        zero_x = np.average(points_to_save[:, 0])
        zero_y = np.average(points_to_save[:, 1])
        points_to_save[:, 0] -= zero_x
        points_to_save[:, 1] -= zero_y

        np.savetxt(save_location, points_to_save, delimiter=",")  # save to csv file


if __name__ == "__main__":
    test = ContourTracer(1920, 1080)
    test.load_image("test_lens.jpg")
    test.init_window()
    test.show()
