"""
This rhino script tries to extract all the extrusion endpoints from a model.
It outputs them as a JSON-ish array of 3D coordinate arrays, written to a text file of your choice.
"""
import rhinoscriptsyntax as rs
import rhinoscript.utility as rhutil
import json

def ExportEndpoints():
    objects = rs.AllObjects()
    path_endpoints = []
    for obj in objects:
            """
            try:
                rhutil.coerceguid(id)
                obj = rs.MakeSurfacePeriodic(obj, 0) # 0 designates perodicity in the U direction
            except:
                pass
            """
            if rs.IsSurface(obj):
                surface = rhutil.coercesurface(obj)
                if hasattr(surface, 'PathStart'):
                    path_endpoints.append([
                        [ float(i) for i in str(surface.PathStart).split(',') ],
                        [ float(i) for i in str(surface.PathEnd).split(',') ],
                    ])

    #Get the filename to create
    filter = "Text File (*.txt)|*.txt|All Files (*.*)|*.*||"
    filename = rs.SaveFileName("Save point coordinates as", filter)
    if( filename==None ): return
    
    file = open(filename, "w")
    file.write( json.dumps(path_endpoints, indent=4) )
    file.close()


if( __name__ == '__main__' ):
    ExportEndpoints()
