"""
created by Nikolay V. Ulyanov (ulianownv@mail.ru)
http://www.smcsystem.ru
"""
import datetime
import os.path
import tempfile
from __builtin__ import long, unicode
from typing import Dict, List, Callable

import SMCApi


class Value(SMCApi.IValue):
    def __init__(self, value, typev=None):
        # type: (any, SMCApi.ValueType) -> None
        self.value = value
        self.typev = typev
        if typev is None:
            valueType = type(value)
            if valueType is str or valueType is unicode:  # isinstance(value, basestring):
                self.typev = SMCApi.ValueType.STRING
            elif valueType == bytearray or valueType == bytes:
                self.typev = SMCApi.ValueType.BYTES
            elif valueType == int:
                self.typev = SMCApi.ValueType.INTEGER
            elif valueType == long:
                self.typev = SMCApi.ValueType.LONG
            elif valueType == float:
                self.typev = SMCApi.ValueType.DOUBLE
            elif valueType == bool:
                self.typev = SMCApi.ValueType.BOOLEAN
            elif valueType == SMCApi.ObjectArray:
                self.typev = SMCApi.ValueType.OBJECT_ARRAY
            else:
                raise ValueError("wrong type")

    def getType(self):
        return self.typev

    def getValue(self):
        return self.value


class Message(SMCApi.IMessage, SMCApi.IValue):
    def __init__(self, messageType, value, date=None):
        # type: (SMCApi.MessageType, SMCApi.IValue, datetime) -> None
        self.messageType = messageType
        self.value = value
        if date is not None:
            self.date = date
        else:
            self.date = datetime.datetime.now()

    def getDate(self):
        return self.date

    def getMessageType(self):
        return self.messageType

    def getType(self):
        return self.value.getType()

    def getValue(self):
        return self.value.getValue()


class Action(SMCApi.IAction):
    def __init__(self, messages, type):
        # type: (List[SMCApi.IMessage], SMCApi.ActionType) -> None
        if messages is not None:
            self.messages = list(messages)
        else:
            self.messages = []
        self.type = type

    def getMessages(self):
        return self.messages

    def getType(self):
        return self.type


class Command(SMCApi.ICommand):
    def __init__(self, actions, type):
        # type: (List[SMCApi.IAction], SMCApi.CommandType) -> None
        if actions is not None:
            self.actions = list(actions)
        else:
            self.actions = []
        self.type = type

    def getActions(self):
        return self.actions

    def getType(self):
        return self.type


class ModuleType(object):
    def __init__(self, name, minCountSources=0, maxCountSources=-1, minCountExecutionContexts=0, maxCountExecutionContexts=-1,
                 minCountManagedConfigurations=0, maxCountManagedConfigurations=-1):
        # type: (str, int, int, int, int, int, int) -> None
        self.name = name
        self.minCountSources = minCountSources
        self.maxCountSources = maxCountSources
        self.minCountExecutionContexts = minCountExecutionContexts
        self.maxCountExecutionContexts = maxCountExecutionContexts
        self.minCountManagedConfigurations = minCountManagedConfigurations
        self.maxCountManagedConfigurations = maxCountManagedConfigurations


class Module(SMCApi.CFGIModule):
    def __init__(self, name, types=None):
        # type: (str, List[ModuleType]) -> None
        self.name = name
        if types:
            self.types = list(types)
        else:
            self.types = [ModuleType("default")]

    def getName(self):
        return self.name

    def countTypes(self):
        return len(self.types)

    def getTypeName(self, typeId):
        return self.types[typeId].name

    def getMinCountSources(self, typeId):
        return self.types[typeId].minCountSources

    def getMaxCountSources(self, typeId):
        return self.types[typeId].maxCountSources

    def getMinCountExecutionContexts(self, typeId):
        return self.types[typeId].minCountExecutionContexts

    def getMaxCountExecutionContexts(self, typeId):
        return self.types[typeId].maxCountExecutionContexts

    def getMinCountManagedConfigurations(self, typeId):
        return self.types[typeId].minCountManagedConfigurations

    def getMaxCountManagedConfigurations(self, typeId):
        return self.types[typeId].maxCountManagedConfigurations


class Container(SMCApi.CFGIContainerManaged):
    def __init__(self, executionContextTool, name, containers=None, configurations=None):
        # type: (ExecutionContextToolImpl, str, List[SMCApi.CFGIContainer], List[SMCApi.CFGIConfiguration]) -> None
        self.executionContextTool = executionContextTool
        self.name = name
        self.enable = True
        if containers is not None:
            self.containers = list(containers)
        else:
            self.containers = []
        if configurations is not None:
            self.configurations = list(configurations)
        else:
            self.configurations = []

    def setExecutionContextTool(self, executionContextTool):
        # type: (ExecutionContextToolImpl) -> None
        self.executionContextTool = executionContextTool

    def countConfigurations(self):
        return len(self.configurations)

    def getConfiguration(self, id):
        return self.configurations[id]

    def countManagedConfigurations(self):
        return len(self.configurations)

    def getManagedConfiguration(self, id):
        return self.configurations[id]

    def countContainers(self):
        return len(self.containers)

    def getContainer(self, id):
        return self.containers[id]

    def createContainer(self, name):
        container = Container(self.executionContextTool, name)
        self.containers.append(container)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONTAINER_CREATE, container.getName())
        return container

    def removeContainer(self, id):
        if id < 0 or id >= len(self.containers):
            raise SMCApi.ModuleException("id")
        container = self.containers[id]
        if container.countConfigurations() > 0:
            raise SMCApi.ModuleException("container has child configurations")
        if container.countContainers() > 0:
            raise SMCApi.ModuleException("container has child containers")
        self.containers.pop(id)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONTAINER_REMOVE, container.getName())

    def getName(self):
        return self.name

    def isEnable(self):
        return self.enable


class Configuration(SMCApi.CFGIConfigurationManaged):
    def __init__(self, executionContextTool, container, module, name, description=None, settings=None, variables=None, executionContexts=None,
                 bufferSize=0, threadBufferSize=1):
        # type: (ExecutionContextToolImpl, Container, SMCApi.Module, str, str, Dict[str, SMCApi.IValue], Dict[str, SMCApi.IValue], List[SMCApi.CFGIExecutionContextManaged], int, int) -> None
        self.executionContextTool = executionContextTool
        self.container = container
        self.module = module
        self.name = name
        self.description = description
        if settings:
            self.settings = dict(settings)
        else:
            self.settings = {}
        if variables:
            self.variables = dict(variables)
        else:
            self.variables = {}
        if executionContexts:
            self.executionContexts = list(executionContexts)
        else:
            self.executionContexts = []
        self.bufferSize = bufferSize
        self.threadBufferSize = threadBufferSize
        self.enable = True

        if self.container:
            self.container.configurations.append(self)

    def setExecutionContextTool(self, executionContextTool):
        self.executionContextTool = executionContextTool
        for ec in self.executionContexts:
            ec.setExecutionContextTool(executionContextTool)
        if self.container:
            self.container.setExecutionContextTool(executionContextTool)

    def setContainer(self, container):
        if self.container:
            self.container.configurations.remove(self)
        self.container = container
        if self.container:
            self.container.configurations.add(self)

    def setName(self, name):
        self.name = name
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def setSetting(self, key, value):
        self.settings[key] = Value(value)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_SETTING_UPDATE,
                                      "{} {}".format(self.getName(), key))

    def setVariable(self, key, value):
        self.variables[key] = Value(value)
        if self.executionContextTool is not None:
            self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_VARIABLE_UPDATE,
                                          "{} {}".format(self.getName(), key))

    def removeVariable(self, key):
        del self.variables[key]
        if self.executionContextTool is not None:
            self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_VARIABLE_REMOVE,
                                          "{} {}".format(self.getName(), key))

    def setBufferSize(self, bufferSize):
        self.bufferSize = bufferSize
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def setThreadBufferSize(self, threadBufferSize):
        self.threadBufferSize = threadBufferSize
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def setEnable(self, enable):
        self.enable = enable
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def countExecutionContexts(self):
        return len(self.executionContexts)

    def getExecutionContext(self, id):
        if id < 0 or id >= self.countExecutionContexts():
            raise SMCApi.ModuleException("id")
        return self.executionContexts[id]

    def createExecutionContext(self, name, type, maxWorkInterval=-1):
        executionContext = ExecutionContext(self.executionContextTool, name, None, None, None, None, maxWorkInterval, type)
        self.executionContexts.append(executionContext)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_CREATE, "{} {}".format(self.getName(), name))
        return executionContext

    def updateExecutionContext(self, id, type, name, maxWorkInterval=-1):
        executionContext = self.executionContexts[id]
        executionContext.setName(name)
        executionContext.setType(type)
        executionContext.setMaxWorkInterval(maxWorkInterval)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE, "{} {}".format(self.getName(), name))
        return executionContext

    def removeExecutionContext(self, id):
        if id < 0 or id >= self.countExecutionContexts():
            raise SMCApi.ModuleException("id")
        executionContext = self.executionContexts[id]
        del self.executionContexts[id]
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_REMOVE,
                                      "{} {}".format(self.getName(), executionContext.getName()))

    def getContainer(self):
        return self.container

    def getModule(self):
        return self.module

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getAllSettings(self):
        return self.settings

    def getSetting(self, key):
        if not key:
            raise SMCApi.ModuleException("key")
        return self.settings[key]

    def getAllVariables(self):
        return self.variables

    def getVariable(self, key):
        if not key:
            raise SMCApi.ModuleException("key")
        return self.variables[key]

    def getBufferSize(self):
        return self.bufferSize

    def getThreadBufferSize(self):
        return self.threadBufferSize

    def isEnable(self):
        return self.enable

    def isActive(self):
        return False


class SourceList(SMCApi.CFGISourceListManaged):
    def __init__(self, executionContextTool, configurationName, executionContextName, sources=None):
        # type: (ExecutionContextToolImpl, str, str, List[SMCApi.CFGISourceManaged]) -> None
        self.executionContextTool = executionContextTool
        self.configurationName = configurationName
        self.executionContextName = executionContextName
        if sources:
            self.sources = list(sources)
        else:
            self.sources = []

    def setConfigurationName(self, configurationName):
        self.configurationName = configurationName

    def countSource(self):
        return len(self.sources)

    def getSource(self, id):
        return self.sources[id]

    def createSourceConfiguration(self, configuration, getType=SMCApi.SourceGetType.NEW, countLast=1, eventDriven=False):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, configuration, None, eventDriven, None,
                        SMCApi.SourceType.MODULE_CONFIGURATION, self.countSource())
        self.sources.append(source)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_CREATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def createSourceExecutionContext(self, executionContext, getType=SMCApi.SourceGetType.NEW, countLast=1, eventDriven=False):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, executionContext, None, None, eventDriven, None,
                        SMCApi.SourceType.MODULE_CONFIGURATION, self.countSource())
        self.sources.append(source)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_CREATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def createSourceValue(self, value):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, None, Value(value), False, None,
                        SMCApi.SourceType.STATIC_VALUE, self.countSource())
        self.sources.append(source)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_CREATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def createSource(self):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, None, None, False, None,
                        SMCApi.SourceType.MULTIPART, self.countSource())
        self.sources.append(source)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_CREATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def createSourceObjectArray(self, value, fields):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, None, Value(value), False, None,
                        SMCApi.SourceType.OBJECT_ARRAY, self.countSource())
        self.sources.append(source)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_CREATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def updateSourceConfiguration(self, id, configuration, getType=SMCApi.SourceGetType.NEW, countLast=1, eventDriven=False):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, configuration, None, eventDriven, None,
                        SMCApi.SourceType.MODULE_CONFIGURATION, self.countSource())
        self.sources[id] = source
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_UPDATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def updateSourceExecutionContext(self, id, executionContext, getType=SMCApi.SourceGetType.NEW, countLast=1, eventDriven=False):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, executionContext, None, None, eventDriven, None,
                        SMCApi.SourceType.MODULE_CONFIGURATION, self.countSource())
        self.sources[id] = source
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_UPDATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def updateSourceValue(self, id, value):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, None, Value(value), False, None,
                        SMCApi.SourceType.STATIC_VALUE, self.countSource())
        self.sources[id] = source
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_UPDATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def updateSourceObjectArray(self, id, value, fields):
        source = Source(self.executionContextTool, self.configurationName, self.executionContextName, None, None, Value(value), False, None,
                        SMCApi.SourceType.OBJECT_ARRAY, self.countSource())
        self.sources[id] = source
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_UPDATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))
        return source

    def removeSource(self, id):
        if id < 0 or id >= self.countSource():
            raise SMCApi.ModuleException("id")
        source = self.sources[id]
        del self.sources[id]
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_SOURCE_CONTEXT_UPDATE,
                                      "{}.{}.{}".format(self.configurationName, self.executionContextName, source.getOrder()))

    def getSourceListManaged(self, id):
        source = self.sources[id]
        if not source or source.getType() != SMCApi.SourceType.MULTIPART:
            return None
        return SourceList(self.executionContextTool, self.configurationName, self.executionContextName, [source])

    def getSourceManaged(self, id):
        if id < self.countSource():
            return self.sources[id]
        return None


class ExecutionContext(SourceList, SMCApi.CFGIExecutionContextManaged):
    def __init__(self, executionContextTool, name, configuration=None, executionContexts=None, managedConfigurations=None, sources=None,
                 maxWorkInterval=-1, type="default"):
        # type: (ExecutionContextToolImpl, str, Configuration, List[SMCApi.CFGIExecutionContextManaged], List[SMCApi.CFGIConfigurationManaged], List[SMCApi.CFGISourceManaged], int, str) -> None
        if configuration:
            configurationName = configuration.getName()
        else:
            configurationName = "default"
        super(ExecutionContext, self).__init__(executionContextTool, configurationName, name, sources)

        self.executionContextTool = executionContextTool
        self.configuration = configuration
        self.name = name
        if executionContexts:
            self.executionContexts = list(executionContexts)
        else:
            self.executionContexts = []
        if managedConfigurations:
            self.managedConfigurations = list(managedConfigurations)
        else:
            self.managedConfigurations = []
        self.maxWorkInterval = maxWorkInterval
        self.type = type
        self.enable = True

    def setExecutionContextTool(self, executionContextTool):
        self.executionContextTool = executionContextTool

    def setConfiguration(self, configuration):
        self.configuration = configuration
        self.setConfigurationName(configuration.getName())

    def setName(self, name):
        self.name = name

    def setMaxWorkInterval(self, maxWorkInterval):
        self.maxWorkInterval = maxWorkInterval
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def setEnable(self, enable):
        self.enable = enable
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def countExecutionContexts(self):
        return len(self.executionContexts)

    def getExecutionContext(self, id):
        if id < 0 or id >= self.countExecutionContexts():
            raise SMCApi.ModuleException("id")
        return self.executionContexts[id]

    def insertExecutionContext(self, id, executionContext):
        if id < 0 or id >= self.countExecutionContexts():
            raise SMCApi.ModuleException("id")
        self.executionContexts.insert(id, executionContext)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def updateExecutionContext(self, id, executionContext):
        if id < 0 or id >= self.countExecutionContexts():
            raise SMCApi.ModuleException("id")
        self.executionContexts[id] = executionContext
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def removeExecutionContext(self, id):
        if id < 0 or id >= self.countExecutionContexts():
            raise SMCApi.ModuleException("id")
        del self.executionContexts[id]
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def countManagedConfigurations(self):
        return len(self.managedConfigurations)

    def getManagedConfiguration(self, id):
        if id < 0 or id >= self.countManagedConfigurations():
            raise SMCApi.ModuleException("id")
        return self.managedConfigurations[id]

    def insertManagedConfiguration(self, id, configuration):
        if id < 0 or id >= self.countManagedConfigurations():
            raise SMCApi.ModuleException("id")
        self.managedConfigurations.insert(id, configuration)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def updateManagedConfiguration(self, id, configuration):
        if id < 0 or id >= self.countManagedConfigurations():
            raise SMCApi.ModuleException("id")
        self.managedConfigurations[id] = configuration
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def removeManagedConfiguration(self, id):
        if id < 0 or id >= self.countManagedConfigurations():
            raise SMCApi.ModuleException("id")
        del self.managedConfigurations[id]
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE,
                                      "{}.{}".format(self.configuration.getName(), self.getName()))

    def setType(self, type):
        self.type = type

    def getConfiguration(self):
        return self.configuration

    def getName(self):
        return self.name

    def getMaxWorkInterval(self):
        return self.maxWorkInterval

    def isEnable(self):
        return self.enable

    def isActive(self):
        return False

    def getType(self):
        return self.type


class SourceFilter(SMCApi.CFGISourceFilter):
    def __init__(self, type, params=None):
        # type: (SMCApi.SourceFilterType, List) -> None
        self.type = type
        if self.params:
            self.params = list(params)
        else:
            self.params = []

    def getType(self):
        return self.type

    def getParams(self):
        return self.params

    def countParams(self):
        if self.type == SMCApi.SourceFilterType.POSITION:
            return 4
        elif self.type == SMCApi.SourceFilterType.NUMBER:
            return 2
        elif self.type == SMCApi.SourceFilterType.STRING_EQUAL:
            return 2
        elif self.type == SMCApi.SourceFilterType.STRING_CONTAIN:
            return 2
        elif self.type == SMCApi.SourceFilterType.OBJECT_PATHS:
            return 1
        else:
            raise Exception()

    def getParam(self, id):
        return self.params[id]


class Source(SMCApi.CFGISourceManaged):
    def __init__(self, executionContextTool, configurationName, executionContextName, executionContextSource=None, configurationSource=None,
                 valueSource=None,
                 eventDriven=False, sources=None, type=SMCApi.SourceType.STATIC_VALUE, order=0):
        # type: (ExecutionContextToolImpl, str,str, SMCApi.CFGIExecutionContext, SMCApi.CFGIConfiguration, SMCApi.IValue, bool, List[SMCApi.CFGISourceManaged], SMCApi.SourceType, int) -> None
        self.executionContextTool = executionContextTool
        self.configurationName = configurationName
        self.executionContextName = executionContextName
        self.executionContextSource = executionContextSource
        self.configurationSource = configurationSource
        self.eventDriven = eventDriven
        if not self.eventDriven:
            self.eventDriven = False
        self.valueSource = valueSource
        self.type = type
        self.order = order
        if SMCApi.SourceType.MULTIPART == type:
            self.sourceList = SourceList(self.executionContextTool, self.configurationName, self.executionContextName, sources)
        else:
            self.sourceList = None
        self.filters = []

    def getType(self):
        return self.type

    def countParams(self):
        if self.type == SMCApi.SourceType.MODULE_CONFIGURATION:
            return 4
        elif self.type == SMCApi.SourceType.EXECUTION_CONTEXT:
            return 4
        elif self.type == SMCApi.SourceType.STATIC_VALUE:
            return 1
        elif self.type == SMCApi.SourceType.MULTIPART:
            return 0
        elif self.type == SMCApi.SourceType.CALLER:
            return 0
        elif self.type == SMCApi.SourceType.CALLER_RELATIVE_NAME:
            return 1
        elif self.type == SMCApi.SourceType.OBJECT_ARRAY:
            return 1
        else:
            raise Exception()

    def getParam(self, id):
        return None

    def countFilters(self):
        return len(self.filters)

    def getFilter(self, id):
        return self.filters[id]

    def createFilterPosition(self, range, period=0, countPeriods=0, startOffset=0, forObject=False):
        return None

    def createFilterNumber(self, min, max, fieldName=None):
        return None

    def createFilterStrEq(self, needEquals, value, fieldName=None):
        return None

    def createFilterStrContain(self, needContain, value, fieldName=None):
        return None

    def createFilterObjectPaths(self, paths):
        return None

    def updateFilterPosition(self, id, range, period=0, countPeriods=0, startOffset=0, forObject=False):
        return None

    def updateFilterNumber(self, id, min, max, fieldName=None):
        return None

    def updateFilterStrEq(self, id, needEquals, value, fieldName=None):
        return None

    def updateFilterStrContain(self, id, needContain, value, fieldName=None):
        return None

    def updateFilterObjectPaths(self, id, paths):
        return None

    def removeFilter(self, id):
        del self.filters[id]

    def getOrder(self):
        return self.order

    def setOrder(self, order):
        self.order = order


class FileToolImpl(SMCApi.FileTool):
    def __init__(self, fileName):
        # type: (str) -> None
        self.fileName = fileName

    def getName(self):
        return os.path.basename(self.fileName)

    def exists(self):
        return os.path.exists(self.fileName)

    def isDirectory(self):
        return os.path.isdir(self.fileName)

    def getChildrens(self):
        childrens = []
        for fileName in os.listdir(self.fileName):
            childrens.append(FileToolImpl(os.path.join(self.fileName, fileName)))
        return childrens

    def getBytes(self):
        f = open(self.fileName, "rb")
        data = f.read()
        f.close()
        return data

    def length(self):
        return os.path.getsize(self.fileName)


class ConfigurationToolImpl(Configuration, SMCApi.ConfigurationTool):
    def __init__(self, name="default", configuration=None, description=None, settings=None, homeFolder=None, workDirectory=None):
        # type: (str, Configuration, str, Dict[str, SMCApi.IValue], str, str) -> None

        if configuration:
            executionContextTool = configuration.executionContextTool
            container = configuration.container
            module = configuration.module
            if not name:
                name = configuration.name
            if not description:
                description = configuration.description
            if not settings:
                settings = configuration.settings
            variables = configuration.variables
            executionContexts = configuration.executionContexts
            bufferSize = configuration.bufferSize
            threadBufferSize = configuration.threadBufferSize
        else:
            executionContextTool = None
            container = None
            module = None
            variables = None
            executionContexts = None
            bufferSize = None
            threadBufferSize = None

        super(ConfigurationToolImpl, self).__init__(executionContextTool, container, module, name, description, settings, variables,
                                                    executionContexts, bufferSize, threadBufferSize)
        if homeFolder is None:
            homeFolder = tempfile.gettempdir()
        self.homeFolder = homeFolder
        if workDirectory is None:
            workDirectory = tempfile.gettempdir()
        self.workDirectory = workDirectory
        # type: Dict[str, bool]
        self.variablesChangeFlag = {}
        for v in self.getAllVariables():
            self.variablesChangeFlag[v.name] = True

    def init(self, executionContextTool):
        # type: (ExecutionContextToolImpl) -> None
        self.executionContextTool = executionContextTool

    def getVariablesChangeFlag(self):
        return self.variablesChangeFlag

    def setVariable(self, key, value):
        super(ConfigurationToolImpl, self).setVariable(key, value)
        self.variablesChangeFlag[key] = False

    def isVariableChanged(self, key):
        return self.variablesChangeFlag[key]

    def removeVariable(self, key):
        super(ConfigurationToolImpl, self).removeVariable(key)
        self.variablesChangeFlag[key] = False

    def getHomeFolder(self):
        return FileToolImpl(self.homeFolder)

    def getWorkDirectory(self):
        return self.workDirectory

    # noinspection PyStatementEffect
    def loggerTrace(self, text):
        print
        "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    # noinspection PyStatementEffect
    def loggerDebug(self, text):
        print
        "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    # noinspection PyStatementEffect
    def loggerInfo(self, text):
        print
        "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    # noinspection PyStatementEffect
    def loggerWarn(self, text):
        print
        "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    # noinspection PyStatementEffect
    def loggerError(self, text):
        print
        "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)


# noinspection PyAbstractClass
class ExecutionContextToolImpl(ExecutionContext, SMCApi.ExecutionContextTool):
    def __init__(self, input=None, managedConfigurations=None, executionContextsOutput=None, executionContexts=None, name="default", type="default"):
        # type: (List[List[SMCApi.IAction]], List[Configuration], List[SMCApi.IAction], List[Callable[[List[object]], SMCApi.IAction]], str, str) -> None
        # ExecutionContext.__init__(self, self, name)
        SMCApi.FlowControlTool.__init__(self)
        SMCApi.ConfigurationControlTool.__init__(self)
        SMCApi.ExecutionContextTool.__init__(self)
        ExecutionContext.__init__(self, self, name)
        # super(ExecutionContextToolImpl, self).__init__(name)
        if input is not None:
            self.input = list(input)
        else:
            self.input = []
        self.output = []
        if managedConfigurations is not None:
            self.managedConfigurations = list(managedConfigurations)
        else:
            self.managedConfigurations = []
        for c in self.managedConfigurations:
            c.setExecutionContextTool(self)
        if executionContextsOutput is not None:
            self.executionContextsOutput = list(executionContextsOutput)
        else:
            self.executionContextsOutput = []
        if executionContexts is not None:
            self.executionContexts = list(executionContexts)
            for _ in self.executionContexts:
                self.executionContextsOutput.append(None)
        else:
            self.executionContexts = []
        self.name = name
        self.type = type
        self.modules = []
        modulesByName = {}
        for cfg in self.managedConfigurations:
            modulesByName[cfg.getModule().getName()] = cfg.getModule()
        modulesByName["Module"] = Module("Module")
        for name in modulesByName:
            self.modules.append(modulesByName[name])

        self.configurationControlTool = ConfigurationControlTool(self, self.modules, self.managedConfigurations)
        # noinspection PyTypeChecker
        self.flowControlTool = FlowControlTool(self, self.executionContextsOutput, self.executionContexts)

    def init(self, configurationTool):
        # type: (ConfigurationToolImpl) -> None
        self.configuration = configurationTool
        self.setConfiguration(self.configuration)

    def getOutput(self):
        return self.output

    def add(self, messageType, value):
        # type: (SMCApi.MessageType, object) -> None
        self.output.append(Message(messageType, Value(value)))

    def addMessage(self, value):
        if not value:
            raise SMCApi.ModuleException("value")
        if isinstance(value, list):
            date = datetime.datetime.now()
            for element in value:
                self.output.append(Message(SMCApi.MessageType.DATA, Value(element), date))
        else:
            self.output.append(Message(SMCApi.MessageType.DATA, Value(value)))

    def addError(self, value):
        if not value:
            raise SMCApi.ModuleException("value")
        if isinstance(value, list):
            date = datetime.datetime.now()
            for element in value:
                self.output.append(Message(SMCApi.MessageType.ERROR, Value(element), date))
        else:
            self.output.append(Message(SMCApi.MessageType.ERROR, Value(value)))

    def addLog(self, value):
        if not value:
            raise SMCApi.ModuleException("value")
        self.output.append(Message(SMCApi.MessageType.LOG, Value(value)))

    def countSource(self):
        return len(self.input)

    def getSource(self, id):
        sources = []
        if self.input:
            for i in range(len(self.input)):
                sources.append(Source(self, self.configuration.getName(), self.getName(), ExecutionContext(self, str(i)), None, None, False, None,
                                      SMCApi.SourceType.EXECUTION_CONTEXT, i))
        return SourceList(self, self.configuration.getName(), self.getName(), sources).getSource(id)

    def getMessagesAll(self, sourceId):
        if sourceId < 0 or self.countSource() <= sourceId:
            raise SMCApi.ModuleException("sourceId")
        data = self.input[sourceId]
        if not data:
            data = []
        return data

    def countCommands(self, sourceId):
        return len(self.getMessagesAll(sourceId))

    def countCommandsFromExecutionContext(self, executionContext):
        return 0

    def getMessages(self, sourceId, fromIndex=-1, toIndex=-1):
        lst = self.filter(self.getMessagesAll(sourceId), SMCApi.ActionType.EXECUTE, SMCApi.MessageType.DATA)
        if fromIndex != -1 or toIndex != -1:
            lst = lst[fromIndex: toIndex]
        return lst

    # noinspection PyMethodMayBeStatic
    def filter(self, actions, actionType=None, messageType=None):
        # type: (List[SMCApi.IAction], SMCApi.ActionType, SMCApi.MessageType)->List[SMCApi.IAction]
        result = []
        for a in actions:
            if actionType and actionType != a.getType():
                continue
            collect = filter(lambda m: not messageType or messageType == m.getMessageType(), a.getMessages())
            result.append(Action(collect, a.getType()))
        return result

    def getCommands(self, sourceId, fromIndex=-1, toIndex=-1):
        lst = [Command(self.getMessagesAll(sourceId), SMCApi.CommandType.EXECUTE)]
        if fromIndex != -1 or toIndex != -1:
            lst = lst[fromIndex: toIndex]
        return lst

    def getCommandsFromExecutionContext(self, executionContext, fromIndex=-1, toIndex=-1):
        return []

    def isError(self, action):
        result = True
        while True:
            if not action:
                break
            if not action.getMessages() or len(action.getMessages()) == 0:
                break
            if any(SMCApi.MessageType.ACTION_ERROR == m.getMessageType() or SMCApi.MessageType.ERROR == m.getMessageType()
                   for m in action.getMessages()):
                break
            result = False
            break
        return result

    def getConfigurationControlTool(self):
        return self.configurationControlTool

    def getFlowControlTool(self):
        return self.flowControlTool

    def isNeedStop(self):
        return False


class ConfigurationControlTool(SMCApi.ConfigurationControlTool):
    def __init__(self, executionContextTool, modules, managedConfigurations):
        # type: (ExecutionContextToolImpl, List[SMCApi.CFGIModule], List[Configuration]) -> None
        self.executionContextTool = executionContextTool
        self.modules = modules
        self.managedConfigurations = managedConfigurations

    def getModules(self):
        return self.modules

    def countManagedConfigurations(self):
        return len(self.managedConfigurations)

    def getManagedConfiguration(self, id):
        return self.managedConfigurations[id]

    def createConfiguration(self, id, container, module, name):
        # noinspection PyTypeChecker
        configuration = Configuration(self.executionContextTool, container, module, name, "")
        configuration.setContainer(container)
        self.managedConfigurations.insert(id, configuration)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_CREATE, configuration.getName())
        return configuration

    def removeManagedConfiguration(self, id):
        configuration = self.managedConfigurations.pop(id)
        configuration.setContainer(None)
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_CONFIGURATION_REMOVE, configuration.getName())


class FlowControlTool(SMCApi.FlowControlTool):
    def __init__(self, executionContextTool, executionContextsOutput, executionContexts=None):
        # type: (ExecutionContextToolImpl, List[SMCApi.IAction], List[Callable[[List[object]], SMCApi.IAction]]) -> None
        self.executionContextTool = executionContextTool
        self.executionContextsOutput = executionContextsOutput
        self.executionContexts = executionContexts
        self.executeInParalel = []

    def countManagedExecutionContexts(self):
        return len(self.executionContextsOutput)

    def executeNow(self, type, managedId, values):
        if not type:
            raise SMCApi.ModuleException("type")
        if managedId < 0 or managedId >= self.countManagedExecutionContexts():
            raise SMCApi.ModuleException("managedId")
        messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_NOW_START
        if type == SMCApi.CommandType.START:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_NOW_START
        elif type == SMCApi.CommandType.EXECUTE:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_NOW_EXECUTE
        elif type == SMCApi.CommandType.UPDATE:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_NOW_UPDATE
        elif type == SMCApi.CommandType.STOP:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_NOW_STOP
        self.executionContextTool.add(messageType, managedId)
        if self.executionContexts:
            if type(values) == list:
                values = map(lambda v: Value(v).getValue(), values)
            self.executionContextsOutput[managedId] = self.executionContexts[managedId](values)

    def executeParallel(self, type, managedIds, values, waitingTacts=0, maxWorkInterval=-1):
        if not type:
            raise SMCApi.ModuleException("type")
        if not managedIds or len(managedIds) == 0:
            raise SMCApi.ModuleException("managedIds")
        if waitingTacts < 0:
            raise SMCApi.ModuleException("waitingTacts")
        for managedId in managedIds:
            if managedId < 0 or managedId >= self.countManagedExecutionContexts():
                raise SMCApi.ModuleException("managedId")
        messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_PARALLEL_START
        if type == SMCApi.CommandType.START:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_PARALLEL_START
        elif type == SMCApi.CommandType.EXECUTE:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_PARALLEL_EXECUTE
        elif type == SMCApi.CommandType.UPDATE:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_PARALLEL_UPDATE
        elif type == SMCApi.CommandType.STOP:
            messageType = SMCApi.MessageType.FLOW_CONTROL_EXECUTE_PARALLEL_STOP
        for managedId in managedIds:
            self.executionContextTool.add(messageType, managedId)
        self.executionContextTool.add(SMCApi.MessageType.FLOW_CONTROL_EXECUTE_PARALLEL_WAITING_TACTS, waitingTacts)
        self.executeInParalel.append(managedIds)
        if self.executionContexts:
            if type(values) == list:
                values = map(lambda v: Value(v).getValue(), values)
            for managedId in managedIds:
                self.executionContextsOutput[managedId] = self.executionContexts[managedId](values)
        return len(self.executeInParalel) - 1

    def isThreadActive(self, threadId):
        return False

    def getMessagesFromExecuted(self, threadId=0, managedId=0):
        if managedId < 0 or managedId >= self.countManagedExecutionContexts():
            raise SMCApi.ModuleException("managedId")
        return self.executionContextTool.filter([self.executionContextsOutput[managedId]], SMCApi.ActionType.EXECUTE, SMCApi.MessageType.DATA)

    def getCommandsFromExecuted(self, threadId=0, managedId=0):
        if managedId < 0 or managedId >= self.countManagedExecutionContexts():
            raise SMCApi.ModuleException("managedId")
        return [Command(self.executionContextTool.filter([self.executionContextsOutput[managedId]]), SMCApi.CommandType.EXECUTE)]

    def releaseThread(self, threadId):
        del self.executeInParalel[threadId]

    def releaseThreadCache(self, threadId):
        del self.executeInParalel[threadId]

    def getManagedExecutionContext(self, id):
        return None


class Process:
    def __init__(self, configurationTool, module):
        # type: (ConfigurationToolImpl, SMCApi.Module) -> None
        self.configurationTool = configurationTool
        self.module = module

    def fullLifeCycle(self, executionContextTool):
        # type: (ExecutionContextToolImpl) -> List[SMCApi.IMessage]
        result = []
        messages = self.start()
        for m in messages:
            result.append(m)
        messages = self.execute(executionContextTool)
        for m in messages:
            result.append(m)
        messages = self.update()
        for m in messages:
            result.append(m)
        messages = self.execute(executionContextTool)
        for m in messages:
            result.append(m)
        messages = self.stop()
        for m in messages:
            result.append(m)
        return result

    def start(self):
        # type: () -> List[SMCApi.IMessage]
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.ACTION_START, Value(1)))
        try:
            self.module.start(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.ACTION_STOP, Value(1)))
        return result

    def execute(self, executionContextTool):
        # type: (ExecutionContextToolImpl) -> List[SMCApi.IMessage]
        result = []
        if self.module is None:
            return result
        self.configurationTool.init(executionContextTool)
        executionContextTool.init(self.configurationTool)
        result.append(Message(SMCApi.MessageType.ACTION_START, Value(1)))
        try:
            output = list(executionContextTool.output)
            executionContextTool.output = []
            self.module.process(self.configurationTool, executionContextTool)
            result.extend(executionContextTool.output)
            output.extend(executionContextTool.output)
            executionContextTool.output = output
        except Exception as e:
            result.append(Message(SMCApi.MessageType.ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.ACTION_STOP, Value(1)))
        return result

    def update(self):
        # type: () -> List[SMCApi.IMessage]
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.ACTION_START, Value(1)))
        try:
            self.module.update(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.ACTION_STOP, Value(1)))
        return result

    def stop(self):
        # type: () -> List[SMCApi.IMessage]
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.ACTION_START, Value(1)))
        try:
            self.module.stop(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.ACTION_STOP, Value(1)))
        return result
