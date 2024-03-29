from qgis.utils import *
from qgis.core import *

import re
import os
import time


class ContextBuilder:
    HEADER = """<ows-context:OWSContext xmlns:ows-context="http://www.opengis.net/ows-context" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ows="http://www.opengis.net/ows" version="0.3.1" id="ows-context-ex-1-v3">
  <ows-context:General>
    <ows:BoundingBox crs="EPSG:3857">
      <ows:LowerCorner>-5274429.416442219 3348478.9630677192</ows:LowerCorner>
      <ows:UpperCorner>4118152.619240239 8289368.471421512</ows:UpperCorner>
    </ows:BoundingBox>
  </ows-context:General>
  <ows-context:ResourceList>
  <ows-context:Layer name="{type=wmts,name=sextant}" group="Background layers" hidden="true" opacity="1">
      <ows:Title>Sextant</ows:Title>
      <ows-context:Server service="urn:ogc:serviceType:WMS">
        <ows-context:OnlineResource xlink:href="https://sextant.ifremer.fr/geowebcache/service/wmts?service=WMTS&amp;request=GetCapabilities&amp;version=1.0.0"/>
      </ows-context:Server>
    </ows-context:Layer>
    <ows-context:Layer name="{type=wmts,name=Ocean_Basemap}" group="Background layers" hidden="false" opacity="1">
      <ows:Title>Base Map</ows:Title>
      <ows-context:Server service="urn:ogc:serviceType:WMS">
        <ows-context:OnlineResource xlink:href="http://server.arcgisonline.com/arcgis/rest/services/Ocean_Basemap/MapServer/WMTS/1.0.0/WMTSCapabilities.xml"/>
      </ows-context:Server>
    </ows-context:Layer>
    <ows-context:Layer name="{type=bing_aerial}" group="Background layers" hidden="true" opacity="1">
      <ows:Title>Bing Aerial</ows:Title>
    </ows-context:Layer>
    <ows-context:Layer name="{type=osm}" group="Background layers" hidden="true" opacity="1">
      <ows:Title>OpenStreetMap</ows:Title>
    </ows-context:Layer>"""

    LAYER = """<ows-context:Layer name="{layerCode}" group="/{layerGroup}" hidden="true" opacity="1" groupcombo="moses">
      <ows:Title>{year}</ows:Title>
      <ows-context:Server service="urn:ogc:serviceType:WMS" version="1.3.0">
        <ows-context:OnlineResource xlink:href="{wmsUrl}"/>
      </ows-context:Server>
      <ows-context:Extension>
        <ows-context:MetadataUrlList/>
        <ows-context:QIList/>
      </ows-context:Extension>
    </ows-context:Layer>"""

    FOOTER = """
  </ows-context:ResourceList>
</ows-context:OWSContext>"""


    def __init__(self, file):
        self.file = file

    def writeHeader(self):
        contextFile = open(self.file, "w+")
        contextFile.write(self.HEADER)
        contextFile.close()

    def writeLayer(self, layerCode, wmsUrl, activityFullLabel, indicatorFullLabel, year):
        contextFile = open(self.file, "a+")

        groupTokens = layerCode.replace('.', '/').split('/')
        groupTokens.pop()
        groupTokens.pop(0)
        groupTokens[1] = activityFullLabel
        groupTokens[2] = indicatorFullLabel

        layerConfig = f"" + self.LAYER.format(layerCode=layerCode,
                                              layerGroup='/'.join(groupTokens),
                                              wmsUrl=wmsUrl,
                                              year=year)
        contextFile.write(layerConfig)
        contextFile.close()

    def writeFooter(self):
        contextFile = open(self.file, "a+")
        contextFile.write(f"" + self.FOOTER)
        contextFile.close()


class MapfileBuilder:
  HEADER = """MAP
    NAME "{projectName}"
    EXTENT -180 -90 180 90
    UNITS DD
    IMAGETYPE PNGA
    SYMBOLSET "symbol/symbols.txt"
    FONTSET "fonts/fonts.txt"

    DEBUG {debug}
    CONFIG "MS_ERRORFILE" "stderr"

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
        wms_onlineresource "{wmsBaseUrl}"
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
        wms_inspire_resourcelocator "{wmsBaseUrl}"
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
    # # {layerCode} ##
    LAYER
      NAME "{layerCode}"
      TYPE POLYGON
      DUMP TRUE
      STATUS ON
      EXTENT -180 -90 180 90
      UNITS DD

      CONNECTIONTYPE POSTGIS
      CONNECTION "host={dbHost} dbname={dbName} user={dbUsername}
                  password='{dbPassword}' port={dbPort}"
      DATA "wkb_geometry FROM (
      SELECT n.nuts_id, v.activity_id, v.indicator_id, v.unit,
        year, value, status, data_source, website, wkb_geometry
              FROM {dbSchema}.nuts n
             LEFT OUTER JOIN {dbSchema}.{dbTable} v
               ON v.nuts_id = n.nuts_id AND v.indicator_id = '{indicator}'
                 AND v.activity_id = '{activity}' {yearFilter}
              WHERE n.levl_code = '{level}'
          ) AS RS USING UNIQUE nuts_id USING srid=4326"

      PROJECTION
          "init=epsg:4326"
      END

      TEMPLATE "queryable"
      METADATA
        wms_title "{layerTitle}"
        wms_name "{layerCode}"
        wms_abstract "{layerAbstract}"
        wms_srs "EPSG:4326"
        wms_connectiontimeout "120"
        wms_server_version "1.3.0"
        wms_attribution_title "{projectName}"
        wms_attribution_onlineresource "http://mosesproject.eu/"
        wms_layer_group "/{layerGroup}"
        wms_group_title "/{layerGroup}"
        wms_group_abstract ""
        gml_include_items "all"
        wms_metadataurl_format "text/xml"
        wms_metadataurl_type "TC211"
        wms_metadataurl_href "{layerMetadataUrl}"
        {wmsTimeConfig}
      END

      CLASS
        NAME "No data"
        EXPRESSION (NOT [value])
        STYLE
          COLOR 240 240 240
          OUTLINECOLOR 211 211 211
        END
      END
      {categories}
    END
  """

  TIME = """
        wms_timeextent "{listOfYears}"
        wms_timeitem "year"
        wms_timeformat "YYYY"
        wms_timedefault "{lastYear}"
  """

  CATEGORY = """
      CLASS
        NAME "{label}"
        EXPRESSION ({min} <= [value] AND [value] <{equal} {max})
        STYLE
          COLOR {color}
          OUTLINECOLOR 211 211 211
        END
      END
      """

  FOOTER = """
END
  """

  def __init__(self, file, projectName, projectDescription, projectUrl, wmsBaseUrl, debug):
    self.file = file
    self.projectName = projectName
    self.projectDescription = projectDescription
    self.projectUrl = projectUrl
    self.wmsBaseUrl = wmsBaseUrl
    self.debug = debug

  # Write the mapfile
  def writeHeader(self):
    mapfile = open(self.file, "w+")
    mapfile.write(self.HEADER.format(projectName=self.projectName,
                                     projectDescription=self.projectDescription,
                                     projectUrl=self.projectUrl,
                                     debug=self.debug,
                                     wmsBaseUrl=self.wmsBaseUrl))
    mapfile.close()

  def writeLayer(self, layerCode, layerTitle, layerAbstract, level, activity, indicator, year, categories, dbHost, dbPort, dbName, dbUsername,
                 dbPassword, dbSchema, activityFullLabel, indicatorFullLabel, asTime = False, dbTable = 'moses_indicator_values', listOfYears = [2013, 2014, 2015]):
    """

    :rtype: object
    """
    mapfile = open(self.file, "a+")
    categoriesConfig = ""
    for c in categories:
      # Upper bound of last class must be equal to get the max value
      equal = ''
      if c == len(categories) - 1:
        equal = '='
      categoriesConfig = categoriesConfig + self.CATEGORY.format(min=categories[c].min,
                                                                 max=categories[c].max,
                                                                 equal=equal,
                                                                 # equal=(c==5 ? '=' : ''),
                                                                 color=categories[c].color,
                                                                 label=categories[c].label)

    groupTokens = layerCode.replace('.', '/').split('/')
    groupTokens.pop()
    groupTokens.pop(0)
    groupTokens[1] = activityFullLabel
    groupTokens[2] = indicatorFullLabel

    if asTime:
        wmsTimeConfig = self.TIME.format(
            listOfYears=','.join(str(x) for x in listOfYears),
            lastYear=listOfYears[0])
        yearFilter = ''
    else:
        wmsTimeConfig = ''
        yearFilter = f"AND v.year = '{year}'"

    layerConfig = f"" + self.LAYER.format(layerCode=layerCode,
                                          layerTitle=layerTitle,
                                          level=level,
                                          layerGroup='/'.join(groupTokens),
                                          layerAbstract=layerAbstract,
                                          activity=activity,
                                          indicator=indicator,
                                          yearFilter=yearFilter,
                                          projectName=self.projectName,
                                          layerMetadataUrl="",
                                          dbHost=dbHost,
                                          dbPort=dbPort,
                                          dbName=dbName,
                                          dbUsername=dbUsername,
                                          dbPassword=dbPassword,
                                          dbSchema=dbSchema,
                                          dbTable=dbTable,
                                          categories=categoriesConfig,
                                          wmsTimeConfig=wmsTimeConfig)
    mapfile.write(layerConfig)
    mapfile.close()

  def writeFooter(self):
    mapfile = open(self.file, "a+")
    mapfile.write(f"" + self.FOOTER)
    mapfile.close()



class CONST:
  class LAYERNAME:
    activities = "moses_activities"
    indicators = "moses_indicators"
    ivalue = "moses_indicator_values"
    ivalueview = "moses_indicator_values_with_nuts"




class MosesPublication:
  # dbName = 'moses'
  # dbHost = 'localhost'
  # dbPort = '5432'
  # dbUsername = 'www-data'
  # dbPassword = 'www-data'
  # dbSchema = 'public'
  dbName = 'moses'
  dbHost = 'vpostgres2.ifremer.fr'
  dbPort = '5432'
  dbUsername = 'moses_usr'
  dbPassword = 'The ...'
  dbSchema = 'moses'

  # wmsTimeLayerMode = False
  wmsTimeLayerMode = True

  classificationMethod = "equalInterval"
  classificationNbOfClasses = 5

  # Define color map
  # ['Spectral', 'RdYlGn', 'Set2', 'Accent', 'OrRd', 'Set1', 'PuBu', 'Set3', 'BuPu', 'Dark2', 'RdBu', 'Oranges', 'BuGn', 'PiYG', 'YlOrBr', 'YlGn', 'Reds', 'RdPu', 'Greens', 'PRGn', 'YlGnBu', 'RdYlBu', 'Paired', 'BrBG', 'Purples', 'Pastel2', 'Pastel1', 'GnBu', 'Greys', 'RdGy', 'YlOrRd', 'PuOr', 'PuRd', 'Blues', 'PuBuGn']
  colorScheme = 'Oranges'

  palette = QgsColorBrewerColorRamp.create({'colors': str(classificationNbOfClasses), 'schemeName': colorScheme})

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
      if nbOfClasses - 1 == x:
        upper = max
      else:
        upper = lower + interval
      # TODO: Round values
      color = self.palette.color(x/nbOfClasses).getRgb()
      print(color)
      classes[x] = self.ThematicCategory(lower, upper, f'{lower} - {upper}', f'{color[0]} {color[1]} {color[2]}')
    return classes

  def addFilteredLayer(self, layerCode, n, a, i, y, group, nbOfClasses, min, max):
    """
    Add layer with indicator values for a specific level and year.

    :rtype: QgsVectorLayer
    """
    layer = QgsProject.instance().mapLayersByName(layerCode)
    if layer is not None and len(layer) > 0:
        QgsProject.instance().removeMapLayers([layer[0].id()])

    uri = QgsDataSourceUri()
    uri.setConnection(self.dbHost, self.dbPort, self.dbName, self.dbUsername, self.dbPassword)
    # Add filter to global view / Provider filter
    filter = f'"year" = \'{y}\' AND "levl_code" = \'{n}\' AND "activity_id" = \'{a}\' AND "indicator_id" = \'{i}\''
    # uri.setDataSource(self.dbSchema, CONST.LAYERNAME.ivalueview, "wkb_geometry", filter)
    uri.setDataSource(self.dbSchema, "moses_indicator_values_with_nuts_m", "wkb_geometry", filter)
    vlayer = QgsVectorLayer(uri.uri(False), f'{layerCode}', "postgres")

    # https://gis.stackexchange.com/questions/325236/qgis-3-crashes-when-adding-a-postgis-view-as-a-map-layer
    QgsProject.instance().addMapLayer(vlayer)
    QgsProject.instance().layerTreeRoot().findLayer(vlayer.id()).setItemVisibilityChecked(False)

    renderer = QgsGraduatedSymbolRenderer('value', [])
    # renderer.setClassAttribute('value')
    renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)

    if min == max:
        nbOfClasses = 1

    renderer.updateClasses(vlayer,QgsGraduatedSymbolRenderer.EqualInterval, nbOfClasses)
    style = QgsStyle().defaultStyle()
    # ramp = style.addColorRamp("mosesPalette", self.palette)

    renderer.updateColorRamp(self.palette)
    vlayer.setRenderer(renderer)

    root = QgsProject.instance().layerTreeRoot()
    layer = root.findLayer(vlayer.id())
    clone = layer.clone()
    group.insertChildNode(-1, clone)
    root.removeChildNode(layer)

    return vlayer

  def __init__(self):
    # TODO: Move to property file
    projectName = "MOSES project data visualization service"
    projectDescription = "Publishing indicators by NUTS level on marine coastline"
    projectUrl = "http://mosesproject.eu/"
    wmsBaseUrl = "http://www.ifremer.fr/services/wms/moses"
    wmsTimeBaseUrl = "http://www.ifremer.fr/services/wms/moses"
    # wmsBaseUrl = "http://localhost/cgi-bin/mapserv?map=/data/dev/moses/moses.map"
    # wmsTimeBaseUrl = "http://localhost/cgi-bin/mapserv?map=/data/dev/moses/moses.map"
    debug = 'on'

    map = 'O:/wms/moses.map'
    maptime = 'O:/wms/moses-time.map'
    context = 'V:/moses/moses.xml'
    contexttime = 'V:/moses/moses-time.xml'
    # map = '/data/dev/moses/moses.map'
    # maptime = '/data/dev/moses/moses-time.map'
    # context = '/data/dev/moses/moses.xml'
    # contexttime = '/data/dev/moses/moses-time.xml'

    start_time = time.time()

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

    contextBuilder = ContextBuilder(context)
    contextBuilder.writeHeader()
    contextBuilderByActivity = {}
    if self.wmsTimeLayerMode:
        contextTimeBuilder = ContextBuilder(contexttime)
        contextTimeBuilder.writeHeader()
        contextTimeBuilderByActivity = {}
    mapBuilder = MapfileBuilder(map, projectName, projectDescription, projectUrl, wmsBaseUrl, debug);
    mapBuilder.writeHeader()
    mapTimeBuilder = MapfileBuilder(maptime, projectName, projectDescription, projectUrl, wmsTimeBaseUrl, debug);
    mapTimeBuilder.writeHeader()

    # removeAllMapLayers ?

    #nutsLevels = {1}
    nutsLevels = {0, 1, 2, 3}
    # ... activities
    requestActivities = QgsFeatureRequest()
    requestActivities.addOrderBy("id")

    uniqueActivities = lActivities.uniqueValues(lActivities.fields().indexOf("id"))
    uniqueIndicators = lIndicators.uniqueValues(lIndicators.fields().indexOf("id"))
    progressTotal = len(nutsLevels) * len(uniqueIndicators) * len(uniqueActivities) * len(years)
    progressCurrent = 0
    numberOfLayers = 0

    # for a in lActivities.uniqueValues(lActivities.fields().indexOf("id")):
    for activityFeature in lActivities.getFeatures(requestActivities):
      # TODO: Get label
      # Add one group per activity
      # help(QgsProject.instance().layerTreeRoot())
      # layerTreeRoot
      activityId = activityFeature.attribute('id')
      activitySector = activityFeature.attribute('sector').replace('/', '-')
      activityLabel = activityFeature.attribute('name')
      #activityFullLabel = f'{activityLabel} (NACE code: {activityId})'
      activityFullLabel = f'{activityLabel}'
      activityGroupLayerName = f'{activityFullLabel}'
      # activityGroupLayerName = f'{activityId}.{activityLabel}'


      contextBuilderByActivity[activityId] = ContextBuilder(context.replace('.xml', f'{activityId.replace(",", "")}.xml'))
      contextBuilderByActivity[activityId].writeHeader();
      if self.wmsTimeLayerMode:
          contextTimeBuilderByActivity[activityId] = ContextBuilder(context.replace('.xml', f'{activityId.replace(",", "")}-time.xml'))
          contextTimeBuilderByActivity[activityId].writeHeader();

      activityGroupLayer = QgsProject.instance().layerTreeRoot().findGroup(activityGroupLayerName)
      if activityGroupLayer is None:
        activityGroupLayer = QgsProject.instance().layerTreeRoot().addGroup(activityGroupLayerName)


      for indicator in uniqueIndicators:
        indicatorFullLabel = self.getIndicatorFullLabel(indicator, lIndicators)

        # TODO: Collect min/max value over all years ?
        for nutsLevel in nutsLevels:
          # TODO: Use infinity
          ivMinForAllYears = 9999999
          ivMaxForAllYears = -9999999
          listOfYears = []
          counterForAllYears = 0

          for year in years:
            progressCurrent = progressCurrent + 1
            print(f"{progressCurrent:>15}/{progressTotal:<15} - {progressCurrent / progressTotal:.0%}")

            print(f"Processing {activityId} / {indicator} / {nutsLevel} / {year} ")
            # Check if any data for this combination
            query = f'"activity_id" = \'{activityId}\' AND "indicator_id" = \'{indicator}\' AND "year" = \'{year}\' AND "nuts_level" = \'{nutsLevel}\''
            request = QgsFeatureRequest().setFilterExpression(query)
            request.addOrderBy("value")
            selection = lValue.getFeatures(request)
            nbFeatures = sum(1 for _ in selection)
            selection = lValue.getFeatures(request)

            if nbFeatures > 0:
              listOfYears.append(year)
              indicatorGroupLayerName = indicatorFullLabel
              indicatorGroupLayer = activityGroupLayer.findGroup(indicatorGroupLayerName)
              if indicatorGroupLayer  is None:
                  indicatorGroupLayer = activityGroupLayer.addGroup(indicatorGroupLayerName)

              nutsGroupLayerName = f'Nuts{nutsLevel}'
              nutsGroupLayer = indicatorGroupLayer.findGroup(nutsGroupLayerName)
              if nutsGroupLayer is None:
                  nutsGroupLayer = indicatorGroupLayer.addGroup(nutsGroupLayerName)

              # Collect min/max value
              ivMin = None
              ivMax = None
              counter = 0
              listOfNutsIdsWithData = []
              for k in selection:
                v = k.attribute("value")
                listOfNutsIdsWithData.append(k.attribute("nuts_id"))
                counter = counter + 1
                counterForAllYears = counterForAllYears + 1
                if counter == 1:
                  ivMin = k.attribute("value")
                  ivMinForAllYears=min(ivMin, ivMinForAllYears)
                  # print(k.attribute("year"))
                ivMax = k.attribute("value")
                ivMaxForAllYears=max(ivMax, ivMaxForAllYears)

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
              layerCode = f"MOSES.{activitySector}.{activityId.replace(',', '')}.{indicator}.NUTS{nutsLevel}.{year}"
              print(f'Layer code is {layerCode}')
              layerTitle = f"Moses indicator for nuts level {nutsLevel} activity {activityId} indicator {indicator} in {year}"

              layerAbstract=f'{",".join(listOfNutsIdsWithData)} provides information on this indicator.' if len(listOfNutsIdsWithData) > 0 else ''

              if self.isBuildingMapfile:
                mapBuilder.writeLayer(layerCode, layerTitle, layerAbstract, nutsLevel, activityId, indicator, year, classes, self.dbHost,
                                      self.dbPort, self.dbName, self.dbUsername, self.dbPassword, self.dbSchema, activityFullLabel, indicatorFullLabel)
                contextBuilder.writeLayer(layerCode, wmsBaseUrl, activityFullLabel, indicatorFullLabel, year)
                contextBuilderByActivity[activityId].writeLayer(layerCode, wmsBaseUrl, activityFullLabel, indicatorFullLabel, year)


              if self.isAddingLayerToQgisProject:
                # TODO: Add layer with proper SQL filter to current project
                self.addFilteredLayer(layerCode, nutsLevel, activityId, indicator, year, nutsGroupLayer, self.classificationNbOfClasses, ivMin, ivMax)
              numberOfLayers = numberOfLayers + 1


          # Create a time layer
          if self.wmsTimeLayerMode and ivMinForAllYears != -ivMaxForAllYears:
              layerCode = f"MOSES.{activitySector}.{activityId.replace(',', '')}.{indicator}.NUTS{nutsLevel}"
              print(f'Time layer code is {layerCode}')
              layerTitle = f"Moses indicator for nuts level {nutsLevel} activity {activityId} indicator {indicator}"
              classes = self.buildClassification(ivMinForAllYears, ivMaxForAllYears, counterForAllYears, self.classificationNbOfClasses)

              mapTimeBuilder.writeLayer(layerCode, layerTitle, layerAbstract, nutsLevel, activityId, indicator, year, classes, self.dbHost,
                                      self.dbPort, self.dbName, self.dbUsername, self.dbPassword, self.dbSchema, activityFullLabel, indicatorFullLabel, True, 'moses_indicator_values_date', listOfYears)

              contextTimeBuilder.writeLayer(layerCode, wmsTimeBaseUrl, activityFullLabel, indicatorFullLabel, '')
              contextTimeBuilderByActivity[activityId].writeLayer(layerCode, wmsTimeBaseUrl, activityFullLabel, indicatorFullLabel, '')


      #break
        #break
      #break
      contextBuilderByActivity[activityId].writeFooter();
      if self.wmsTimeLayerMode:
        contextTimeBuilderByActivity[activityId].writeFooter();
      # print (f'Processing activity \'{a}\' > indicator \'{i}\' > year \'{y}\' ...')

    mapBuilder.writeFooter()
    contextBuilder.writeFooter()
    if self.wmsTimeLayerMode:
      mapTimeBuilder.writeFooter()
      contextTimeBuilder.writeFooter()

    elapsed_time = time.time() - start_time
    print( 'Execution time: %.3f' % (elapsed_time))
    print(f"Number of layers added to mapfile: {numberOfLayers}.")

  def getIndicatorFullLabel(self, indicator, lIndicators):
    query = f'"id" = \'{indicator}\''
    request = QgsFeatureRequest().setFilterExpression(query)
    feature = lIndicators.getFeatures(request)
    for f in feature:
        name = f.attribute('name')
        if f.attribute('unit') == '-':
            return f.attribute('name')
        else:
            return '{name} ({unit})'.format(name=f.attribute('name'), unit=f.attribute('unit'))


MosesPublication()
