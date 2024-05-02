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
    def __init__(self, value):
        # type: (any) -> None
        self.value = value
        valueType = type(value)
        if valueType is str or valueType is unicode:  # isinstance(value, basestring):
            self.type = SMCApi.ValueType.STRING
        elif valueType == bytearray or valueType == bytes:
            self.type = SMCApi.ValueType.BYTES
        elif valueType == int:
            self.type = SMCApi.ValueType.INTEGER
        elif valueType == long:
            self.type = SMCApi.ValueType.LONG
        elif valueType == float:
            self.type = SMCApi.ValueType.DOUBLE
        elif valueType == bool:
            self.type = SMCApi.ValueType.BOOLEAN
        elif valueType == SMCApi.ObjectArray:
            self.type = SMCApi.ValueType.OBJECT_ARRAY
        else:
            raise ValueError("wrong type")

    def getType(self):
        return self.type

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
    def __init__(self, name, types=[ModuleType("default")]):
        # type: (str, List[ModuleType]) -> None
        self.name = name
        self.types = types

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
    def __init__(self, name, containers=None, configurations=None):
        # type: (str, List[SMCApi.CFGIContainer], List[SMCApi.CFGIConfiguration]) -> None
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
        container = Container(name);
        self.containers.append(container)
        return container

    def removeContainer(self, id):
        self.containers.pop(id)

    def getName(self):
        return self.name

    def isEnable(self):
        return self.enable


class Configuration(SMCApi.CFGIConfigurationManaged):
    def __init__(self, container, module, name, executionContextTool=None, description=None, settings=None, variables=None, executionContexts=None,
                 bufferSize=None):
        # type: (SMCApi.CFGIContainer, SMCApi.Module, str, SMCApi.ExecutionContextTool, str, Dict[str, SMCApi.IValue], Dict[str, SMCApi.IValue], List[SMCApi.CFGIExecutionContextManaged], int) -> None
        self.container = container
        self.module = module
        self.name = name
        self.executionContextTool = executionContextTool
        self.description = description
        if settings is not None:
            self.settings = dict(settings)
        else:
            self.settings = {}
        if variables is not None:
            self.variables = dict(variables)
        else:
            self.variables = {}
        if executionContexts is not None:
            self.executionContexts = list(executionContexts)
        else:
            self.executionContexts = []
        if bufferSize is not None:
            self.bufferSize = bufferSize
        else:
            self.bufferSize = 1
        self.enable = True

        if self.container:
            self.container.configurations.append(self)

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
        return self.executionContexts[id]

    def createExecutionContext(self, name, maxWorkInterval=-1):
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_CREATE, "{} {}".format(self.getName(), name))

    def updateExecutionContext(self, id, name, maxWorkInterval=-1):
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_UPDATE, "{} {}".format(self.getName(), name))

    def removeExecutionContext(self, id):
        self.executionContextTool.add(SMCApi.MessageType.CONFIGURATION_CONTROL_EXECUTION_CONTEXT_REMOVE, "{} {}".format(self.getName(), id))

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
        return self.settings[key]

    def getAllVariables(self):
        return self.variables

    def getVariable(self, key):
        return self.variables[key]

    def getBufferSize(self):
        return self.bufferSize

    def getThreadBufferSize(self):
        return self.threadBufferSize

    def isEnable(self):
        return self.enable

    def isActive(self):
        return False


class ConfigurationToolImpl(SMCApi.ConfigurationTool):
    def __init__(self, name, description=None, settings=None, homeFolder=None, workDirectory=None):
        # type: (str, str, Dict[str, SMCApi.IValue], str, str) -> None
        # SMCApi.CFGIConfiguration
        self.configuration = Configuration(Container("rootContainer"), Module("Module"), name, None, description, settings)
        if homeFolder is None:
            homeFolder = tempfile.gettempdir()
        self.homeFolder = homeFolder
        if workDirectory is None:
            workDirectory = tempfile.gettempdir()
        self.workDirectory = workDirectory

    def init(self, executionContextTool):
        # type: (ExecutionContextToolImpl) -> None
        self.configuration.executionContextTool = executionContextTool

    def setVariable(self, key, value):
        self.configuration.setVariable(key, value)

    def isVariableChanged(self, key):
        return False

    def removeVariable(self, key):
        self.configuration.removeVariable(key)

    def getHomeFolder(self):
        return FileToolImpl(self.homeFolder)

    def getWorkDirectory(self):
        return self.workDirectory

    def countExecutionContexts(self):
        return self.configuration.countExecutionContexts()

    def getExecutionContext(self, id):
        self.configuration.getExecutionContext(id)

    def getContainer(self):
        self.configuration.getContainer()

    def hasLicense(self, freeDays):
        return True

    def getModule(self):
        return self.configuration.getModule()

    def getName(self):
        return self.configuration.getName()

    def getDescription(self):
        return self.configuration.getDescription()

    def getAllSettings(self):
        return self.configuration.getAllSettings()

    def getSetting(self, key):
        return self.configuration.getSetting(key)

    def getAllVariables(self):
        return self.configuration.getAllVariables()

    def getVariable(self, key):
        return self.configuration.getVariable(key)

    def getBufferSize(self):
        return self.configuration.getBufferSize()

    def getThreadBufferSize(self):
        return self.configuration.getThreadBufferSize()

    def isEnable(self):
        return self.configuration.isEnable()

    def loggerTrace(self, text):
        print "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    def loggerDebug(self, text):
        print "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    def loggerInfo(self, text):
        print "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    def loggerWarn(self, text):
        print "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    def loggerError(self, text):
        print "%s: Log Cfg %d: %s" % (datetime.datetime.now(), 0, text)

    def isActive(self):
        return False


class ExecutionContextToolImpl(SMCApi.ExecutionContextTool, SMCApi.ConfigurationControlTool, SMCApi.FlowControlTool):
    def __init__(self, input=None, managedConfigurations=None, executionContextsOutput=None, executionContexts=None, name="default", type="default"):
        # type: (List[List[SMCApi.IAction]], List[Configuration], List[SMCApi.IAction], List[Callable[[List[object]], SMCApi.IAction]], str, str) -> None
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
            c.executionContextTool = self
        if executionContextsOutput is not None:
            self.executionContextsOutput = list(executionContextsOutput)
        else:
            self.executionContextsOutput = []
        if executionContexts is not None:
            self.executionContexts = list(executionContexts)
            for ec in self.executionContexts:
                self.executionContextsOutput.append(None)
        else:
            self.executionContexts = []
        self.configuration = None
        self.name = name
        self.type = type
        self.executeInParalel = []
        self.modules = []
        modulesByName = {}
        for cfg in self.managedConfigurations:
            modulesByName[cfg.getModule().getName()] = cfg.getModule()
        modulesByName["Module"] = Module("Module")
        for name in modulesByName:
            self.modules.append(modulesByName[name])

    def init(self, configurationTool):
        # type: (ConfigurationToolImpl) -> None
        self.configuration = configurationTool.configuration

    def add(self, messageType, value):
        # type: (SMCApi.MessageType, object) -> None
        self.addMessage(Message(messageType, Value(value)))

    def addMessage(self, value):
        if isinstance(value, list):
            date = datetime.datetime.now()
            for element in value:
                self.output.append(Message(SMCApi.MessageType.DATA, Value(element), date))
        else:
            self.output.append(Message(SMCApi.MessageType.DATA, Value(value)))

    def addError(self, value):
        if isinstance(value, list):
            date = datetime.datetime.now()
            for element in value:
                self.output.append(Message(SMCApi.MessageType.ERROR, Value(element), date))
        else:
            self.output.append(Message(SMCApi.MessageType.ERROR, Value(value)))

    def countCommands(self, sourceId):
        return len(self.input[sourceId])

    def countCommandsFromExecutionContext(self, executionContext):
        return 0

    def getMessages(self, sourceId, fromIndex=-1, toIndex=-1):
        return self.input[sourceId]

    def getCommands(self, sourceId, fromIndex=-1, toIndex=-1):
        return [Command(self.input[sourceId], SMCApi.CommandType.EXECUTE)]

    def getCommandsFromExecutionContext(self, executionContext, fromIndex=-1, toIndex=-1):
        return None

    def isError(self, action):
        return False

    def getConfigurationControlTool(self):
        return self

    def getFlowControlTool(self):
        return self

    def isNeedStop(self):
        return False

    def getConfiguration(self):
        return self.configuration

    def getName(self):
        return self.name

    def getMaxWorkInterval(self):
        return -1

    def isEnable(self):
        return True

    def countSource(self):
        return len(self.input)

    def getSource(self, id):
        return None

    def getModules(self):
        return self.modules

    def countManagedConfigurations(self):
        return len(self.managedConfigurations)

    def getManagedConfiguration(self, id):
        return self.managedConfigurations[id]

    def createConfiguration(self, id, container, module, name):
        configuration = Configuration(container, module, name)
        self.managedConfigurations.append(configuration)
        return configuration

    def removeManagedConfiguration(self, id):
        self.managedConfigurations.pop(id)

    def countManagedExecutionContexts(self):
        return len(self.executionContexts)

    def executeNow(self, type, managedId, values):
        inputList = []
        if values is not None:
            for v in values:
                inputList.append(Value(v))
        self.executionContextsOutput[managedId] = self.executionContexts[managedId](inputList)

    def executeParallel(self, type, managedIds, values, waitingTacts=0, maxWorkInterval=-1):
        inputList = []
        if values is not None:
            for v in values:
                inputList.append(Value(v))
        self.executeInParalel.append(managedIds)
        for managedId in managedIds:
            self.executionContextsOutput[managedId] = self.executionContexts[managedId](inputList)
        return len(self.executeInParalel)

    def isThreadActive(self, threadId):
        return False

    def getMessagesFromExecuted(self, threadId=0, managedId=0):
        return [self.executionContextsOutput[managedId]]

    def getCommandsFromExecuted(self, threadId=0, managedId=0):
        return [Command(self.executionContextsOutput[managedId], SMCApi.CommandType.EXECUTE)]

    def releaseThread(self, threadId):
        del self.executeInParalel[threadId]

    def releaseThreadCache(self, threadId):
        del self.executeInParalel[threadId]

    def isActive(self):
        return False

    def getManagedExecutionContext(self, id):
        return None

    def addLog(self, value):
        self.output.append(Message(SMCApi.MessageType.LOG, Value(value)))

    def getType(self):
        return self.type


class Process:
    def __init__(self, configurationTool, module):
        # type: (ConfigurationToolImpl, SMCApi.Module) -> None
        self.configurationTool = configurationTool
        self.module = module

    def start(self):
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
