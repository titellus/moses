from qgis.core import *
from qgis.utils import *

import re
import os


# Mapfile builder is used to create a mapfile
class MapfileBuilder:
  HEADER = """MAP
    NAME "{projectName}"
    EXTENT -180 -90 180 90
    UNITS DD
    IMAGETYPE PNGA
    SYMBOLSET "symbol/symbols.txt"
    FONTSET "fonts/fonts.txt"
  
    OUTPUTFORMAT
      NAME "PNGA"
      DRIVER "AGG/PNG"
      MIMETYPE "image/png"
      IMAGEMODE RGBA
      EXTENSION "png"
      FORMATOPTION "INTERLACE=OFF"
    END
  
    OUTPUTFORMAT
      NAME "PNG-8"
      DRIVER "GD/PNG"
      MIMETYPE "image/png"
      IMAGEMODE PC256
      EXTENSION "png"
      FORMATOPTION "INTERLACE=OFF"
    END
  
    OUTPUTFORMAT
      NAME jpeg
      DRIVER AGG/JPEG
      MIMETYPE "image/jpeg"
      IMAGEMODE RGB
      EXTENSION "jpg"
      FORMATOPTION "INTERLACE=OFF"
      FORMATOPTION "QUALITY=80"
    END
  
    WEB
      IMAGEPATH "/var/www/mapserver/tmp/"
      METADATA
        wms_title "{projectName}"
        wms_onlineresource "http://www.ifremer.fr/services/wms/moses"
        wms_srs "CRS:84 EPSG:4326 EPSG:27582 EPSG:3395 EPSG:2154 EPSG:3857"
        wms_abstract "Web Map Service for MOSES"
        wms_accessconstraints "None"
        wms_contactperson "Equipe Sextant"
        wms_contactelectronicmailaddress "sextant@ifremer.fr"
        wms_contactorganization "Ifremer"
        wms_contactposition "distributor"
        wms_keywordlist "MOSES, Sextant, Inspire, OGC, WMS, Ifremer, océan, ISO"
        wms_fees "conditions unknown"
        wms_inspire_view_service "true"
        wms_enable_request "*"
        wms_encoding "ISO-8859-15"
        wms_inspire_temporal_reference "2013-08-14"
        wms_inspire_mpoc_name "Equipe Sextant"
        wms_inspire_resourcelocator "http://www.ifremer.fr/services/wms/moses"
        wms_inspire_mpoc_email "sextant@ifremer.fr"
        wms_inspire_capabilities "url"
        wms_inspire_keyword "infoMapAccessService"
        wms_inspire_SpatialDataServiceType "view"
      END
    END
  
    LEGEND
      STATUS ON
      KEYSIZE 20 10
      KEYSPACING 12 25
      LABEL
          FONT Arial
          TYPE truetype
          SIZE 8
          COLOR 0 0 89
      END
    END
  
    #  pour l'impression A3
    MAXSIZE 5000
  
    PROJECTION
      "init=epsg:4326"
    END
  
    SYMBOL
      NAME "circle"
      TYPE ellipse
      FILLED true
      POINTS 1 1 END
    END
  """

  LAYER = """
    LAYER
      NAME "{layerCode}"
      TYPE POLYGON
      DUMP TRUE
      STATUS ON      
      EXTENT -180 -90 180 90
      UNITS DD
      
      CONNECTIONTYPE POSTGIS
      CONNECTION "host={dbHost} dbname={dbName} user={dbUsername}
                  password={dbPassword} port={dbPort}"
      DATA "geom FROM (
        SELECT nuts_id, activity_id, indicator_id, year, value, status, data_source, website
        FROM indicator_values v, indicators i, activity a, nuts n
        WHERE
          v.indicator_id = i.id 
          AND v.activity_id = a.id 
          AND v.nuts_id = n.id
          AND n.level = '{level}'
          AND i.id = '{indicator}'
          AND a.id = '{activity}'
          AND v.year = {year})
            AS RS USING UNIQUE n.id USING srid=4326"

      PROJECTION
          "init=epsg:4326"
      END
      
      TEMPLATE "queryable"
      METADATA
        wms_title "{layerCode}"
        wms_name "{layerCode}"
        wms_srs "EPSG:4326" 
        wms_connectiontimeout "120"
        wms_server_version "1.1.1"
        wms_attribution_title "{projectName}"
        wms_include_items "all"
        wms_layer_group "{layerGroup}"        
        gml_include_items "all"
        wms_metadataurl_format "text/xml"
        wms_metadataurl_type "TC211"
        wms_metadataurl_href "{layerMetadataUrl}" 
      END
      
      {categories}
    END
  """

  CATEGORY = """
      CLASS
        NAME "{label}"
        EXPRESSION ({min} <= [value] AND [value] < {max})
        STYLE
          COLOR {color}
          OUTLINECOLOR 0 0 0
        END
      END
      """

  FOOTER = """
END
  """

  def __init__(self, file, projectName, projectDescription, projectUrl):
    self.file = file
    self.projectName = projectName
    self.projectDescription = projectDescription
    self.projectUrl = projectUrl

  # Write the mapfile
  def writeHeader(self):
    mapfile = open(self.file, "w+")
    mapfile.write(self.HEADER.format(projectName=self.projectName,
                                     projectDescription=self.projectDescription,
                                     projectUrl=self.projectUrl))
    mapfile.close()

  def writeLayer(self, layerCode, level, activity, indicator, year, categories, dbHost, dbPort, dbName, dbUsername,
                 dbPassword, dbSchema):
    """

    :rtype: object
    """
    mapfile = open(self.file, "a+")
    categoriesConfig = ""
    for c in categories:
      categoriesConfig = categoriesConfig + self.CATEGORY.format(min=categories[c].min,
                                                                 max=categories[c].max,
                                                                 color=categories[c].color,
                                                                 label=categories[c].label)

    layerConfig = f"" + self.LAYER.format(layerCode=layerCode,
                                          level=level,
                                          layerGroup=activity,
                                          activity=activity,
                                          indicator=indicator,
                                          year=year,
                                          projectName=self.projectName,
                                          layerMetadataUrl="",
                                          dbHost=dbHost,
                                          dbPort=dbPort,
                                          dbName=dbName,
                                          dbUsername=dbUsername,
                                          dbPassword=dbPassword,
                                          dbSchema=dbSchema,
                                          categories=categoriesConfig)
    mapfile.write(layerConfig)
    mapfile.close()

  def writeFooter(self):
    mapfile = open(self.file, "a+")
    mapfile.write(f"" + self.FOOTER)
    mapfile.close()


# Constants
class CONST:
  class LAYERNAME:
    activities = "moses_activities"
    indicators = "moses_indicators"
    ivalue = "moses_indicator_values"
    ivalueview = "moses_indicator_values_with_nuts"


class MosesPublication:
  dbName = 'moses'
  dbHost = 'localhost'
  dbPort = '5432'
  dbUsername = 'www-data'
  dbPassword = 'www-data'
  dbSchema = 'public'

  classificationMethod = "equalInterval"
  classificationNbOfClasses = 5

  # Define color map
  # ['Spectral', 'RdYlGn', 'Set2', 'Accent', 'OrRd', 'Set1', 'PuBu', 'Set3', 'BuPu', 'Dark2', 'RdBu', 'Oranges', 'BuGn', 'PiYG', 'YlOrBr', 'YlGn', 'Reds', 'RdPu', 'Greens', 'PRGn', 'YlGnBu', 'RdYlBu', 'Paired', 'BrBG', 'Purples', 'Pastel2', 'Pastel1', 'GnBu', 'Greys', 'RdGy', 'YlOrRd', 'PuOr', 'PuRd', 'Blues', 'PuBuGn']
  colorScheme = 'Greys'

  palette = QgsColorBrewerColorRamp(
    colors=5,
    schemeName=colorScheme,
    inverted=True)
  palette.loadPalette()

  isBuildingMapfile = True
  isAddingLayerToQgisProject = True

  def addTable(self, tableName, schema=None, geometryColumn=None):
    """
    Add DB table to current project

    :rtype: QgsVectorLayer
    """
    uri = QgsDataSourceUri()
    uri.setConnection(self.dbHost, self.dbPort, self.dbName, self.dbUsername, self.dbPassword)
    uri.setDataSource(schema or self.dbSchema, tableName, geometryColumn)
    vlayer = QgsVectorLayer(uri.uri(False), tableName, "postgres")
    QgsProject.instance().addMapLayer(vlayer)
    return vlayer

  def getTable(self, tableName):
    """
    Get a table and exit if not found.
    
    :rtype: QgsVectorLayer
    """
    layers = QgsProject.instance().mapLayersByName(tableName)
    table = None
    if len(layers) == 0:
      print (f"Open PostgreSQL table '{tableName}' in current project. Adding it ...")
      return self.addTable(tableName)
      # TODO: Could be an error
    else:
      table = layers[0]
      print (f"MOSES indicator layer '{tableName}' found")
    return table

  class ThematicCategory:
    min = 0
    max = 0
    label = ""
    color = ""

    def __init__(self, min, max, label, color):
      self.min = min
      self.max = max
      self.label = label
      self.color = color

  def buildClassification(self, min, max, nb, nbOfClasses):
    classes = {}

    # No space for creating intervals
    if min == max:
      nbOfClasses = 1

    interval = (max - min) / nbOfClasses
    print(f" * Building classification with {nbOfClasses} with interval {interval} between {min} and {max} ...")
    for x in range(0, nbOfClasses):
      lower = min + (interval * x)
      upper = lower + interval
      # TODO: Round values
      color = palette.color(x).getRgb()
      print(color)
      classes[x] = self.ThematicCategory(lower, upper, f'{lower} - {upper}', f'{color[0]} {color[1]} {color[2]}')
    return classes

  def addFilteredLayer(self, layerCode, n, a, i, y, group):
    """
    Add layer with indicator values for a specific level and year.

    :rtype: QgsVectorLayer
    """
    uri = QgsDataSourceUri()
    print("Adding layer")
    uri.setConnection(self.dbHost, self.dbPort, self.dbName, self.dbUsername, self.dbPassword)
    # Add filter to global view / Provider filter
    filter = f'"year" = \'{y}\' AND "levl_code" = \'{n}\'AND "activity_id" = \'{a}\' AND "indicator_id" = \'{i}\''
    uri.setDataSource(self.dbSchema, CONST.LAYERNAME.ivalueview, "wkb_geometry", filter)
    vlayer = QgsVectorLayer(uri.uri(False), CONST.LAYERNAME.ivalueview, "postgres")
    QgsProject.instance().addMapLayer(vlayer)
    return vlayer

  def __init__(self):
    # TODO: Move to property file
    projectName = "MOSES visualization service"
    projectDescription = "Publishing indicators by NUTS level on marine coastline"
    projectUrl = "http://mosesproject.eu/projectpartners/"

    # for c in range(0, p.colors()):
    #  print(p.color(c).getRgb())
    # return
    # Load layers on map
    # https://gis.stackexchange.com/questions/277040/load-a-postgis-layer-into-a-qgis-map
    lValue = self.getTable(CONST.LAYERNAME.ivalue)
    lActivities = self.getTable(CONST.LAYERNAME.activities)
    lIndicators = self.getTable(CONST.LAYERNAME.indicators)

    # Loop on all
    layerCount = 0
    layerWithDataCount = 0
    years = lValue.uniqueValues(lValue.fields().indexOf("year"))
    if len(years) == 0:
      print('No years found.')
      return

    mapBuilder = MapfileBuilder('/tmp/moses.map', projectName, projectDescription, projectUrl);
    mapBuilder.writeHeader()

    # removeAllMapLayers ?

    nutsLevel = {1}
    # nutsLevel = {1, 2, 3}
    # ... activities
    requestActivities = QgsFeatureRequest()
    requestActivities.addOrderBy("id")

    # for a in lActivities.uniqueValues(lActivities.fields().indexOf("id")):
    for activityFeature in lActivities.getFeatures(requestActivities):
      # TODO: Get label
      # Add one group per activity
      # help(QgsProject.instance().layerTreeRoot())
      # layerTreeRoot
      activityId = activityFeature.attribute('id')
      activityLabel = activityFeature.attribute('name')
      groupLayer = QgsProject.instance().layerTreeRoot().addGroup(f'{activityId}.{activityLabel}')

      for indicator in lIndicators.uniqueValues(lIndicators.fields().indexOf("id")):
        # TODO: Collect min/max value over all years ?
        for year in years:
          for nutsLevel in nutsLevel:
            print(f"Processing {activityId} / {indicator} / {nutsLevel} / {year} ")
            # Check if any data for this combination
            query = f'"activity_id" = \'{activityId}\' AND "indicator_id" = \'{indicator}\' AND "year" = \'{year}\''
            request = QgsFeatureRequest().setFilterExpression(query)
            request.addOrderBy("value")
            selection = lValue.getFeatures(request)
            nbFeatures = sum(1 for _ in selection)
            selection = lValue.getFeatures(request)

            if nbFeatures > 0:
              # Collect min/max value
              ivMin = None
              ivMax = None
              counter = 0
              for k in selection:
                v = k.attribute("value")
                counter = counter + 1
                if counter == 1:
                  ivMin = k.attribute("value")
                  # print(k.attribute("year"))
                ivMax = k.attribute("value")

              # print("Found {0}".format(len(list(selection))))
              # print(selection)
              # TODO: Handle min=max=0 ?
              print(
                f"Indicator with {nbFeatures} values for level {nutsLevel}, indicator {activityId}/{indicator}, year {year} min={ivMin}/max={ivMax}")
              # TODO: Define how to classify ?
              # TODO? Could be relevant to build the classification using QGIS
              classes = self.buildClassification(ivMin, ivMax, counter, self.classificationNbOfClasses)
              for c in classes:
                print(f"  * Classe #{c}. {classes[c].label}")

              #  NUTS3.311.V16110.2013
              layerCode = f"NUTS{nutsLevel}.{activityId}.{indicator}.{year}"
              if self.isBuildingMapfile:
                mapBuilder.writeLayer(layerCode, nutsLevel, activityId, indicator, year, classes, self.dbHost,
                                      self.dbPort, self.dbName, self.dbUsername, self.dbPassword, self.dbSchema)
              if self.isAddingLayerToQgisProject:
                # TODO: Add layer with proper SQL filter to current project
                self.addFilteredLayer(layerCode, nutsLevel, activityId, indicator, year, groupLayer)
          break
        break
      break
      # print (f'Processing activity \'{a}\' > indicator \'{i}\' > year \'{y}\' ...')

    mapBuilder.writeFooter()


MosesPublication();
