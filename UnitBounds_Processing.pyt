#-------------------------------------------------------------------------------

#   UnitBounds_Processing.pyt
#
#   Create UnitBounds.gdb/unit_bounds_wgs feature class
#   from Lands nps_boundary.shp and
#   UnitBounds_Processing.gdb/AlternateBounds and AffiliatedAreas
#   feature classes.
#
#   Prerequisites/Inputs:
#       ArcGIS 10.2.2 or higher
#       Source nps_boundary.shp fron Lands
#           https://irma.nps.gov/App/Reference/Profile/2194483?lnv=true
#       XML metadata template in known subfolder (<somewhere>/Templates/Metadata)
#       Output Folder/Workspace
#
#   Outputs:
#       Two file geodatabases feature classes: unit_bounds_wgs and
#       nps_boundary (copy of nps_boundary.shp) in
#       UnitBounds.gdb
#
#   Created by:  NPS Inventory and Monitoring Division GIS Staff
#   Update date: 20150820
#
#
#
#-------------------------------------------------------------------------------

import arcpy
import os, time
from datetime import datetime

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "UnitBounds_Processing"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [UpdateUnitBounds]

class UpdateUnitBounds(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Unit Bounds"
        self.description = "Create or update unit_bounds_wgs feature class in UnitBounds.gdb"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName = "Source NPS Lands Shapefile",
            name = "npsAdminBounds",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        param0.value = r"X:\ProjectData\Data_Processing\NPS_Bounds\NPS_Boundary_Source\nps_boundary\nps_boundary.shp"

        param1 = arcpy.Parameter(
            displayName = "Output GeoDatabase",
            name = "outDB",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input")

        param2 = arcpy.Parameter(
            displayName = "Alternate Bounds feature class",
            name = "altBounds",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
            )
        param2.value = "D:\Workspace\UnitBound_Processing.gdb\AlternateBounds"

        param3 = arcpy.Parameter(
            displayName = "Affiliated Areas feature class",
            name = "affBounds",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
            )
        param3.value = "D:\Workspace\UnitBound_Processing.gdb\AffiliatedAreas"

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def deleteUnit(self, targetLayer, codeSnippet):
        """
            Deletes selected feature from target layer
        """
        arcpy.SelectLayerByAttribute_management(targetLayer,"NEW_SELECTION", codeSnippet)
        arcpy.DeleteFeatures_management(targetLayer)
        arcpy.AddMessage('\n Deleted '  + codeSnippet)
        arcpy.SelectLayerByAttribute_management(targetLayer,"CLEAR_SELECTION")


    def calcField(self, targetLayer, targetField, selectSnippet, expr, switch=None, targetField2=None, selectSnippet2=None, expr2=None):
        """
            Calculates field for selected records
        """
        arcpy.SelectLayerByAttribute_management(targetLayer,"NEW_SELECTION", selectSnippet)
        if switch:
            arcpy.SelectLayerByAttribute_management(targetLayer,"SWITCH_SELECTION", selectSnippet)
        arcpy.CalculateField_management(targetLayer, targetField, expr, "PYTHON")
        arcpy.AddMessage('\nCalculated Field: '  + selectSnippet + ' as ' + expr)
        arcpy.SelectLayerByAttribute_management(targetLayer,"CLEAR_SELECTION")
        if targetField2:
            arcpy.SelectLayerByAttribute_management(targetLayer,"NEW_SELECTION", selectSnippet)
            arcpy.CalculateField_management(targetLayer, targetField2, expr2, "PYTHON")
            arcpy.SelectLayerByAttribute_management(targetLayer,"CLEAR_SELECTION")
            arcpy.AddMessage('\nCalculated Field: '  + selectSnippet2 + ' as ' + expr2)

    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1
        # Lands bounds have M and Z values for some reason
        arcpy.env.outputMFlag = "Disabled"
        arcpy.env.outputZFlag = "Disabled"
        outputLandsFeatureClassName = "nps_boundary"
        outputGDBFeatureClassName = "unit_bounds_wgs"
        tempDissolveFeatureClassName = "lands_dissolve"
        tempMergedFeatureClassName = "lands_merged"
        tempLayer = "tempLayer"
        altLayer = "altLayer"
        affLayer = "affLayer"
        mergeLayer = "mergeLayer"
        outputLandsFeatureClass = os.path.join(parameters[1].valueAsText, outputLandsFeatureClassName)
        outputGDBFeatureClass = os.path.join(parameters[1].valueAsText, outputGDBFeatureClassName)
        tempDissolveFeatureClass = os.path.join(parameters[1].valueAsText, tempDissolveFeatureClassName)
        tempMergedFeatureClass = os.path.join(parameters[1].valueAsText, tempMergedFeatureClassName)
        metadataTemplate = r''
        altFeatureClass = parameters[2].valueAsText
        affFeatureClass = parameters[3].valueAsText
        outSR = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'

        unitsToDelete = [
            'UNIT_CODE = \'ALKA\'',
            'UNIT_CODE = \'AMME\'',
            'UNIT_CODE = \'BICA\'',
            'UNIT_CODE = \'HAVO\'',
            'UNIT_CODE = \'KLGO\'',
            'UNIT_CODE = \'LAKE\'',
            'UNIT_CODE = \'NPSA\'',
            'UNIT_CODE = \'VALR\'',
            'UNIT_CODE = \'WAPA\''
        ]

        # Dissolve nps_boundary.shp to remove lingering single-part features
        arcpy.CopyFeatures_management(parameters[0].valueAsText, outputLandsFeatureClass); messages.addGPMessages()
        arcpy.Dissolve_management(parameters[0].valueAsText, tempDissolveFeatureClass, "UNIT_CODE;UNIT_NAME;UNIT_TYPE;DATE_EDIT;GIS_NOTES", "#", "MULTI_PART"); messages.addGPMessages()
        arcpy.RepairGeometry_management(tempDissolveFeatureClass); messages.addGPMessages()

        # Prepare feature layer for use in selection and delete features replaced by AlternateBounds features.
        arcpy.MakeFeatureLayer_management(tempDissolveFeatureClass, tempLayer); messages.addGPMessages()
        arcpy.AddMessage('\n' + str(unitsToDelete) +  '\n')
        for item, stmt in enumerate(unitsToDelete):
            UpdateUnitBounds.deleteUnit(self, tempLayer, stmt)
            #deleteUnit(self, tempLayer, stmt)
        arcpy.RepairGeometry_management(tempLayer); messages.addGPMessages()

        # Update Feature_Source and Source_Metadata attributes
        arcpy.AddField_management(tempLayer,"Feature_Source","TEXT","#","#",80,"#","NULLABLE", "#", "Feature_Source"); messages.addGPMessages()
        arcpy.AddField_management(tempLayer,"Source_Metadata","TEXT","#","#",100,"#","NULLABLE", "#"); messages.addGPMessages()
        arcpy.AddField_management(tempLayer,"Source_Details","TEXT","#","#",120,"#","NULLABLE", "#"); messages.addGPMessages()

        UpdateUnitBounds.calcField(self, tempLayer, "Feature_Source", 'GIS_Notes LIKE \'LEGACY%\'', '"Legacy Sources"')
        UpdateUnitBounds.calcField(self, tempLayer, "Feature_Source", 'GIS_Notes LIKE \'Lands%\'', '"NPS Land Resources Division"', None, "Source_Metadata", 'GIS_Notes LIKE \'Lands%\'', '"https://irma.nps.gov/App/Reference/Profile/2194483?lnv=true"')
        UpdateUnitBounds.calcField(self, tempLayer, "Feature_Source",  'GIS_Notes LIKE \'Lands%\' OR GIS_Notes LIKE \'LEGACY%\'', '"NPS Inventory and Monitoring Division - Central Office"', 1)
        arcpy.CalculateField_management(tempLayer, "Source_Details", '!GIS_Notes!', 'PYTHON_9.3'); messages.addGPMessages()

        # Prepare feature layers for alternate bounds and affiliated areas
        arcpy.MakeFeatureLayer_management(altFeatureClass, altLayer); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(affFeatureClass, affLayer); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(affLayer,"NEW_SELECTION", "UNIT_CODE <> 'AMME' AND UNIT_CODE <> 'IATR'"); messages.addGPMessages()
        arcpy.DeleteField_management(tempLayer,["GIS_Notes"]); messages.addGPMessages()

        # Merge in alternate bounds and affiliated areas, Remove extraneous fields
        arcpy.Merge_management([tempLayer, altLayer, affLayer], tempMergedFeatureClass); messages.addGPMessages()
        arcpy.RepairGeometry_management(tempMergedFeatureClass); messages.addGPMessages()
        arcpy.DeleteField_management(tempMergedFeatureClass,["STATE","REGION","CREATED_BY","METADATA","PARKNAME","Full_Name","UNIT_TYPE"]); messages.addGPMessages()
        arcpy.AddField_management(tempMergedFeatureClass,"Full_Name","TEXT","#","#",100,"#","NULLABLE", "#"); messages.addGPMessages()
        expression = '!UNIT_NAME!'
        arcpy.CalculateField_management(tempMergedFeatureClass, "Full_Name", expression, "PYTHON"); messages.addGPMessages()

        # Update Feature_Source and Source_Metadata attributes for merged features
        arcpy.MakeFeatureLayer_management(tempMergedFeatureClass, mergeLayer); messages.addGPMessages()
        UpdateUnitBounds.calcField(self, mergeLayer, "Feature_Source", 'Source_Details LIKE \'Good%\'', '"Legacy Sources"')
        UpdateUnitBounds.calcField(self, mergeLayer, "Feature_Source", 'Feature_Source IS Null', '"NPS Inventory and Monitoring Division - Central Office"')

        # Delete older versions
        workspace = parameters[1].valueAsText
        arcpy.env.workspace = workspace
        fcs = arcpy.ListFeatureClasses('unit_bounds_wgs_2*', "Polygon"); messages.addGPMessages()
        for fc in fcs:
            arcpy.Delete_management(fc); messages.addGPMessages()

        # Version existing feature class; Project new feature class and import metadata
        if arcpy.Exists(outputGDBFeatureClass):
            arcpy.Rename_management(outputGDBFeatureClass, outputGDBFeatureClass+ '_' + datestamp); messages.addGPMessages()
        arcpy.Project_management(tempMergedFeatureClass, outputGDBFeatureClass, outSR); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClass); messages.addGPMessages()

        #arcpy.MetadataImporter_conversion(metadataTemplate ,outputGDBFeatureClass); messages.addGPMessages()

        itemsToDelete = [tempLayer, mergeLayer, altLayer, affLayer, tempDissolveFeatureClass, tempMergedFeatureClass]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()


