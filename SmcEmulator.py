"""
created by Nikolay V. Ulyanov (ulianownv@mail.ru)
http://www.smcsystem.ru
"""
import datetime
import tempfile

import SMCApi
from typing import Dict, List, Callable


class Value(SMCApi.IValue):
    def __init__(self, value):
        # type: (any) -> None
        self.value = value
        if type(value) == str:
            self.type = SMCApi.ValueType.STRING
        elif type(value) == bytearray or type(value) == bytes:
            self.type = SMCApi.ValueType.BYTES
        elif type(value) == int:
            self.type = SMCApi.ValueType.INTEGER
        elif type(value) == long:
            self.type = SMCApi.ValueType.LONG
        elif type(value) == float:
            self.type = SMCApi.ValueType.DOUBLE
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


class Configuration(SMCApi.CFGIConfigurationManaged):
    def __init__(self, name, executionContextTool=None, description=None, settings=None, variables=None, bufferSize=None):
        # type: (str, ExecutionContextToolImpl, str, Dict[str, SMCApi.IValue], Dict[str, SMCApi.IValue], int) -> None
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
        if bufferSize is not None:
            self.bufferSize = bufferSize
        else:
            self.bufferSize = 1
        self.enable = True

    def setName(self, name):
        self.name = name
        self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def setSetting(self, key, value):
        self.settings[key] = Value(value)
        self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_CONFIGURATION_SETTING_UPDATE,
                                      "{} {}".format(self.getName(), key))

    def setVariable(self, key, value):
        self.variables[key] = Value(value)
        if self.executionContextTool is not None:
            self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_CONFIGURATION_VARIABLE_UPDATE,
                                          "{} {}".format(self.getName(), key))

    def removeVariable(self, key):
        del self.variables[key]
        if self.executionContextTool is not None:
            self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_CONFIGURATION_VARIABLE_REMOVE,
                                          "{} {}".format(self.getName(), key))

    def setBufferSize(self, bufferSize):
        self.bufferSize = bufferSize
        self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def setEnable(self, enable):
        self.enable = enable
        self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_CONFIGURATION_UPDATE, self.getName())

    def countExecutionContexts(self):
        return 0

    def getExecutionContext(self, id):
        return None

    def createExecutionContext(self, name, maxWorkInterval=-1):
        self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_EXECUTION_CONTEXT_CREATE, "{} {}".format(self.getName(), name))

    def removeExecutionContext(self, id):
        self.executionContextTool.add(SMCApi.MessageType.MESSAGE_CONFIGURATION_CONTROL_EXECUTION_CONTEXT_REMOVE, "{} {}".format(self.getName(), id))

    def getContainer(self):
        return None

    def getModule(self):
        return None

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

    def isEnable(self):
        return self.enable


class ConfigurationToolImpl(SMCApi.ConfigurationTool):
    def __init__(self, name, description=None, settings=None, homeFolder=None, workDirectory=None):
        # type: (str, str, Dict[str, SMCApi.IValue], str, str) -> None
        # SMCApi.CFGIConfiguration
        self.configuration = Configuration(name, None, description, settings)
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
        return None

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

    def isEnable(self):
        return self.configuration.isEnable()


class ExecutionContextToolImpl(SMCApi.ExecutionContextTool, SMCApi.ConfigurationControlTool, SMCApi.FlowControlTool):
    def __init__(self, input=None, managedConfigurations=None, executionContextsOutput=None, executionContexts=None):
        # type: (List[List[SMCApi.IAction]], List[Configuration], List[SMCApi.IAction], List[Callable[[List[object]], SMCApi.IAction]]) -> None
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
        self.executeInParalel = []

    def init(self, configurationTool):
        # type: (ConfigurationToolImpl) -> None
        self.configuration = configurationTool.configuration

    def add(self, messageType, value):
        # type: (SMCApi.MessageType, object) -> None
        self.addMessage(Message(messageType, Value(value)))

    def addMessage(self, value):
        self.output.append(Message(SMCApi.MessageType.MESSAGE_DATA, Value(value)))

    def addError(self, value):
        self.output.append(Message(SMCApi.MessageType.MESSAGE_ERROR_TYPE, Value(value)))

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
        return "default"

    def getMaxWorkInterval(self):
        return -1

    def isEnable(self):
        return True

    def countSource(self):
        return len(self.input)

    def getSource(self, id):
        return None

    def getModules(self):
        return None

    def countManagedConfigurations(self):
        return len(self.managedConfigurations)

    def getManagedConfiguration(self, id):
        return self.managedConfigurations[id]

    def createConfiguration(self, id, container, module, name):
        pass

    def removeManagedConfiguration(self, id):
        pass

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

    def getManagedExecutionContext(self, id):
        return None


class Process:
    def __init__(self, configurationTool, module):
        # type: (ConfigurationToolImpl, SMCApi.Module) -> None
        self.configurationTool = configurationTool
        self.module = module

    def start(self):
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            self.module.start(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))
        return result

    def execute(self, executionContextTool):
        # type: (ExecutionContextToolImpl) -> List[SMCApi.IMessage]
        result = []
        if self.module is None:
            return result
        self.configurationTool.init(executionContextTool)
        executionContextTool.init(self.configurationTool)
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            output = list(executionContextTool.output)
            executionContextTool.output = []
            self.module.process(self.configurationTool, executionContextTool)
            result.extend(executionContextTool.output)
            output.extend(executionContextTool.output)
            executionContextTool.output = output
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))
        return result

    def update(self):
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            self.module.update(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))
        return result

    def stop(self):
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            self.module.stop(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e.message))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))
        return result
