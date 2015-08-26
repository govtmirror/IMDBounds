#-------------------------------------------------------------------------------

#   NPScapeBounds_Processing.pyt
#
#   Create or update NPScape_Bounds.gdb/npscape_bounds_albers, npscape_bounds_webmercator, and
#   npscape_bounds_webmercator_convexhulls feature classes.
#   Create or update feature classes in Alaska, CONUS, and Pacific
#   feature datasets.
#
#
#   Prerequisites/Inputs:
#       ArcGIS 10.2.2 or higher
#       Source IMDBounds.gdb\imd_unit_bounds_albers feature class
#
#       XML metadata template in known subfolder (<somewhere>/Templates/Metadata)
#       Output Folder/Workspace
#
#   Outputs:
#       Three feature class at the GDB root: npscape_bounds_albers, npscape_bounds_webmercator, and
#       npscape_bounds_webmercator_convexhulls
#
#       Feature classes in each feature dataset with polygons specific to that extent.
#
#   Created by:  NPS Inventory and Monitoring Division GIS Staff
#   Update date: 20150824
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
        self.label = "NPScapeBounds_Processing"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [UpdateNPScapeBounds]

class UpdateNPScapeBounds(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update NPScape Bounds"
        self.description = "Create or update NPScape Bounds feature classes in NPScape_Bounds.gdb"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName = "Source Unit Bounds Feature Class - Albers",
            name = "albersBounds",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        #param0.value = "D:\Workspace\IMD_Bounds.gdb\imd_unit_bounds_albers"

        param1 = arcpy.Parameter(
            displayName = "Source Unit Bounds Feature Class - WebMercator",
            name = "webMercBounds",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        #param1.value = "D:\Workspace\IMD_Bounds.gdb\imd_unit_bounds_webmercator"

        param2 = arcpy.Parameter(
            displayName = "Output GeoDatabase",
            name = "outDB",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input")

        param3 = arcpy.Parameter(
            displayName = "IMD Bounds Lookup Table",
            name = "altBounds",
            datatype = "DETable",
            parameterType = "Required",
            direction = "Input"
            )
        param3.value = "D:\Workspace\NPScape_Bounds.gdb\NPScape_Parks_20150824"

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

    def projectDataset(self, sourceDataset, outpuDataset, outputSpatialRef, transform=None):
        """
            Re-projects and repairs source dataset
        """
        arcpy.Project_management(sourceDataset, outpuDataset, outputSpatialRef, transform)
        arcpy.RepairGeometry_management(outpuDataset)
        arcpy.AddMessage('\n Re-projected to '  + outpuDataset)

    def populateDatasets(self, targetLayer, targetDataset, selectClause, outputFC):
        arcpy.SelectLayerByAttribute_management(targetLayer, "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management(targetLayer, "NEW_SELECTION", "UNIT_CODE IN ("+ selectClause+")")
        arcpy.CopyFeatures_management(targetLayer, outputFC)
        arcpy.SelectLayerByAttribute_management(targetLayer, "CLEAR_SELECTION")
        arcpy.RepairGeometry_management(outputFC)
        arcpy.AddMessage('\n Created '  + outputFC)

    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]

        arcpy.env.overwriteOutput = 1
        # Lands bounds have M and Z values for some reason; this is an extra check
        # since M and Z are disabled in the UnitBounds_Processing UpdateUnitBounds tool
        arcpy.env.outputMFlag = "Disabled"
        arcpy.env.outputZFlag = "Disabled"
        outputInitTempFeatureClassName = "temp_npscape_bounds0"
        outputTempFeatureClassName = "temp_npscape_bounds"
        outputGDBFeatureClassName = "npscape_bounds"
        tempLayer = "tempLayer"
        lookupTable = "lookupTable"
        tableName = parameters[3].valueAsText[(parameters[3].valueAsText).rfind(".gdb")+5:]
        selectClause = "UNIT_CODE IN (SELECT UNIT_CODE FROM " +tableName + ")"
        outputGDBFeatureClassInitTemp = os.path.join(parameters[2].valueAsText, outputInitTempFeatureClassName)
        outputGDBFeatureClassTemp = os.path.join(parameters[2].valueAsText, outputTempFeatureClassName)
        outputGDBFeatureClassAlbers = os.path.join(parameters[2].valueAsText, outputGDBFeatureClassName + "_albers")
        outputGDBFeatureClassWebMerc = os.path.join(parameters[2].valueAsText, outputGDBFeatureClassName + "_webmercator")
        outputGDBFeatureClassConvexHulls = os.path.join(parameters[2].valueAsText, outputGDBFeatureClassName + "_webmercator_convexhulls")

        outputGDBFeatureClassAlaska = os.path.join(parameters[2].valueAsText, "Alaska\\" + outputGDBFeatureClassName + "_Alaska")
        outputGDBFeatureClassHawaii = os.path.join(parameters[2].valueAsText, "Hawaii\\" + outputGDBFeatureClassName + "_Hawaii")
        outputGDBFeatureClassSaipan = os.path.join(parameters[2].valueAsText, "Pacific_Saipan_Guam\\" + outputGDBFeatureClassName + "_Saipan_Guam")
        outputGDBFeatureClassSamoa = os.path.join(parameters[2].valueAsText, "Pacific_Samoa\\" + outputGDBFeatureClassName + "_Samoa")
        outputGDBFeatureClassCONUS = os.path.join(parameters[2].valueAsText, "CONUS\\" + outputGDBFeatureClassName + "_CONUS")

        AllUnits = [
            'ABLI', 'ACAD', 'AGFO', 'ALAG', 'ALFL', 'ALKA', 'ALPO', 'AMIS', 'AMME', 'ANAC', 'ANIA', 'ANTI', 'APPA', 'APCO', 'APIS', 'ARCH', 'ARPO', 'ASIS', 'AZRU',
            'BADL', 'BAND', 'BAWA', 'BELA', 'BEOL', 'BIBE', 'BICA', 'BICY', 'BIHO', 'BISC', 'BISO', 'BITH', 'BLCA', 'BLRI', 'BLUE', 'BOHA', 'BOWA',
            'BRCA', 'BUFF', 'BUIS', 'CABR', 'CACH', 'CACO', 'CAGR', 'CAHA', 'CAHE', 'CAKR', 'CALO', 'CANA', 'CANY', 'CARE', 'CARL', 'CASA', 'CATO',
            'CAVE', 'CAVO', 'CEBR', 'CHAT', 'CHCH', 'CHCU', 'CHIC', 'CHIR', 'CHIS', 'CHOH', 'CHPI', 'CIRO', 'COLM', 'COLO', 'CORO', 'CONG', 'COWP',
            'CRLA', 'CRMO', 'CUGA', 'CUIS', 'CURE', 'CUVA', 'DENA', 'DEPO', 'DETO', 'DEVA', 'DEWA', 'DINO', 'DRTO', 'EBLA', 'EFMO', 'EISE', 'ELMA',
            'ELMO', 'EUON', 'EVER', 'FIIS', 'FLFO', 'FOBO', 'FOBU', 'FOCA', 'FODA', 'FODO', 'FOFR', 'FOLA', 'FOLS', 'FOMA', 'FOMO', 'FONE',
            'FOPO', 'FOPU', 'FORA', 'FOSU', 'FOUN', 'FOUS', 'FOVA', 'FOWA', 'FRDO', 'FRHI', 'FRSP', 'GAAR', 'GARI', 'GATE', 'GETT', 'GEWA', 'GICL',
            'GLAC', 'GLBA', 'GLCA', 'GOGA', 'GOSP', 'GRBA', 'GRCA', 'GREE', 'GRKO', 'GRPO', 'GRSA', 'GRSM', 'GRTE', 'GUCO', 'GUIS', 'GUMO', 'GWCA',
            'GWMP', 'HAFE', 'HAFO', 'HALE', 'HAVO', 'HEHO', 'HOBE', 'HOCU', 'HOFU', 'HOME', 'HOSP', 'HOVE', 'HUTR', 'INDU', 'ISRO',
            'JECA', 'JELA', 'JODA', 'JOFL', 'JOMU', 'JOTR', 'KAHO', 'KALA', 'KATM', 'KEFJ', 'KEMO', 'KIMO', 'KLGO', 'KNRI', 'KOVA', 'LABE',
            'LACL', 'LAKE', 'LAMR', 'LARO', 'LAVO', 'LEWI', 'LIBI', 'LIBO', 'LIRI', 'LYJO', 'MABE', 'MABI', 'MACA', 'MANA', 'MANZ', 'MEVE', 'MIMA',
            'MISS', 'MNRR', 'MOCA', 'MOCR', 'MOJA', 'MONO', 'MORA', 'MORR', 'MORU', 'MUWO', 'NABR', 'NACE', 'NATR', 'NAVA', 'NEPE', 'NERI', 'NIOB',
            'NISI', 'NOAT', 'NOCA', 'NPSA', 'OBRI', 'OCMU', 'OLYM', 'ORCA', 'ORPI', 'OZAR', 'PAAL', 'PAIS', 'PARA', 'PECO', 'PEFO', 'PERI', 'PETE', 'PETR',
            'PINN', 'PIPE', 'PIRO', 'PISC', 'PISP', 'POCH', 'PORE', 'PRSF', 'PRWI', 'PUHE', 'PUHO', 'RABR', 'REDW', 'RICH', 'RIGR', 'ROCR', 'ROMO',
            'ROVA', 'RUCA', 'SAAN', 'SACN', 'SAGA', 'SAGU', 'SAHI', 'SAIR', 'SAJH', 'SAMO', 'SAND', 'SAPU', 'SARA', 'SCBL', 'SEKI',
            'SHEN', 'SHIL', 'SITK', 'SLBE', 'STRI', 'SUCR', 'TAPR', 'THRO', 'THST', 'TICA', 'TIMU', 'TONT', 'TUMA', 'TUZI', 'UPDE', 'VALR', 'VAFO',
            'VICK', 'VIIS', 'VOYA', 'WABA', 'WACA', 'WAPA', 'WEFA', 'WHIS', 'WHMI', 'WHSA', 'WICA', 'WICR', 'WOTR', 'WRBR', 'WRST', 'WUPA',
            'YELL', 'YOSE', 'YUCH', 'YUHO', 'ZION']


        Alaska_Parks = "'ALAG','ANIA','BELA','CAKR','DENA','GAAR','GLBA','KATM','KEFJ','KOVA','KLGO','LACL','NOAT','SITK','YUCH','WRST'"
        Hawaii_Parks = "'ALKA','HALE','KALA','KAHO','HAVO','PUHE','PUHO','VALR'"
        PacificSaipan_Parks = "'AMME','WAPA'"
        PacificSamoa_Parks= "'NPSA'"
        Alaska_Parks_Array = ['ALAG','ANIA','BELA','CAKR','DENA','GAAR','GLBA','KATM','KEFJ','KOVA','KLGO','LACL','NOAT','SITK','YUCH','WRST']
        Hawaii_Parks_Array = ['ALKA','HALE','KALA','KAHO','HAVO','PUHE','PUHO','VALR']
        PacificSaipan_Parks_Array = ['AMME','WAPA']
        PacificSamoa_Parks_Array = ['NPSA']

        # Delete older versions
        fcsToDelete = [outputGDBFeatureClassName + '_albers_2*',
                        outputGDBFeatureClassName + '_webmercator_2*',
                        outputGDBFeatureClassName + '_webmercator_convexhulls_2*']

        workspace = parameters[2].valueAsText
        arcpy.env.workspace = workspace
        for fc in fcsToDelete:
            fcs = arcpy.ListFeatureClasses(fc, "Polygon")
            for fcc in fcs:
                arcpy.Delete_management(fcc); messages.addGPMessages()

        # Version existing feature classes; Project tp new feature classes
        fcsToVersion = [outputGDBFeatureClassAlbers,
                outputGDBFeatureClassWebMerc,
                outputGDBFeatureClassConvexHulls]

        for fc in fcsToVersion:
            if arcpy.Exists(fc):
                arcpy.Rename_management(fc, fc + '_' + datestamp); messages.addGPMessages()

        # Join lookup to unit_bounds_wgs and copy matching features to temp feature class
        arcpy.FeatureClassToFeatureClass_conversion(parameters[0].valueAsText, parameters[2].valueAsText, outputInitTempFeatureClassName); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(outputGDBFeatureClassInitTemp, tempLayer); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer,"NEW_SELECTION", selectClause); messages.addGPMessages()

        arcpy.CopyFeatures_management(tempLayer, outputGDBFeatureClassAlbers); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer,"CLEAR_SELECTION"); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassAlbers); messages.addGPMessages()

        arcpy.CopyFeatures_management(tempLayer, outputGDBFeatureClassTemp); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassTemp); messages.addGPMessages()

        arcpy.FeatureClassToFeatureClass_conversion(parameters[1].valueAsText, parameters[2].valueAsText, outputInitTempFeatureClassName); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(outputGDBFeatureClassInitTemp, tempLayer); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer,"NEW_SELECTION", selectClause); messages.addGPMessages()
        arcpy.CopyFeatures_management(tempLayer, outputGDBFeatureClassWebMerc); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer,"CLEAR_SELECTION"); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassWebMerc); messages.addGPMessages()

        # Create convex hull feature class
        arcpy.MinimumBoundingGeometry_management(outputGDBFeatureClassWebMerc, outputGDBFeatureClassConvexHulls, "CONVEX_HULL"); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassConvexHulls); messages.addGPMessages()

        # Create feature classes in feature datasets:
        arcpy.Delete_management(tempLayer); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(outputGDBFeatureClassTemp, tempLayer); messages.addGPMessages()

        UpdateNPScapeBounds.populateDatasets(self, tempLayer, "Alaska", Alaska_Parks, outputGDBFeatureClassAlaska)
        UpdateNPScapeBounds.populateDatasets(self, tempLayer, "Hawaii", Hawaii_Parks, outputGDBFeatureClassHawaii)
        UpdateNPScapeBounds.populateDatasets(self, tempLayer, "Pacific_Saipan_Guam", PacificSaipan_Parks, outputGDBFeatureClassSaipan)

        arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", "UNIT_CODE IN ("+ Alaska_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "ADD_TO_SELECTION", "UNIT_CODE IN ("+Hawaii_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "ADD_TO_SELECTION", "UNIT_CODE IN ("+PacificSaipan_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "ADD_TO_SELECTION", "UNIT_CODE IN ("+PacificSamoa_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "SWITCH_SELECTION"); messages.addGPMessages()
        arcpy.CopyFeatures_management(tempLayer, outputGDBFeatureClassCONUS)
        arcpy.SelectLayerByAttribute_management(tempLayer, "CLEAR_SELECTION")
        arcpy.RepairGeometry_management(outputGDBFeatureClassCONUS)

        # Import metadata
        #for fc in fcsToVersion:
            #arcpy.MetadataImporter_conversion(metadataTemplate ,fc); messages.addGPMessages()

        itemsToDelete = [tempLayer, lookupTable, outputGDBFeatureClassTemp, outputGDBFeatureClassInitTemp]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()





