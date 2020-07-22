from appJar import gui
from PIL import Image, ImageTk
import imghdr
import os
from contour_tracer import ContourTracer
from contour_tracer import CONTOUR_PREVIEW_SAVE_LOCATION
from scale_selector import ScaleSelector
from scale_selector import SCALE_PREVIEW_SAVE_LOCATION


contour_tracer = ContourTracer(1920, 1080)  # TODO: get screen dims
scale_selector = ScaleSelector(1920, 1080)
image_file_location = None


def delete_files_in_directory(dir_name):
    file_list = [f for f in os.listdir(dir_name)]
    for f in file_list:
        os.remove(os.path.join(dir_name, f))


def press_load_button():
    global contour_tracer, image_file_location
    file = app.entry("file_entry")
    print("File:", file)
    if imghdr.what(file) is not None:  # make sure it's a picture
        image_file_location = file
        photo = ImageTk.PhotoImage(load_image(200, file))
        app.setImageData("contour_preview", photo, fmt="PhotoImage")
        app.setImageData("scale_preview", photo, fmt="PhotoImage")

        w, h = Image.open(file).size

        app.setLabel("raw_size_preview_label", "  Raw w, h = %d, %d" % (w,h))

        downsample_string = app.getEntry("downsample_entry")
        if len(downsample_string) > 0:
            try:
                downsample = float(downsample_string)
                if downsample >= 1:
                    contour_tracer.load_image(image_file_location, downsample)
                    scale_selector.load_image(image_file_location, downsample)
                    return
                else:
                    app.popUp("Error", "Not a valid downsample. Choose a number >= 1")
            except:
                app.popUp("Error", "Not a valid downsample. Choose a number >= 1")

        contour_tracer.load_image(image_file_location)
        scale_selector.load_image(image_file_location)


def press_save_button():
    print("Save")
    scale_factor = get_scale_factor()
    save_location = "output/" + app.getEntry("save_entry")
    if not save_location.endswith(".csv"):
        save_location = save_location + ".csv"
    print(save_location)

    if scale_factor is not None:
        try:
            tolerance = float(app.getEntry("tolerance_entry")) / 10.0  # convert to cm
            contour_tracer.scale_and_save_points(save_location, scale_factor, tolerance)
        except:
            app.popUp("Error", "Please ensure all information has been entered correctly")
    else:
        app.popUp("Error", "Please enter all required information")


def press_close_button():
    app.stop()


def press_contour_preview():
    global image_file_location, contour_tracer
    if image_file_location is not None:
        contour_tracer.init_window()
        contour_tracer.show()
        photo = ImageTk.PhotoImage(load_image(200, CONTOUR_PREVIEW_SAVE_LOCATION))
        app.setImageData("contour_preview", photo, fmt="PhotoImage")


def press_scale_preview():
    global image_file_location, scale_selector
    if image_file_location is not None:
        scale_selector.init_window()
        scale_selector.show()
        photo = ImageTk.PhotoImage(load_image(200, SCALE_PREVIEW_SAVE_LOCATION))
        app.setImageData("scale_preview", photo, fmt="PhotoImage")

        pixel_distance = scale_selector.get_pixel_distance()
        if pixel_distance is not None:
            app.setLabel("scale_text1", ("%.2f pixels = " % pixel_distance))
        else:
            app.setLabel("scale_text1", "______ pixels = ")


def get_scale_factor():
    entry_string = app.getEntry("scale_entry")
    pixel_distance = scale_selector.get_pixel_distance()
    if len(entry_string) > 0 and pixel_distance is not None:
        try:
            dist_mm = float(entry_string)
            dist_cm = dist_mm / 10.0
            if pixel_distance > 0 and dist_cm > 0:
                return dist_cm / pixel_distance
        except:
            return None
    return None


def load_image(height, location=None):
    if location is None or not os.path.exists(location):
        im = Image.open("cropped-placeholder.jpg")
    else:
        im = Image.open(location)

    w, h = im.size
    ratio = w / h
    new_h = height
    new_w = new_h * ratio
    im = im.resize((int(new_w), int(new_h)))
    return im


def populate_save_entry():
    save_file_index = 0
    while os.path.exists("output/point_data_%d.csv" % save_file_index):
        save_file_index += 1
    app.setEntry("save_entry", "point_data_%d.csv" % save_file_index)


app = gui()
app.setFont(14)

# delete previous previews
delete_files_in_directory("previews")

app.startLabelFrame("Select Image File")
app.addFileEntry("file_entry", 0, 0)
app.addLabel("raw_size_preview_label", "  Raw w, h = 0, 0", 0, 1)
#photo = ImageTk.PhotoImage(load_image(100))
#app.addImageData("image_preview", photo, fmt="PhotoImage")
app.addLabel("downsample_text1", "Downsample Factor = ", 1, 0)
app.addEntry("downsample_entry", 1, 1)
app.setEntry("downsample_entry", "1.0")
app.addButton("Load", press_load_button, 2, 0)
app.stopLabelFrame()

app.startLabelFrame("Select Contours")
photo = ImageTk.PhotoImage(load_image(200))
app.addImageData("contour_preview", photo, fmt="PhotoImage")
app.setImageSubmitFunction("contour_preview", press_contour_preview)
app.stopLabelFrame()

app.startLabelFrame("Set Scale and Tolerances")
photo = ImageTk.PhotoImage(load_image(200))
app.addImageData("scale_preview", photo, fmt="PhotoImage")
app.setImageSubmitFunction("scale_preview", press_scale_preview)
app.addLabel("scale_text1", "______ pixels = ", 1, 0)
app.addEntry("scale_entry", 1, 1)
app.addLabel("scale_text2", "mm", 1, 2)
app.addLabel("tolerance_text1", "Tolerance = ", 2, 0)
app.addEntry("tolerance_entry", 2, 1)
app.setEntry("tolerance_entry", "0.0")
app.addLabel("tolerance_text2", "mm", 2, 2)
app.stopLabelFrame()

app.startLabelFrame("")
app.setSticky("ew")
app.addLabel("save_text", "Save Filename (.csv): ", 0, 0)
app.addEntry("save_entry", 0, 1)
populate_save_entry()
app.addButton("Save", press_save_button, 1, 0)
app.addButton("Close", press_close_button, 1, 1)
app.stopLabelFrame()

app.go()