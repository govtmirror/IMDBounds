#-------------------------------------------------------------------------------

#   IMDBounds_Processing.pyt
#
#   Create or update IMD_Bounds.gdb/imd_unit_bounds_albers, imd_unit_bounds_webmercator, and
#   imd_unit_bounds_webmercator_convexhulls feature classes.
#   Create or update feature classes in Alaska, CONUS, and Pacific
#   feature datasets.
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
#       Three feature class at the GDB root: imd_unit_bounds_albers, imd_unit_bounds_webmercator, and
#   imd_unit_bounds_webmercator_convexhulls
#
#       Feature classes in each feature dataset with polygons specific to that extent.
#
#   Created by:  NPS Inventory and Monitoring Division GIS Staff
#   Update date: 20150826
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
        self.label = "IMDBounds_Processing"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [UpdateIMDBounds]

class UpdateIMDBounds(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update IMD Bounds"
        self.description = "Create or update IMD Bounds feature classes in IMDBounds.gdb"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName = "Source Unit Bounds Feature Class",
            name = "unitBounds",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        #param0.value = r"X:\ProjectData\Data_Processing\NPS_Bounds\NPS_Boundary_Source\nps_boundary\nps_boundary.shp"

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
            displayName = "Folder Containing Metadata Templates",
            name = "metaFolder",
            datatype = "Folder",
            parameterType = "Required",
            direction = "Input"
            )
        param3.value = "X:\ProjectData\Data_Processing\Bounds_Processing\Metadata_Templates"

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

    def updateNames(self, targetLayer, selectClause, targetFields):
        tempNameLayer = "tempNameLayer"
        arcpy.MakeFeatureLayer_management(targetLayer, tempNameLayer)
        arcpy.SelectLayerByAttribute_management(tempNameLayer, "NEW_SELECTION", "UNIT_CODE = '"+ selectClause +"'")
        for targetField in targetFields:
            updatedValue = "!"  + targetField + "! + ' and Preserve'"
            arcpy.CalculateField_management(tempNameLayer, targetField,  updatedValue, "PYTHON_9.3")
        #arcpy.CalculateField_management(in_table="imd_unit_bounds_albers",field="UNIT_NAME",expression="!UNIT_NAME! + ' and Preserve'",expression_type="PYTHON_9.3",code_block="#")
        arcpy.SelectLayerByAttribute_management(tempNameLayer, "CLEAR_SELECTION")
        arcpy.AddMessage('\n Updated Names: ' + selectClause + ' for '  + targetLayer)

    def execute(self, parameters, messages):
        message = ""
        today=datetime.now()
        datestamp = str(today.isoformat()).replace('-','')[0:8]
        metadataTemplates = ["imdbounds_albers_template.xml","imdbounds_albers_template.xml", "imdbounds_generic_template.xml"]

        arcpy.env.overwriteOutput = 1
        # Lands bounds have M and Z values for some reason; this is an extra check
        # since M and Z are disabled in the UnitBounds_Processing UpdateUnitBounds tool
        arcpy.env.outputMFlag = "Disabled"
        arcpy.env.outputZFlag = "Disabled"
        outputInitTempFeatureClassName = "temp_unit_bounds_wgs0"
        outputTempFeatureClassName = "temp_unit_bounds_wgs"
        outputTempDissolveFeatureClassName = "temp_dissolved_unit_bounds_wgs"
        outputGDBFeatureClassName = "imd_unit_bounds"
        tempLayer = "tempLayer"
        lookupTable = "lookupTable"
        outputGDBFeatureClassInitTemp = os.path.join(parameters[1].valueAsText, outputInitTempFeatureClassName)
        outputGDBFeatureClassTemp = os.path.join(parameters[1].valueAsText, outputTempFeatureClassName)
        outputGDBFeatureClassTempDissolve = os.path.join(parameters[1].valueAsText, outputTempDissolveFeatureClassName)
        outputGDBFeatureClassAlbers = os.path.join(parameters[1].valueAsText, outputGDBFeatureClassName + "_albers")
        outputGDBFeatureClassWebMerc = os.path.join(parameters[1].valueAsText, outputGDBFeatureClassName + "_webmercator")
        outputGDBFeatureClassConvexHulls = os.path.join(parameters[1].valueAsText, outputGDBFeatureClassName + "_webmercator_convexhulls")

        outputGDBFeatureClassAlaska = os.path.join(parameters[1].valueAsText, "Alaska\\" + outputGDBFeatureClassName + "_Alaska")
        outputGDBFeatureClassHawaii = os.path.join(parameters[1].valueAsText, "Hawaii\\" + outputGDBFeatureClassName + "_Hawaii")
        outputGDBFeatureClassSaipan = os.path.join(parameters[1].valueAsText, "Pacific_Saipan_Guam\\" + outputGDBFeatureClassName + "_Saipan_Guam")
        outputGDBFeatureClassSamoa = os.path.join(parameters[1].valueAsText, "Pacific_Samoa\\" + outputGDBFeatureClassName + "_Samoa")
        outputGDBFeatureClassCONUS = os.path.join(parameters[1].valueAsText, "CONUS\\" + outputGDBFeatureClassName + "_CONUS")

        outSRAlbers = 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic_USGS_version",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],PARAMETER["Latitude_Of_Origin",23.0],UNIT["Meter",1.0]]", "NAD_1983_To_WGS_1984_4", "GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]")'
        outSRWebMerc = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]'
        transformMethod = "NAD_1983_To_WGS_1984_5"

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
        Conus_Select_Array0 = [Alaska_Parks_Array,Hawaii_Parks_Array,PacificSaipan_Parks_Array,PacificSamoa_Parks_Array]
        Conus_Select_Array = [ y for x in Conus_Select_Array0 for y in x]
        for unit in Conus_Select_Array:
            AllUnits.remove(unit)

        UpdateNames_Array = ['ALAG','ANIA','DENA','GAAR','GLBA','KATM','LACL','WRST','GRSA']
        #updatedNames = {'ANIA': 'Aniakchak National Monument and Preserve','DENA': 'Denali National Park and Preserve','GAAR': 'Gates of the Arctic National Park and Preserve','GLBA': 'Glacier Bay National Park and Preserve','KATM': 'Katmai National Park and Preserve','LACL': 'Lake Clark National Park and Preserve','WRST': 'Wrangell-St. Elias National Park','GRSA': 'Great Sand Dunes National Park and Preserve'}

        # Join lookup to unit_bounds_wgs and copy matching features to temp feature class
        arcpy.FeatureClassToFeatureClass_conversion(parameters[0].valueAsText, parameters[1].valueAsText, outputInitTempFeatureClassName); messages.addGPMessages()
        arcpy.MakeFeatureLayer_management(outputGDBFeatureClassInitTemp, tempLayer); messages.addGPMessages()
        arcpy.MakeTableView_management(parameters[2].valueAsText, lookupTable); messages.addGPMessages()
        arcpy.JoinField_management(tempLayer, "UNIT_CODE", lookupTable, "Unit_Code", ["Network_Code", "Lifecycle"]); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", "Network_Code IS NOT NULL"); messages.addGPMessages()
        arcpy.Dissolve_management(tempLayer, outputGDBFeatureClassTempDissolve, "UNIT_CODE"); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassTempDissolve); messages.addGPMessages()
        arcpy.JoinField_management(outputGDBFeatureClassTempDissolve, "UNIT_CODE", tempLayer, "UNIT_CODE", ["UNIT_NAME","DATE_EDIT", "Full_Name", "Feature_Source","Source_Metadata","Source_Details","Network_Code","Lifecycle"]); messages.addGPMessages()
        arcpy.CopyFeatures_management(outputGDBFeatureClassTempDissolve, outputGDBFeatureClassTemp); messages.addGPMessages()
        #arcpy.CopyFeatures_management(tempLayer, outputGDBFeatureClassTemp); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassTemp); messages.addGPMessages()

        # Update names for logical (dissolved) parks
        for unitCode in UpdateNames_Array:
            UpdateIMDBounds.updateNames(self, outputGDBFeatureClassTemp, unitCode, ["UNIT_NAME", "Full_Name"])

        # Delete older versions
        fcsToDelete = [outputGDBFeatureClassName + '_albers' + '_2*',
                        outputGDBFeatureClassName + '_webmercator' + '_2*',
                        outputGDBFeatureClassName + '_webmercator_convexhulls' + '_2*']

        workspace = parameters[1].valueAsText
        arcpy.env.workspace = workspace
        for fc in fcsToDelete:
            fcs = arcpy.ListFeatureClasses(fc, "Polygon"); messages.addGPMessages()
            for fcc in fcs:
                arcpy.Delete_management(fcc); messages.addGPMessages()

        # Version existing feature classes; Project tp new feature classes
        fcsToVersion = [outputGDBFeatureClassAlbers,
                outputGDBFeatureClassWebMerc,
                outputGDBFeatureClassConvexHulls]

        for fc in fcsToVersion:
            if arcpy.Exists(fc):
                arcpy.Rename_management(fc, fc + '_' + datestamp); messages.addGPMessages()

        UpdateIMDBounds.projectDataset(self, outputGDBFeatureClassTemp, outputGDBFeatureClassAlbers, outSRAlbers, transformMethod)
        UpdateIMDBounds.projectDataset(self, outputGDBFeatureClassTemp, outputGDBFeatureClassWebMerc, outSRWebMerc)

        # Create convex hull feature class
        arcpy.MinimumBoundingGeometry_management(outputGDBFeatureClassWebMerc, outputGDBFeatureClassConvexHulls, "CONVEX_HULL"); messages.addGPMessages()
        arcpy.RepairGeometry_management(outputGDBFeatureClassConvexHulls); messages.addGPMessages()

        # Create feature classes in feature datasets:
        arcpy.MakeFeatureLayer_management(outputGDBFeatureClassTemp, tempLayer); messages.addGPMessages()

        UpdateIMDBounds.populateDatasets(self, tempLayer, "Alaska", Alaska_Parks, outputGDBFeatureClassAlaska)
        UpdateIMDBounds.populateDatasets(self, tempLayer, "Hawaii", Hawaii_Parks, outputGDBFeatureClassHawaii)
        UpdateIMDBounds.populateDatasets(self, tempLayer, "Pacific_Saipan_Guam", PacificSaipan_Parks, outputGDBFeatureClassSaipan)
        UpdateIMDBounds.populateDatasets(self, tempLayer, "Pacific_Samoa", PacificSamoa_Parks, outputGDBFeatureClassSamoa)

        arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", "UNIT_CODE IN ("+ Alaska_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "ADD_TO_SELECTION", "UNIT_CODE IN ("+Hawaii_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "ADD_TO_SELECTION", "UNIT_CODE IN ("+PacificSaipan_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "ADD_TO_SELECTION", "UNIT_CODE IN ("+PacificSamoa_Parks+")"); messages.addGPMessages()
        arcpy.SelectLayerByAttribute_management(tempLayer, "SWITCH_SELECTION"); messages.addGPMessages()
        arcpy.CopyFeatures_management(tempLayer, outputGDBFeatureClassCONUS)
        arcpy.SelectLayerByAttribute_management(tempLayer, "CLEAR_SELECTION")
        arcpy.RepairGeometry_management(outputGDBFeatureClassCONUS)

        # Import metadata
        for fc in fcsToVersion:
            if fc.endswith("_albers"):
                arcpy.MetadataImporter_conversion(os.path.join(parameters[3].valueAsText, metadataTemplates[0]), fc); messages.addGPMessages()
            elif fc.endswith("_webercator"):
                arcpy.MetadataImporter_conversion(os.path.join(parameters[3].valueAsText, metadataTemplates[1]), fc); messages.addGPMessages()
            else:
                pass

        fcsInDatasets = [outputGDBFeatureClassAlaska, outputGDBFeatureClassHawaii, outputGDBFeatureClassSaipan, outputGDBFeatureClassSamoa, outputGDBFeatureClassCONUS]
        for fc in fcsInDatasets:
            arcpy.MetadataImporter_conversion(os.path.join(parameters[3].valueAsText, metadataTemplates[2]), fc); messages.addGPMessages()

        itemsToDelete = [tempLayer, lookupTable, outputGDBFeatureClassTemp, outputGDBFeatureClassInitTemp, outputGDBFeatureClassTempDissolve]
        for item in itemsToDelete:
            if arcpy.Exists(item):
                arcpy.Delete_management(item); messages.addGPMessages()





