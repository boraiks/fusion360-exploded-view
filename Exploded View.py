import adsk.core
import adsk.fusion
import traceback

def get_y_value(item):
    return item[1]

def get_abs_y_value(item):
    return abs(item[1])

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        
        if not design:
            return
            
        root = design.rootComponent
        
        gap_cm = 3.0  # 10 mm
        tol_cm = 0.1  # 1 mm tolerance
        
        # 1. Collect bounding box center Y values
        parts = []
        for occ in root.occurrences:
            if occ.isGrounded or occ.isGroundToParent:
                continue
            
            bbox = occ.boundingBox
            center_y = (bbox.minPoint.y + bbox.maxPoint.y) / 2.0
            parts.append((occ, center_y))
        
        # 2. Separate parts based on Y position (-> based on origin)
        positive_list = []
        negative_list = []
        
        for p in parts:
            y_value = p[1]
            if y_value >= 0:
                positive_list.append(p)
            else:
                negative_list.append(p)
                
        # Sort the lists
        pos_parts = sorted(positive_list, key=get_y_value)
        neg_parts = sorted(negative_list, key=get_abs_y_value)
        
        # 3. Explode logic
        def explode_group(group, direction):
            if not group: 
                return
            
            layer = 1
            first_item = group[0]
            prev_y = first_item[1]
            
            for item in group:
                occ = item[0]
                current_y = item[1]
                
                y_difference = abs(current_y - prev_y)
                if y_difference > tol_cm:
                    layer += 1
                    prev_y = current_y

                move_y = layer * gap_cm * direction
                
                mat = occ.transform2
                vec = mat.translation
                vec.y += move_y
                mat.translation = vec
                occ.transform2 = mat

        # 4. Apply explosion
        explode_group(pos_parts, 1)
        explode_group(neg_parts, -1)
        
    except:
        if ui:
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))