"""
This rhino script tries to extract all the cylinder endpoints from a model.
It outputs them as a JSON-ish array of 3D coordinate arrays, written to a text file of your choice.
"""
import rhinoscriptsyntax as rs
import json

def ExportEndpoints():
    #Get the objects that Rhino thinks are cylinders
    objects = rs.AllObjects()
    cylindricalObjects = []
    for obj in objects:
        if rs.IsSurface(obj) and rs.IsCylinder(obj):
            cylindricalObjects.append(obj)
    if( len(cylindricalObjects) == 0 ): return

    #Get the filename to create
    filter = "Text File (*.txt)|*.txt|All Files (*.*)|*.*||"
    filename = rs.SaveFileName("Save point coordinates as", filter)
    if( filename==None ): return
    
    file = open(filename, "w")
    cylinders = []
    for id in cylindricalObjects:
        plane, height, radius = rs.SurfaceCylinder(id)
        origin = plane.Origin
        normal = plane.Normal
        cylPathVector = rs.VectorScale( rs.VectorUnitize(normal), height )
        endpoint = rs.VectorAdd( origin, cylPathVector)
        points = [origin, endpoint]
        
        coordArr = []
        for pt in points:
            coords = [ float(coord) for coord in str(pt).split(',') ]
            coordArr.append(coords)
        cylinders.append(coordArr)
    file.write( json.dumps(cylinders, indent=4) )
    file.close()


if( __name__ == '__main__' ):
    ExportEndpoints()
