
import adsk.core, adsk.fusion, traceback

SPLINE = True
DOWNSAMPLE = 20  # Integer >= 1
CONSTRAIN = False
SCALE_FACTOR = 1.024  # a percent. e.g. 1.01 means scale up by 1% in all directions


def fprint(ui, message):
    if ui:
        ui.messageBox(message)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()

        ui = app.userInterface

        # Get all components in the active design.
        product = app.activeProduct
        design = product
        title = 'Import Spline csv'
        if not design:
            ui.messageBox('No active Fusion design', title)
            return

        dlg = ui.createFileDialog()
        dlg.title = 'Open CSV File'
        dlg.filter = 'Comma Separated Values (*.csv);;All Files (*.*)'
        if dlg.showOpen() != adsk.core.DialogResults.DialogOK:
            return

        point_objects = adsk.core.ObjectCollection.create()

        filename = dlg.filename
        f = open(filename, 'r')
        line = f.readline()
        data = []
        sample_count = 0
        while line:
            pntStrArr = line.split(',')
            for pntStr in pntStrArr:
                data.append(float(pntStr))

            if len(data) == 2:

                sample_count += 1
                if sample_count % DOWNSAMPLE == 0:
                    point_x = data[0]
                    point_y = data[1]

                    point_x *= SCALE_FACTOR
                    point_y *= SCALE_FACTOR

                    point = adsk.core.Point3D.create(point_x, point_y, 0)  # all our points are 2D
                    point_objects.add(point)

            line = f.readline()
            data.clear()
        f.close()
        root = design.rootComponent

        if root.sketches.count > 0:
            ui.messageBox("Select sketch")
            skSel = ui.selectEntity('Select the point sketch', 'Sketches')
            if skSel:
                sketch = adsk.fusion.Sketch.cast(skSel.entity)
                sketch.isComputeDeferred = True
                if SPLINE:
                    if len(point_objects) > 0:
                        point_objects.add(point_objects[0])  # close the spline

                        spline = sketch.sketchCurves.sketchFittedSplines.add(point_objects)

                        if CONSTRAIN:
                            dims = adsk.fusion.SketchDimensions.cast(sketch.sketchDimensions)
                            origin = adsk.core.Point3D.create(0, 0, 0)
                            origin_point = sketch.sketchPoints.add(origin)
                            for point in spline.fitPoints:
                                dims.addDistanceDimension(point, origin_point, 1, origin)  # horizontal dimension
                                dims.addDistanceDimension(point, origin_point, 2, origin)  # vertical dimension
                    else:
                        ui.messageBox("No points found in selected .csv file")
                else: # Don't spline
                    if CONSTRAIN:
                        dims = adsk.fusion.SketchDimensions.cast(sketch.sketchDimensions)
                        origin = adsk.core.Point3D.create(0, 0, 0)
                        origin_point = sketch.sketchPoints.add(origin)
                        for point in point_objects:
                            p = sketch.sketchPoints.add(point)
                            dims.addDistanceDimension(p, origin_point, 1, origin)  # horizontal dimension
                            dims.addDistanceDimension(p, origin_point, 2, origin)  # vertical dimension
                    else:
                        for point in point_objects:
                            sketch.sketchPoints.add(point)

                sketch.isComputeDeferred = False

        else:
            ui.messageBox("No sketches. Please create a sketch before importing points")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

