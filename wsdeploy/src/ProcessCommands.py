try:
    import AdminConfig
    import AdminControl
    import AdminApp
    import AdminTask
    import Help
except:
    pass

import re
import sys
from org.apache.log4j import *
class ProcessCommands:

    logger = Logger.getLogger("ProcessCommands")

    def generateCommands(self, cmdList=None, action=None):
        '''Method that takes a list of command dictionaries and processes them.  Use this method to process a series or sequential commands.'''
        self.action = action
        if self.action == None:
            self.action = 'R'
        self.cmdList = cmdList
        self.logger.info("generateCommands: processing command list.")
        if self.cmdList == None:
            self.logger.error("generateCommands: No list was passed to the generateCommands method")
            raise ProcessCommandException("No list was passed to the generateCommands method")
        self.logger.info("generateCommands: action is %s" % self.action)
        self.logger.trace("generateCommands: self.cmdList = %s " % self.cmdList)
        for item in self.cmdList:
            cmdDict = item
            self.logger.trace("generateCommands: item = %s" % item)
            for k, v in cmdDict.items():
                self.logger.trace("generateCommands: k = %s" % k )
                self.logger.trace("generateCommands: v = %s" % v )
                if k == "Cell":
                    self.logger.debug("generateCommands: block = Cell")
                    if AdminControl.getCell() != v['name']:
                        self.logger.error("generateCommands: Cell name %s != %s.  You may have connected to the wrong WebSphere environment or the name of the cell in the configuration xml is not correct." % (AdminControl.getCell(),v['name']))
                        raise ProcessCommandException("Cell name %s != %s.  You may have connected to the wrong WebSphere environment or the name of the cell in the configuration xml is not correct." % (AdminControl.getCell(),v['name']))
                elif k == "ServerCluster":
                    self.logger.trace("generateCommands: block = ServerCluster")
                    '''IMPLEMENT ME'''
                elif re.search("ClusterMember", k):
                    self.logger.trace("generateCommands: block = ClusterMember")
                    '''IMPLEMENT ME'''
                elif k == "Server":
                    self.logger.trace("generateCommands: block = Server")
                    self.processServer(cmdDict=cmdDict, action=action)
                elif k == "DataSource" or k == "MQQueueConnectionFactory" or k == 'MQQueue' or k == "JDBCProvider":
                    self.logger.trace("generateCommands: block = JDBCProvider, DataSource, MQQueueConnectionFactory, MQQueue")
                    self.processConfigItem(cmdDict=cmdDict, action=action)
                elif k == "J2EEResourceProperty":
                    self.logger.trace("generateCommands: block = J2EEResourceProperty")
                    self.processPropertySet(cmdDict=cmdDict, action=action)
                elif k == "JAASAuthData":
                    self.logger.trace("generateCommands: block = JAASAuthData")
                    self.processSecurity(cmdDict=cmdDict, action=action)
                elif k == "ConnectionPool" or k == "connectionPool" or k == "sessionPool":
                    self.logger.trace("generateCommands: block = ConnectionPool, connectionPool, sessionPool")
                    self.processNestedAttribute(cmdDict=cmdDict, action=action)
                elif k == "JavaVirtualMachine" or k == "ProcessExecution":
                    self.logger.trace("generateCommands: block = JavaVirtualMachine, ProcessExecution")
                    self.processNestedAttribute(cmdDict=cmdDict, action=action)
                elif k == 'SIBus' or k == 'SIBusMember' or k == 'SIBTopicSpace':
                    self.logger.trace("generateCommands: block = SIBus, SIBusMember, SIBTopicSpace")
                    self.processAdminTask(cmdDict=cmdDict, action=action)
                elif k == "env" or k == "Node" or k == 'dmgr' or k == 'JMSProvider':
                    self.logger.trace("generateCommands: block = env, Node, dmgr")
                    '''Ignore a tag'''
                    self.logger.debug("generateCommands: ignoring tag %s" % k )
                else:
                    '''Throw an exception if the tag is unknown'''
                    self.logger.error("generateCommands: %s is an unknown key.  Remove it from the configuration or add code to handle it." % k)
                    raise ProcessCommandException("generateCommands: %s is an unknown key. Remove it from the configuration or add code to handle it." % k)

    def processServer(self, cmdDict=None, action=None):
        '''processServer: This method processes a server configuration object. It takes two parameters, a dictionary containing the command and the action (RW)'''
        self.logger.trace("processServer: cmdDict=%s" % cmdDict)
        if cmdDict == None:
            self.logger.error("processServer: No dictionary was passed to the generateCommands method")
            raise ProcessCommandException("No dictionary was passed to the generateCommands method")
        #end-if
        k = cmdDict.keys()[0]
        v = cmdDict.values()[0]
        self.logger.trace("processServer: key=%s, value=%s" % (k, v))
        if k and v != None:
            self.validateScope(v, 'processServer')
            srv = AdminConfig.getid(v['scope']+"%s:%s/" % (k, v['name']))
            self.logger.trace("processServer: srv=%s " % srv)
            if srv == "":
                self.logger.info("processServer: creating server %s" % v['name'])
            else:
                srvObj = AdminConfig.getObjectName(srv)
                self.logger.trace("processServer: srvObj %s" % srvObj)
                ptype = AdminControl.getAttribute(srvObj, 'processType')
                self.logger.trace("processServer: ptype %s" % ptype)
                if ptype != 'UnManagedProcess':
                    self.logger.info("processServer: This is a Network Deployment Profile so this command will run.")
                else:
                    self.logger.warn("processServer: This is not a Network Deployment Profile so this command won't be run.  Use the manageprofiles too to create servers." )
                    #raise ProcessCommandException("This is not a Network Deployment Profile so this command won't be run.  Use the manageprofiles too to create servers.")
                #end-if
            #end-if
        else:
            self.logger.error("processServer: key and value parameters were not suppled to the method.")
            raise ProcessCommandException("key and value parameters were not suppled to the method.")
        #end-if

    def processNestedAttribute(self, cmdDict=None, action=None):
        '''processNestedAttribute: This method processes a single nested attribute. It takes two parameters, a dictionary containing the command and the action (RW)'''
        self.logger.trace("processNestedAttribute: cmdDict=%s" % cmdDict)
        if cmdDict == None:
            self.logger.error("processNestedAttribute: No dictionary was passed to the generateCommands method")
            raise ProcessCommandException("No dictionary was passed to the generateCommands method")
        #end-if
        k = cmdDict.keys()[0]
        v = cmdDict.values()[0]
        self.logger.trace("processNestedAttribute: key=%s, value=%s" % (k, v))
        self.validateScope(v, 'processNestedAttribute')
        attribute = None
        if re.match("[a-z]", k):
            self.logger.trace("processNestedAttribute: %s is a nested property." % k)
            attribute=AdminConfig.showAttribute(AdminConfig.getid(v['scope']), k)
        else:
            attribute = AdminConfig.list('%s' % k, AdminConfig.getid(v['scope']))
            self.logger.trace("processNestedAttribute: %s is an object." % k)
        #end-if
        for (k2, v2) in v.items():
            if k2 != "scope":
                actualValue=AdminConfig.showAttribute(attribute, k2)
                if actualValue != v2:
                    if action == 'W':
                        self.logger.info("processNestedAttribute: modifying %s%s:%s=%s" % (v['scope'], k, k2, v2))
                        self.logger.debug("processNestedAttribute: command=AdminConfig.modify(attribute, [[%s, %s]])" % (k2, v2))
                        AdminConfig.modify(attribute, [[k2, v2]])
                    else:
                        self.logger.warn("processNestedAttribute: audit failure %s%s:%s, actual=%s config=%s" % (v['scope'], k, k2, actualValue, v2))
                    #end-if
                else:
                    self.logger.debug("processNestedAttribute: ignoring %s%s:%s=%s" % (v['scope'], k, k2, v2))
                #end-if
            #end-if
        #end-for

    def processConfigItem(self, cmdDict=None, action=None):
        '''processConfigItem: This method processes a single configuration object. It takes two parameters, a dictionary containing the command and the action (RW)'''
        self.logger.trace("processConfigItem: cmdDict=%s" % cmdDict)
        if cmdDict == None:
            self.logger.error("processConfigItem: No dictionary was passed to the generateCommands method")
            raise ProcessCommandException("No dictionary was passed to the generateCommands method")
        #end-if
        k = cmdDict.keys()[0]
        v = cmdDict.values()[0]
        self.logger.trace("processConfigItem: key=%s, value=%s" % (k, v))
        template = self.setTemplate(key=k, valueDict=v)
        self.logger.trace("processConfigItem: template=%s" % template)
        self.validateScope(valueDict=v, method='processConfigItem')
        self.logger.trace("processConfigItem: scope=%s " % AdminConfig.getid(v['scope']))
        obj = AdminConfig.getid('%s%s:%s' % (v['scope'], k, v['name']))
        self.logger.trace("processConfigItem: obj=%s " % obj)
        if obj == "":
            self.logger.trace("processConfigItem: obj not found, creating...")
            attrList = []
            for key in v.keys():
                if key != 'scope':
                    attrList.append([key, v[key]])
                #end-if
            #end-for
            self.logger.trace("processConfigItem: attrList=%s" % attrList)
            self.logger.trace("processConfigItem: template=%s" % template)
            if template == None:
                self.logger.trace("processConfigItem: template was found...")
                if action == 'W':
                    self.logger.info("processConfigItem: creating %s:%s:%s" % (AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), k, v['name']))
                    self.logger.debug("processConfigItem: command=AdminConfig.create(%s, %s, %s)" % (k, AdminConfig.getid(v['scope']), attrList))
                    AdminConfig.create(k, AdminConfig.getid(v['scope']), attrList)
                else:
                    self.logger.warn("processConfigItem: action is set to %s.  Item %s:%s:%s will not be created.  Attribute and properties for this object will not exist and may cause failures in this script." % (action, AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), k, v['name']))
                #end-if
            else:
                self.logger.trace("processConfigItem: template not found...")
                if action == 'W':
                    self.logger.info("processConfigItem: creating %s:%s:%s" % (AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), k, v['name']))
                    self.logger.trace("processConfigItem: template=%s" % template)
                    self.logger.debug("processConfigItem: command=AdminConfig.createUsingTemplate(%s, %s, %s, %s)" % (k, AdminConfig.getid(v['scope']), attrList, template))
                    AdminConfig.createUsingTemplate(k, AdminConfig.getid(v['scope']), attrList, template)
                else:
                    self.logger.warn("processConfigItem: action is set to %s.  Item %s:%s:%s will not be created.  Attribute and properties for this object will not exist and may cause failures in this script." % (action, AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), k, v['name']))
                #end-if
            #end-if
        #end-if
        else:
            for key in v.keys():
                if key != 'scope':
                    actual = AdminConfig.showAttribute(obj, key)
                    self.logger.trace("processConfigItem: attribute=%s, value=%s" % (key, actual))
                    if actual != v[key]:
                        if action == 'W':
                            self.logger.info("processConfigItem: modifying actual=%s to %s" % (actual,v[key]))
                            self.logger.debug("processConfigItem: command=AdminConfig.modify(%s, [['%s', '%s']])" % (obj, key, v[key]))
                            AdminConfig.modify(obj, [[key, v[key]]])
                        else:
                            self.logger.warn("processPropertySet: audit failure %s:%s, actual=%s config=%s" % (AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), (AdminConfig.showAttribute(obj, 'name')), (AdminConfig.showAttribute(obj, key)), v[key]))
                        #end-if
                    #end-if
                #end-if
            #end-for
        #end-if

    def processPropertySet(self, cmdDict=None, action=None):
        '''processPropertySet: This method processes a single configuration object. It takes two parameters, a dictionary containing the command and the action (RW)'''
        self.logger.trace("processPropertySet: cmdDict=%s" % cmdDict)
        if cmdDict == None:
            self.logger.error("processPropertySet: No dictionary was passed to the generateCommands method")
            raise ProcessCommandException("No dictionary was passed to the generateCommands method")
        #end-if
        k = cmdDict.keys()[0]
        v = cmdDict.values()[0]
        self.logger.trace("processPropertySet: key=%s, value=%s" % (k, v))
        self.validateScope(v, 'processPropertySet')
        self.propSet=AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'propertySet')
        self.logger.trace("processPropertySet: propSet=%s " % self.propSet)
        self.propList = AdminConfig.list(k, AdminConfig.getid(v['scope'])).split('\r\n')
        for key in v.keys():
            if key == 'name':
                self.logger.trace("processPropertySet: key=%s, value=%s" % (key, v[key]))
                itemFound="1"
                for item in self.propList:
                    self.logger.trace("processPropertySet: name=%s" % AdminConfig.showAttribute(item, 'name'))
                    if AdminConfig.showAttribute(item, 'name') == v[key]:
                        self.logger.trace("processPropertySet: actual name=%s, value=%s" % (AdminConfig.showAttribute(item, 'name'), AdminConfig.showAttribute(item, 'value')))
                        self.logger.trace("processPropertySet: config name=%s, value=%s" % (v['name'], v['value']))
                        if AdminConfig.showAttribute(item, 'value') != v['value']:
                            if action == 'W':
                                self.logger.info("processPropertySet: modifying %s:%s:%s=%s" % (AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), AdminConfig.showAttribute(item, 'name'), 'value', v['value']))
                                self.logger.debug("processPropertySet: command=AdminConfig.modify(%s, [[%s, %s]])" % (item, 'value', v['value']))
                                AdminConfig.modify(item, [['value', v['value']]])
                            else:
                                self.logger.warn("processPropertySet: audit failure %s:%s, actual=%s config=%s" % (AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), (AdminConfig.showAttribute(item, 'name')), AdminConfig.showAttribute(item, 'value'), v['value']))
                            #end-if
                        else:
                            self.logger.debug("processPropertySet: ignoring %s %s" % (AdminConfig.showAttribute(item, 'name'), AdminConfig.showAttribute(item, 'value')))
                        #end-if
                        itemFound = "0"
                        break
                    #end-if
                #end-for
                if itemFound == "1":
                    self.logger.info("processPropertySet: creating %s:%s:%s=%s" % (AdminConfig.showAttribute(AdminConfig.getid(v['scope']), 'name'), AdminConfig.showAttribute(item, 'name'), 'value', v['value']))
                    self.logger.debug("processPropertySet: command=AdminConfig.create(k, self.propSet, [['name', '%s'],['type', '%s'],['value', '%s'],['required', '%s'])" % (v[key], v['type'], v['value'], v['required']))
                    AdminConfig.create(k, self.propSet, [['name', v[key]],['type', v['type']],['value', v['value']],['required', v['required']]])
                #end-if
            #end-if
        #end-for

    def processSecurity(self, cmdDict=None, action=None):
        '''Used to process security properties'''
        self.logger.trace("processPropertySet: cmdDict=%s" % cmdDict)
        if cmdDict == None:
            self.logger.error("processPropertySet: No dictionary was passed to the generateCommands method")
            raise ProcessCommandException("No dictionary was passed to the generateCommands method")
        #end-if
        k = cmdDict.keys()[0]
        v = cmdDict.values()[0]
        self.logger.trace("processSecrurity: key=%s, value=%s" % (k, v))
        if k and v != None:
            self.validateScope(v, 'processPropertySet')
            self.jaasAuthDataList = AdminConfig.list(k, AdminConfig.getid('%sSecurity:/' % v['scope'])).split('\r\n')
            self.logger.trace("processSecrurity: jaasAuthDataList=%s"% self.jaasAuthDataList)
            for key in v.keys():
                if key == 'alias':
                    self.logger.trace("processSecrurity: key=%s, value=%s" % (key, v[key]))
                    itemFound="1"
                    self.logger.trace("processSecrurity: items length is=%s" % len(self.jaasAuthDataList))
                    for item in self.jaasAuthDataList:
                        self.logger.trace("processSecrurity: item=%s" % item)
                        if item != "":
                            self.logger.trace("processSecrurity: name=%s" % AdminConfig.showAttribute(item, 'alias'))
                            if AdminConfig.showAttribute(item, 'alias') == v[key]:
                                self.logger.trace("processSecrurity: checking alias %s" % AdminConfig.showAttribute(item,'alias'))
                                for key in v.keys():
                                    if key != 'scope':
                                        self.logger.trace("processSecrurity: key=%s" % key)
                                        if AdminConfig.showAttribute(item, key) != v[key]:
                                            self.logger.trace("processSecrurity: alias:%s, key=%s, actual=%s, config=%s" % (AdminConfig.showAttribute(item,'alias'), key, AdminConfig.showAttribute(item, key), v[key]))
                                            if action == 'W':
                                                self.logger.info("processSecrurity: modifying %s:%s=%s" % (AdminConfig.showAttribute(item,'alias'), key, v[key]))
                                                self.logger.debug("processSecrurity: command=AdminConfig.modify(%s, [[%s, %s]])" % (AdminConfig.showAttribute(item,'alias'), key, v[key]))
                                                AdminConfig.modify(item, [[key, v[key]]])
                                            else:
                                                self.logger.warn("processSecrurity: audit failure %s:, actual=%s config=%s" % (AdminConfig.showAttribute(item,'alias'), AdminConfig.showAttribute(item, key), v[key]))
                                            #end-if
                                        #end-if
                                    #end-if
                                #end-for
                                itemFound = "0"
                                break
                            #end-if
                        #end-if
                    #end-for
                    if itemFound == "1":
                        self.logger.info("processSecrurity: creating %s:%s" % (k, v['alias']))
                        attrList = []
                        for key in v.keys():
                            if key != 'scope':
                                attrList.append([key, v[key]])
                        self.logger.debug("processSecrurity: command=AdminConfig.create(%s, %s, %s)" % (k, AdminConfig.getid('%sSecurity:/' % v['scope']), attrList))
                        AdminConfig.create(k, AdminConfig.getid('%sSecurity:/' % v['scope']), attrList)
                    #end-if
                #end-if
            #end-for
        else:
            self.logger.error("processPropertySet: key and value parameters were not suppled to the method.")
            raise ProcessCommandException("key and value parameters were not suppled to the method.")
        #end-if

    def processAdminTask(self, cmdDict=None, action=None):
        self.logger.trace("processAdminTask: cmdDict=%s" % cmdDict)
        if cmdDict == None:
            self.logger.error("processAdminTask: No dictionary was passed to the generateCommands method")
            raise ProcessCommandException("No dictionary was passed to the generateCommands method")
        #end-if
        k = cmdDict.keys()[0]
        v = cmdDict.values()[0]
        self.logger.trace("processAdminTask: key=%s, value=%s" % (k, v))
        if k and v != None:
            self.validateScope(valueDict=v, method='processAdminTask')
            attrDict = self.convertAttributesToAdminTaskStep(k=k, v=v)
            if k == 'SIBus':
                self.processSIB(k=k, a=attrDict, action=action)
            elif k == 'SIBusMember':
                self.processSIBusMember(k=k, a=attrDict, action=action)
            elif k == 'SIBTopicSpace':
                self.processSIBTopicSpace(k=k, a=attrDict, action=action)
        else:
            self.logger.error("processPropertySet: key and value parameters were not suppled to the method.")
            raise ProcessCommandException("key and value parameters were not suppled to the method.")
        #end-if

    def validateScope(self, valueDict=None, method=None):
        self.valueDict=valueDict
        self.method=method
        self.scope = AdminConfig.getid(valueDict['scope'])
        if self.scope == "":
            self.logger.error("validateScope:%s Scope %s does not exist.  The object may not have been created yet or the scope in the configuration file is incorrect." % (self.method, valueDict['scope']))
            raise ProcessCommandException("Scope %s does not exist.  The object may not have been created yet or the scope in the configuration file is incorrect." % valueDict['scope'])

    def setTemplate(self, key=None, valueDict=None):
        template = None
        if key == 'DataSource':
            if valueDict['providerType'] == 'Oracle JDBC Driver (XA)':
                template = AdminConfig.listTemplates('DataSource', "Oracle JDBC Driver XA DataSource")
            else:
                template = AdminConfig.listTemplates('DataSource', "Oracle JDBC Driver DataSource")
        elif key == 'MQQueueConnectionFactory':
            template = AdminConfig.listTemplates('MQQueueConnectionFactory', 'First Example WMQ QueueConnectionFactory')
            valueDict['scope'] = ('%sJMSProvider:WebSphere MQ JMS Provider/' % valueDict['scope'])
            self.logger.trace("setTemplate: Adjusting Scope for messaging provider=%s" % valueDict['scope'])
        elif key == 'MQQueue':
            template = AdminConfig.listTemplates('MQQueue', 'Example.JMS.WMQ.Q1')
            valueDict['scope'] = ('%sJMSProvider:WebSphere MQ JMS Provider/' % valueDict['scope'])
            self.logger.trace("setTemplate: Adjusting Scope for messaging provider=%s" % valueDict['scope'])
        self.logger.trace("setTemplate: template=%s" % template)
        return template

    def convertAttributesToAdminTaskStep(self, k=None, v=None):
        self.logger.trace("convertAttributesToAdminTaskStep: key=%s, value=%s" % (k, v))
        attrDict = {}
        for key, value in v.items():
            if k == 'SIBus':
                if key != 'scope':
                    self.logger.trace("convertAttributesToAdminTaskStep: key=%s, value=%s" % (key, value))
                    if key == 'name':
                        self.logger.trace("convertAttributesToAdminTaskStep: converting attribute '%s' to AdminTask step '%s'" % (key, 'bus'))
                        attrDict['bus'] = v[key]
                    else:
                        attrDict[key] = v[key]
            elif k == 'SIBusMember' or 'SIBTopicSpace':
                if key == 'scope':
                    self.logger.trace("convertAttributesToAdminTaskStep: converting attribute '%s' to AdminTask step '%s'" % (key, 'bus'))
                    bus = value.split(':')
                    self.logger.trace("convertAttributesToAdminTaskStep: bus=%s" % bus)
                    bus = bus[1]
                    self.logger.trace("convertAttributesToAdminTaskStep: bus=%s" % bus)
                    bus = bus.split('/')
                    self.logger.trace("convertAttributesToAdminTaskStep: bus=%s" % bus)
                    bus = bus[0]
                    self.logger.trace("convertAttributesToAdminTaskStep: bus=%s" % bus)
                    attrDict['bus'] = bus
                elif key == 'identifier':
                    self.logger.trace("convertAttributesToAdminTaskStep: converting attribute '%s' to AdminTask step '%s'" % (key, 'name'))
                    attrDict['name'] = v[key]
                else:
                    attrDict[key] = v[key]
        self.logger.trace("convertAttributesToAdminTaskStep: attrDict=%s" % attrDict)
        return attrDict

    def processSIB(self, k=None, a=None, action=None):
        attrDict=a
        self.sib = AdminConfig.getid('/SIBus:%s/' % attrDict['bus'])
        if self.sib != '':
            for key in attrDict.keys():
                self.logger.trace("processSIB: key=%s" % key)
                if key != 'scope' and key != 'bus':
                    self.value=AdminConfig.showAttribute(self.sib, key)
                    self.logger.trace("processSIB: self.value=%s" % self.value)
                    if self.value != attrDict[key]:
                        if action == 'W':
                            self.logger.info("processSIB: modifying %s:%s:%s=%s" % (k, AdminConfig.showAttribute(self.sib,'name'), key, attrDict[key]))
                            self.logger.debug("processSIB: command=AdminTask.modifySIBus(%s)" % (["-%s %s -%s %s" % ('bus', attrDict['bus'], key, attrDict[key])]))
                            AdminTask.modifySIBus(["-%s %s -%s %s" % ('bus', attrDict['bus'], key, attrDict[key])])
                        else:
                            self.logger.warn("processSIB: audit failure %s:%s, actual=%s config=%s" % (k, AdminConfig.showAttribute(self.sib,'name'), AdminConfig.showAttribute(self.sib, key), attrDict[key]))
        else:
            self.logger.info("processSIB: creating %s:%s" % (k, attrDict['bus']))
            self.logger.debug("processSIB: command=AdminTask.createSIBus(%s)" % (["-%s %s" % (key, value) for key, value in attrDict.items()]))
            AdminTask.createSIBus(["-%s %s" % (key, value) for key, value in attrDict.items()])

    def processSIBusMember(self, k=None, a=None, action=None):
        attrDict=a
        self.sib = AdminConfig.getid('/SIBusMember:%s/' % attrDict['server'])
        if self.sib != '':
            self.logger.warn("processSIBusMember: server %s already member of the bus %s" % (attrDict['server'], attrDict['bus']))
        else:
            self.logger.info("processSIBusMember: creating %s:%s" % (k, attrDict['bus']))
            self.logger.debug("processSIBusMember: command=AdminTask.addSIBusMember(%s)" % (["-%s %s" % (key, value) for key, value in attrDict.items()]))
            AdminTask.addSIBusMember(["-%s %s" % (key, value) for key, value in attrDict.items()])

    def processSIBTopicSpace(self, k=None, a=None, action=None):
        attrDict=a
        attrDict['type'] = 'TopicSpace'
        self.sib = None
        queueList = AdminTask.listSIBDestinations(['-bus %s' % attrDict['bus']]).split('\r\n')
        self.logger.trace("processSIBTopicSpace: queueList=%s" % queueList)
        for queue in queueList:
            self.logger.trace("processSIBTopicSpace: queue=%s" % queue)
            identifier = AdminConfig.showAttribute(queue, "identifier")
            self.logger.trace("processSIBTopicSpace: identifier=%s" % identifier)
            if (identifier == attrDict['name']):
                self.sib = queue
                self.logger.trace("processSIBTopicSpace: topic %s already exists" % attrDict['name'])
        self.logger.trace("processSIBTopicSpace: self.sib=%s" % self.sib)
        if self.sib != None:
            self.logger.warn("processSIBTopicSpace: topic %s already exists on bus %s" % (attrDict['name'], attrDict['bus']))
            destAttr = AdminTask.showSIBDestination('-bus %s -name %s' % (attrDict['bus'], attrDict['name']))
            print destAttr
            for attr in destAttr:
                pairStr = attr.split('=')
                print pairStr
        else:
            self.logger.info("processSIBTopicSpace: creating %s:%s" % (k, attrDict['name']))
            self.logger.debug("processSIBTopicSpace: command=AdminTask.createSIBDestination(%s)" % (["-%s %s" % (key, value) for key, value in attrDict.items()]))
            AdminTask.createSIBDestination(["-%s %s" % (key, value) for key, value in attrDict.items()])

class ProcessCommandException(Exception):
    """ General exception method for class. """
    def __init__(self, val):
        self.val = val
    def __str__(self):
        return repr(self.val)
