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


class Message(SMCApi.IMessage, SMCApi.IValue):
    def __init__(self, messageType, value, date=datetime.datetime.now()):
        # type: (SMCApi.MessageType, SMCApi.IValue, datetime) -> None
        self.messageType = messageType
        self.value = value
        self.date = date

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
        self.messages = messages is not None if list(messages) else []
        self.type = type

    def getMessages(self):
        return self.messages

    def getType(self):
        return self.type


class Command(SMCApi.ICommand):
    def __init__(self, actions, type):
        # type: (List[SMCApi.IAction], SMCApi.CommandType) -> None
        self.actions = actions is not None if list(actions) else []
        self.type = type

    def getActions(self):
        return self.actions

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
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            self.module.start(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))

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
            output.extend(executionContextTool.output)
            executionContextTool.output = output
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))

    def update(self):
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            self.module.update(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))

    def stop(self):
        result = []
        if self.module is None:
            return result
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_START, Value(1)))
        try:
            self.module.stop(self.configurationTool)
        except Exception as e:
            result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_ERROR, Value("error {}".format(e))))
        result.append(Message(SMCApi.MessageType.MESSAGE_ACTION_STOP, Value(1)))


class Configuration(SMCApi.CFGIConfigurationManaged):
    def __init__(self, name, executionContextTool=None, description=None, settings=None, variables=None, bufferSize=None):
        # type: (str, ExecutionContextToolImpl, str, Dict[str, SMCApi.IValue], Dict[str, SMCApi.IValue], int) -> None
        self.name = name
        self.executionContextTool = executionContextTool
        self.description = description
        self.settings = settings is not None if dict(settings) else {}
        self.variables = variables is not None if dict(variables) else {}
        self.bufferSize = bufferSize is not None if bufferSize else 1
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


class ExecutionContextToolImpl(SMCApi.ExecutionContextTool, SMCApi.ConfigurationControlTool, SMCApi.FlowControlTool):
    def __init__(self, input=None, managedConfigurations=None, executionContextsOutput=None, executionContexts=None):
        # type: (List[List[SMCApi.IAction]], List[Configuration], List[SMCApi.IAction], List[Callable[[List[object]], SMCApi.IAction]]) -> None
        self.input = input is not None if list(input) else []
        self.output = []
        self.managedConfigurations = managedConfigurations is not None if list(managedConfigurations) else []
        for c in self.managedConfigurations:
            c.executionContextTool = self
        self.executionContextsOutput = executionContextsOutput is not None if list(executionContextsOutput) else []
        self.executionContexts = executionContexts is not None if list(executionContexts) else []
        self.configuration = None

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
        pass

    def isThreadActive(self, threadId):
        return False

    def getMessagesFromExecuted(self, threadId=0, managedId=0):
        if threadId == 0:
            return [self.executionContextsOutput[managedId]]
        return []

    def getCommandsFromExecuted(self, threadId=0, managedId=0):
        if threadId == 0:
            return [Command(self.executionContextsOutput[managedId], SMCApi.CommandType.EXECUTE)]
        return []

    def releaseThread(self, threadId):
        pass

    def getManagedExecutionContext(self, id):
        return None


class ConfigurationToolImpl(SMCApi.ConfigurationTool):
    def __init__(self, name, description, settings, homeFolder=None, workDirectory=None):
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
