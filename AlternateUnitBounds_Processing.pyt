#-------------------------------------------------------------------------------

#   AlternateUnitBounds_Processing.pyt
#
#   Cross-check IMD parks with Lands nps_boundary.shp
#   and create
#   UnitBounds_Processing.gdb/tbl_MissingFromLands
#   or tbl_IMDParksUpdated tables.
#   Create
#
#
#   Prerequisites/Inputs:
#       ArcGIS 10.2.2 or higher
#       Source nps_boundary.shp fron Lands
#           https://irma.nps.gov/App/Reference/Profile/2194483?lnv=true
#       XML metadata template in known subfolder (<somewhere>/Templates/Metadata)
#       Output Folder/Workspace
#
#   Outputs:
#       One of two file geodatabases tables: tbl_MissingFromLands or
#       tbl_IMDParksUpdated in
#       UnitBounds.gdb
#
#   Created by:  NPS Inventory and Monitoring Division GIS Staff
#   Update date: 20150821
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
        self.label = "AlternateUnitBounds_Processing"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [FindMissingBounds, FindUpdatedIMDParks]

class FindMissingBounds(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Bounds Missing from Lands"
        self.description = "Create tbl_MissingFromLands table in UnitBounds.gdb"
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
            displayName = "IMD Bounds Lookup Table",
            name = "altBounds",
            datatype = "DETable",
            parameterType = "Required",
            direction = "Input"
            )
        param2.value = "X:\ProjectData\Data_Processing\Bounds_Processing\Data\IMD_Bounds.gdb\IM_Parks_20150813" #"D:\Workspace\IMD_Bounds.gdb\IM_Parks_20150813"

        params = [param0, param1, param2]
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

    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1
        outputMissingTableName = "tbl_MissingFromLands"
        tempLayer = "tempLayer"
        lookupTable = "lookupTable"
        outputMissingTable = os.path.join(parameters[1].valueAsText, outputMissingTableName + '_' + datestamp)

        # Join lookup to nps_boundary.shp and copy missing records to tbl_MissingFromLands
        arcpy.MakeFeatureLayer_management(parameters[0].valueAsText, tempLayer); messages.addGPMessages()
        arcpy.MakeTableView_management(parameters[2].valueAsText, lookupTable); messages.addGPMessages()
        arcpy.AddJoin_management(lookupTable, "Unit_Code", tempLayer , "UNIT_CODE"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(lookupTable, "NEW_SELECTION", "nps_boundary.UNIT_CODE IS NULL"); messages.addGPMessages()

        #arcpy.SelectLayerByAttribute_management(in_layer_or_view="IM_Parks_20150813",selection_type="NEW_SELECTION",where_clause=""""nps_boundary.UNIT_CODE" IS NULL""")
        arcpy.CopyRows_management(lookupTable, outputMissingTable); messages.addGPMessages()
        arcpy.RemoveJoin_management(lookupTable); messages.addGPMessages()

        itemsToDelete = [tempLayer, lookupTable]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()

class FindUpdatedIMDParks(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Updated IMD Parks"
        self.description = "Create tbl_UpdatedIMDParks table in UnitBounds.gdb"
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
            displayName = "IMD Bounds Lookup Table",
            name = "altBounds",
            datatype = "DETable",
            parameterType = "Required",
            direction = "Input"
            )
        param2.value = "X:\ProjectData\Data_Processing\Bounds_Processing\Data\IMD_Bounds.gdb\IM_Parks_20150813" #"D:\Workspace\IMD_Bounds.gdb\IM_Parks_20150813"

        param3 = arcpy.Parameter(
            displayName = "Date to Check",
            name = "dateCheck",
            datatype = "GPDate",
            parameterType = "Required",
            direction = "Input"
            )

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

    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1
        outputUpdatedTableName = "tbl_IMDParksUpdated"
        tempLayer = "tempLayer"
        lookupTable = "lookupTable"
        outputUpdatedTable = os.path.join(parameters[1].valueAsText, outputUpdatedTableName + '_' + datestamp)
        checkDate = "date '" + parameters[3].value.strftime('%Y-%m-%d') + "'"
        arcpy.AddMessage("\ncheckDate = " + checkDate)
        selectQuery = '"nps_boundary.DATE_EDIT" >= %s' % checkDate
        arcpy.AddMessage("\nselectQuery = " + selectQuery)

        # Join lookup to nps_boundary.shp and copy missing records to tbl_MissingFromLands
        arcpy.MakeFeatureLayer_management(parameters[0].valueAsText, tempLayer); messages.addGPMessages()
        arcpy.MakeTableView_management(parameters[2].valueAsText, lookupTable); messages.addGPMessages()
        arcpy.AddJoin_management(lookupTable, "Unit_Code", tempLayer , "UNIT_CODE"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(lookupTable, "NEW_SELECTION", "nps_boundary.UNIT_CODE IS NOT NULL"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(lookupTable, "SUBSET_SELECTION", selectQuery); messages.addGPMessages()

        #arcpy.SelectLayerByAttribute_management(in_layer_or_view="IM_Parks_20150813",selection_type="NEW_SELECTION",where_clause=""""nps_boundary.UNIT_CODE" IS NULL""")
        arcpy.CopyRows_management(lookupTable, outputUpdatedTable); messages.addGPMessages()
        arcpy.RemoveJoin_management(lookupTable); messages.addGPMessages()

        itemsToDelete = [tempLayer, lookupTable]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()


